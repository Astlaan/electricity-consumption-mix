<svelte:head>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</svelte:head>

<script lang="ts">
    import { onMount } from 'svelte';

    // Forward declare Plotly for robust type checking
    declare let Plotly: any;

    // --- Constants ---
    const PSR_TYPE_MAPPING = {
        "B01": "Biomass", "B02": "Fossil Brown coal/Lignite", "B03": "Fossil Coal-derived gas",
        "B04": "Fossil Gas", "B05": "Fossil Hard coal", "B06": "Fossil Oil", "B07": "Fossil Oil shale",
        "B08": "Fossil Peat", "B09": "Geothermal", "B10": "Hydro Pumped Storage",
        "B11": "Hydro Run-of-river and poundage", "B12": "Hydro Water Reservoir", "B13": "Marine",
        "B14": "Nuclear", "B15": "Other renewable", "B16": "Solar", "B17": "Waste",
        "B18": "Wind Offshore", "B19": "Wind Onshore", "B20": "Other",
    };

    // --- Data Parsing and Plotting Classes (from public/index.html) ---
    class JsonDataParser {
        data: any;
        constructor(jsonData: string) {
            this.data = JSON.parse(jsonData);
        }
        get index() { return this.data.index.map((ts: number) => new Date(ts)); }
        get columns() { return this.data.columns; }
        get values() { return this.data.data; }
        mean() {
            const numRows = this.values.length;
            if (numRows === 0) return new Map();
            const numCols = this.columns.length;
            const sums = new Array(numCols).fill(0);
            for (let i = 0; i < numRows; i++) {
                for (let j = 0; j < numCols; j++) {
                    sums[j] += this.values[i][j];
                }
            }
            const means = new Map();
            for (let j = 0; j < numCols; j++) {
                means.set(this.columns[j], sums[j] / numRows);
            }
            return means;
        }
    }

    class Plotter {
        aggregated: JsonDataParser;
        contributions: { [key: string]: JsonDataParser } = {};
        constructor(data: any) {
            this.aggregated = new JsonDataParser(data.aggregated);
            for (const country in data.contributions) {
                this.contributions[country] = new JsonDataParser(data.contributions[country]);
            }
        }

        plot(plotMode: string, timeMode: string, startDate: string, endDate: string) {
            switch (plotMode) {
                case 'aggregated': return this._plotAggregated(timeMode, startDate, endDate);
                case 'discriminated': return this._plotHierarchical(timeMode, startDate, endDate);
                case 'areas': return this._plotAreas(timeMode, startDate, endDate);
                default: throw new Error(`Unsupported plot mode: ${plotMode}`);
            }
        }

        _plotAggregated(timeMode: string, startDate: string, endDate: string) {
            const data = this.aggregated.mean();
            const labels: string[] = [];
            const values: number[] = [];
            data.forEach((value, key) => {
                if (value > 0) {
                    labels.push(PSR_TYPE_MAPPING[key as keyof typeof PSR_TYPE_MAPPING] || key);
                    values.push(value);
                }
            });
            const total = values.reduce((a, b) => a + b, 0);
            const percentages = values.map(v => (v / total) * 100);
            const trace = {
                type: 'pie', labels, values, customdata: percentages.map(p => [p]),
                textinfo: 'percent+label', texttemplate: '%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} MW',
                hovertemplate: '%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} MW', hole: 0, insidetextorientation: 'auto'
            };
            let title = "Portugal Electricity Consumption Mix";
            if (timeMode === 'simple' && startDate && endDate) {
                const formattedStartDate = this._formatDateTime(startDate, false, endDate);
                const formattedEndDate = this._formatDateTime(endDate, true);
                title += ` (${formattedStartDate}${formattedStartDate === formattedEndDate ? '' : ' - ' + formattedEndDate})`;
            }
            const layout = this._getBaseLayout(title);
            return { data: [trace], layout };
        }

        _plotHierarchical(timeMode: string, startDate: string, endDate: string) {
            const records: any[] = [];
            const totalHours = this.aggregated.index.length;
            const dataByCountryTimeAggregated: { [key: string]: Map<string, number> } = {};
            let totalPower = 0;
            for (const country in this.contributions) {
                const meanData = this.contributions[country].mean();
                dataByCountryTimeAggregated[country] = meanData;
                meanData.forEach(value => totalPower += value);
            }
            for (const country in dataByCountryTimeAggregated) {
                const series = dataByCountryTimeAggregated[country];
                let countryPower = 0;
                series.forEach(value => countryPower += value);
                const countryEnergy = countryPower * totalHours;
                const percentage = (countryPower / totalPower) * 100;
                records.push({
                    id: country, parent: "", label: country, power: countryPower, percentage: percentage,
                    hover_text: `<b>${country}</b><br>${percentage.toFixed(1)}% of total<br>${countryPower.toFixed(0)} MW (average)<br>${this._calcEnergyString(countryEnergy)}`
                });
                series.forEach((power, source_type) => {
                    if (power > 0) {
                        const sourceName = PSR_TYPE_MAPPING[source_type as keyof typeof PSR_TYPE_MAPPING] || source_type;
                        const energy = power * totalHours;
                        const sourcePercentage = (power / totalPower) * 100;
                        const id = `${country}/${sourceName}`;
                        records.push({
                            id, parent: country, label: sourceName, power, percentage: sourcePercentage,
                            hover_text: `<b>${id}</b><br>${(power / countryPower * 100).toFixed(1)}% of ${country}<br>${sourcePercentage.toFixed(1)}% of total<br>${power.toFixed(0)} MW (average)<br>${this._calcEnergyString(energy)}`
                        });
                    }
                });
            }
            const trace = {
                type: 'sunburst', ids: records.map(r => r.id), labels: records.map(r => r.label),
                parents: records.map(r => r.parent), values: records.map(r => r.power),
                customdata: records.map(r => [r.percentage, r.hover_text]),
                insidetextorientation: 'radial', hovertemplate: '%{customdata[1]}<extra></extra>', branchvalues: 'total',
            };
            let title = "Portugal Electricity Consumption Mix";
            if (timeMode === 'simple' && startDate && endDate) {
                const formattedStartDate = this._formatDateTime(startDate, false, endDate);
                const formattedEndDate = this._formatDateTime(endDate, true);
                title += ` (${formattedStartDate}${formattedStartDate === formattedEndDate ? '' : ' - ' + formattedEndDate})`;
            }
            const layout = this._getBaseLayout(title);
            return { data: [trace], layout };
        }

        _plotAreas(timeMode: string, startDate: string, endDate: string) {
            const traces: any[] = [];
            const index = this.aggregated.index;
            const columns = this.aggregated.columns;
            const values = this.aggregated.values;
            for (let j = 0; j < columns.length; j++) {
                const colName = columns[j];
                const yValues = values.map(row => row[j]);
                traces.push({
                    x: index, y: yValues, name: PSR_TYPE_MAPPING[colName as keyof typeof PSR_TYPE_MAPPING] || colName,
                    type: 'scatter', mode: 'lines', stackgroup: 'one',
                    hovertemplate: `<b>${PSR_TYPE_MAPPING[colName as keyof typeof PSR_TYPE_MAPPING] || colName}</b><br>%{y:.0f} MW<extra></extra>`,
                });
            }
            let title = "Portugal Electricity Consumption Mix";
            if (timeMode === 'simple' && startDate && endDate) {
                const formattedStartDate = this._formatDateTime(startDate, false, endDate);
                const formattedEndDate = this._formatDateTime(endDate, true);
                title += ` (${formattedStartDate}${formattedStartDate === formattedEndDate ? '' : ' - ' + formattedEndDate})`;
            }
            const layout = this._getBaseLayout(title);
            layout.xaxis = { title: 'Time' };
            layout.yaxis = { title: 'Power (MW)' };
            return { data: traces, layout };
        }

        _getBaseLayout(title: string) {
            return {
                title: title, showlegend: false,
                colorway: ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072', '#80b1d3', '#fdb462', '#b3de69', '#fccde5', '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f'],
                width: 900, height: 800, autosize: true,
                annotations: [{
                    text: "Source: https://portugal-electricity-mix.vercel.app<br>Data: ENTSO-E",
                    showarrow: false, x: 0.5, y: -0.1, xref: 'paper', yref: 'paper', xanchor: 'center', yanchor: 'top',
                }],
                margin: { t: 50, b: 100, l: 0, r: 0 },
            };
        }

        _calcEnergyString(energyInMWh: number) {
            const GWh_FACTOR = 1000, TWh_FACTOR = 1000000;
            let value, unit;
            if (energyInMWh >= TWh_FACTOR) { value = energyInMWh / TWh_FACTOR; unit = "TWh"; }
            else if (energyInMWh >= GWh_FACTOR) { value = energyInMWh / GWh_FACTOR; unit = "GWh"; }
            else { value = energyInMWh; unit = "MWh"; }
            return `${value.toPrecision(4)} ${unit}`;
        }

        _formatDateTime(dateTimeString: string, isEndDate = false, endDateString: string | null = null) {
            const date = new Date(dateTimeString + 'Z');
            let day = date.getUTCDate(), month = date.getUTCMonth() + 1, year = date.getUTCFullYear();
            let hours = date.getUTCHours(), minutes = date.getUTCMinutes();
            if (isEndDate && hours === 0 && minutes === 0) {
                date.setUTCDate(date.getUTCDate() - 1);
                day = date.getUTCDate(); month = date.getUTCMonth() + 1; year = date.getUTCFullYear();
            }
            const formattedDate = `${String(day).padStart(2, '0')}/${String(month).padStart(2, '0')}/${year}`;
            if (endDateString) {
                const startDateObj = new Date(dateTimeString + 'Z');
                const endDateObj = new Date(endDateString + 'Z');
                const nextDay = new Date(startDateObj);
                nextDay.setUTCDate(startDateObj.getUTCDate() + 1);
                nextDay.setUTCHours(0, 0, 0, 0);
                if (startDateObj.getUTCHours() === 0 && startDateObj.getUTCMinutes() === 0 && endDateObj.getTime() === nextDay.getTime()) {
                    return formattedDate;
                }
            }
            if (hours === 0 && minutes === 0) return formattedDate;
            const ampm = hours >= 12 ? 'PM' : 'AM';
            const formattedHours = hours % 12 === 0 ? 12 : hours % 12;
            return `${formattedDate} ${formattedHours}${ampm}`;
        }
    }

    // --- Svelte Component State ---
    let plotMode = 'discriminated';
    let timeMode = 'simple';
    let startDate = '2024-01-01T00:00', endDate = '2024-01-01T02:00';
    let startDateMin = '', endDateMin = '', startDateMax = '', endDateMax = '';
    let years = '', months = '', days = '', hours = '';
    let isLoading = false, errorMessage = '', submitDisabled = false;
    let errorDetails: string[] = [];

    // --- Plot State ---
    let plotter: Plotter | null = null;
    let generatedPlotMode = '';
    let currentPlotData: any = null;
    let showPlotControls = false;
    let plotControlShowDetails = true;
    let plotControlAggregateImports = false;
    let plotControlPlotSize = 800;

    // --- Lifecycle and Event Handlers ---
    onMount(() => {
        setFormDateBounds();
        validateDates();
        if (plotMode === 'areas') timeMode = 'simple';

        let lastViewportWidth = window.innerWidth, lastViewportHeight = window.innerHeight, lastZoomLevel = window.devicePixelRatio;
        const handleResize = () => {
            const currentZoomLevel = window.devicePixelRatio;
            if (currentZoomLevel !== lastZoomLevel) { lastZoomLevel = currentZoomLevel; return; }
            if (window.innerWidth !== lastViewportWidth || window.innerHeight !== lastViewportHeight) {
                const plotAreaEl = document.getElementById('plotArea');
                if (plotAreaEl && plotAreaEl.children.length > 0) Plotly.Plots.resize('plotArea');
                lastViewportWidth = window.innerWidth; lastViewportHeight = window.innerHeight;
            }
        };
        window.addEventListener('resize', handleResize);
        window.onbeforeunload = () => window.scrollTo(0, 0);
        return () => {
            window.removeEventListener('resize', handleResize);
            window.onbeforeunload = null;
        };
    });

    // --- Functions ---
    function getDateBounds() {
        const minStartDate = new Date('2015-01-15T00:00Z');
        const maxEndDate = new Date();
        maxEndDate.setUTCHours(maxEndDate.getUTCHours() - 1, 0, 0, 0);
        const minEndDate = new Date(minStartDate);
        minEndDate.setUTCHours(minEndDate.getUTCHours() + 1);
        const maxStartDate = new Date(maxEndDate);
        maxStartDate.setUTCHours(maxStartDate.getUTCHours() - 1);
        return [minStartDate, minEndDate, maxStartDate, maxEndDate];
    }

    function setFormDateBounds() {
        const [minStartDateVal, minEndDateVal, maxStartDateVal, maxEndDateVal] = getDateBounds();
        startDateMin = minStartDateVal.toISOString().slice(0, 16);
        endDateMin = minEndDateVal.toISOString().slice(0, 16);
        startDateMax = maxStartDateVal.toISOString().slice(0, 16);
        endDateMax = maxEndDateVal.toISOString().slice(0, 16);
    }

    function validateDates() {
        const startDateObj = new Date(startDate + 'Z'), endDateObj = new Date(endDate + 'Z');
        let errors: string[] = [];
        if (isNaN(startDateObj.getTime()) || isNaN(endDateObj.getTime())) errors.push("Please insert valid dates");
        if (startDateObj.getUTCMinutes() !== 0) errors.push("Start time must be on the hour (00 minutes)");
        if (endDateObj.getUTCMinutes() !== 0) errors.push("End time must be on the hour (00 minutes)");
        const [minStartDateVal, minEndDateVal, maxStartDateVal, maxEndDateVal] = getDateBounds();
        if (startDateObj < minStartDateVal) errors.push(`Start date cannot be earlier than ${minStartDateVal.toUTCString().replace("GMT", "UTC")}`);
        if (endDateObj < minEndDateVal) errors.push(`End date cannot be earlier than ${minEndDateVal.toUTCString().replace("GMT", "UTC")}`);
        if (startDateObj > maxStartDateVal) errors.push(`Start date cannot be later than ${maxStartDateVal.toUTCString().replace("GMT", "UTC")}`);
        if (endDateObj > maxEndDateVal) errors.push(`End date cannot be later than ${maxEndDateVal.toUTCString().replace("GMT", "UTC")}`);
        if (startDateObj >= endDateObj) errors.push("End date must be after start date");
        if (plotMode === "areas") {
            const timeDifference = (endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60);
            if (timeDifference < 2) errors.push("Time-based charts: Interval must span at least 2 hours.");
            if (timeDifference > 7 * 24) errors.push("Time-based charts: Interval must span at most 7 days (168 hours).");
        }
        errorDetails = errors;
        errorMessage = errors.join('<br>');
        submitDisabled = errors.length > 0;
        return errors.length === 0;
    }

    async function handleSubmit() {
        if (timeMode === 'simple' && !validateDates()) return;
        isLoading = true; errorMessage = ''; errorDetails = []; submitDisabled = true;
        try {
            const requestData = timeMode === 'simple'
                ? { mode: 'simple', plot_mode: plotMode, start_date: startDate, end_date: endDate }
                : { mode: 'advanced', plot_mode: plotMode, years, months, days, hours };
            const response = await fetch('/api/generate_plot', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(requestData)
            });
            const textResponse = await response.text();
            let data;
            try { data = JSON.parse(textResponse); } catch (e) { throw new Error(textResponse || 'Invalid server response'); }
            if (!response.ok) throw new Error(data.error || (response.status === 504 ? "Error: Backend timeout" : 'Failed to generate visualization'));
            if (data.data) {
                plotter = new Plotter(data.data);
                generatedPlotMode = plotMode;
                currentPlotData = plotter.plot(plotMode, timeMode, startDate, endDate);
                updatePlot();
                showPlotControls = true;
                document.getElementById('plotContainer')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
            } else {
                throw new Error('No plot data received');
            }
        } catch (error: any) {
            errorMessage = error.message;
            console.error('Error:', error);
        } finally {
            isLoading = false;
            submitDisabled = timeMode === 'simple' ? !validateDates() : false;
        }
    }

    function updatePlot() {
        if (!currentPlotData || typeof Plotly === 'undefined') return;
        const data = structuredClone(currentPlotData.data);
        const layout = structuredClone(currentPlotData.layout);
        if (generatedPlotMode === 'discriminated' && plotControlAggregateImports) {
            const totalValue = data[0].values.reduce((sum: number, v: number, i: number) => data[0].parents[i] === '' ? sum + v : sum, 0);
            const aggregatedData: any = { ids: [], labels: [], parents: [], values: [], customdata: [], marker: { colors: [] } };
            const imports = { id: "Imports", label: "Imports", parent: "", value: 0, twh: 0, color: "#fdb462" };
            const importSources: { [key: string]: any } = {};
            for (let i = 0; i < data[0].ids.length; i++) {
                const id = data[0].ids[i], label = data[0].labels[i], parent = data[0].parents[i];
                const value = data[0].values[i], customdata = data[0].customdata[i];
                let twh = 0;
                const match = customdata[1].match(/<br>([\d.]+) (T|G)Wh/);
                if (match) { const num = parseFloat(match[1]); twh = match[2] === 'G' ? num / 1000 : num; }
                if (parent === "" && id !== "PT") { imports.value += value; imports.twh += twh; }
                else if (id.startsWith("PT")) {
                    aggregatedData.ids.push(id); aggregatedData.labels.push(label); aggregatedData.parents.push(parent);
                    aggregatedData.values.push(value); aggregatedData.customdata.push(customdata);
                } else {
                    if (!importSources[label]) importSources[label] = { id: `Imports/${label}`, label, parent: "Imports", value: 0, twh: 0 };
                    importSources[label].value += value; importSources[label].twh += twh;
                }
            }
            const importsPercentOfTotal = (imports.value / totalValue) * 100;
            let importsEnergyValue = imports.twh, importsEnergyUnit = "TWh";
            if (importsEnergyValue < 1 && importsEnergyValue > 0) { importsEnergyValue *= 1000; importsEnergyUnit = "GWh"; }
            imports.customdata = [importsPercentOfTotal, `<b>Imports</b><br>${importsPercentOfTotal.toFixed(1)}% of total<br>${Math.round(imports.value)} MW (average)<br>${importsEnergyValue.toFixed(1)} ${importsEnergyUnit}`];
            aggregatedData.ids.push(imports.id); aggregatedData.labels.push(imports.label); aggregatedData.parents.push(imports.parent);
            aggregatedData.values.push(imports.value); aggregatedData.customdata.push(imports.customdata);
            for (const source in importSources) {
                const sourceData = importSources[source];
                const percentOfImports = (sourceData.value / imports.value) * 100;
                const percentOfTotal = (sourceData.value / totalValue) * 100;
                let energyValue = sourceData.twh, energyUnit = "TWh";
                if (energyValue < 1 && energyValue > 0) { energyValue *= 1000; energyUnit = "GWh"; }
                sourceData.customdata = [percentOfTotal, `<b>Imports/${sourceData.label}</b><br>${percentOfImports.toFixed(1)}% of Imports<br>${percentOfTotal.toFixed(1)}% of total<br>${Math.round(sourceData.value)} MW (average)<br>${energyValue.toFixed(1)} ${energyUnit}`];
                aggregatedData.ids.push(sourceData.id); aggregatedData.labels.push(sourceData.label); aggregatedData.parents.push(sourceData.parent);
                aggregatedData.values.push(sourceData.value); aggregatedData.customdata.push(sourceData.customdata);
            }
            data[0] = { ...data[0], ...aggregatedData };
        }
        layout.height = plotControlPlotSize;
        delete layout.width;
        if (plotControlShowDetails) {
            if (data[0].type === "pie") data[0].texttemplate = "%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} MW";
            else if (data[0].type === "sunburst") data[0].texttemplate = "%{label}<br>%{customdata[0]:.1f}%";
        } else {
            data[0].texttemplate = "%{label}";
        }
        if (data[0].type === "sunburst") {
            const colors = { "PT": "#80b1d3", "ES": "#fb8072", "FR": "#b3de69", "Imports": "#fdb462" };
            if (!data[0].marker) data[0].marker = {};
            data[0].marker.colors = data[0].labels.map((label: string, i: number) => {
                const parent = data[0].parents[i];
                return parent === "" ? (colors as any)[label] : null;
            });
        }
        if (data[0].type === "scatter") {
            layout.hovermode = "x"; layout.hoverlabel = { namelength: -1 }; layout.xaxis = { showspikes: true };
        }
        Plotly.newPlot('plotArea', data, layout, { responsive: true });
    }

    // --- Reactive Statements ---
    $: if (timeMode === 'simple') validateDates();
    else { errorMessage = ''; errorDetails = []; submitDisabled = false; }
    $: if (plotMode === 'areas') timeMode = 'simple';
    $: if (currentPlotData) updatePlot();

</script>

<h1>Portugal Electricity Consumption Mix</h1>

<div class="form-container">
    <div class="mode-selector">
        <input type="radio" id="discriminated" name="plotModeRadio" value="discriminated" bind:group={plotMode} on:change={updatePlot} />
        <label for="discriminated">Average by Country and Source</label>
        <input type="radio" id="aggregated" name="plotModeRadio" value="aggregated" bind:group={plotMode} on:change={updatePlot} />
        <label for="aggregated">Average by Source</label>
        <input type="radio" id="areas" name="plotModeRadio" value="areas" bind:group={plotMode} on:change={updatePlot} />
        <label for="areas">Time-based Chart</label>
    </div>

    <div class="mode-selector">
        <input type="radio" id="simpleMode" name="timeModeRadio" value="simple" bind:group={timeMode} />
        <label for="simpleMode">Simple Interval</label>
        <input type="radio" id="advancedMode" name="timeModeRadio" value="advanced" bind:group={timeMode} disabled={plotMode === 'areas'} />
        <label for="advancedMode" class:disabled={plotMode === 'areas'}>Complex Interval</label>
    </div>

    <form on:submit|preventDefault={handleSubmit}>
        {#if timeMode === 'simple'}
            <div id="simpleControls">
                <label for="start_date">Start Date (UTC):</label>
                <input type="datetime-local" id="start_date" bind:value={startDate} on:input={validateDates} on:change={validateDates} min={startDateMin} max={startDateMax} step="3600" required />
                <label for="end_date">End Date (UTC):</label>
                <input type="datetime-local" id="end_date" bind:value={endDate} on:input={validateDates} on:change={validateDates} min={endDateMin} max={endDateMax} step="3600" required />
            </div>
        {/if}
        {#if timeMode === 'advanced'}
            <div id="advancedControls">
                <div class="time-field">
                    <label for="years">Years:</label>
                    <input type="text" id="years" placeholder="e.g., 2015, 2017, 2020-2023" bind:value={years} />
                    <span class="help-text">Empty means no constraint. Ranges (e.g., 2020-2023) are inclusive.</span>
                </div>
                <div class="time-field">
                    <label for="months">Months:</label>
                    <input type="text" id="months" placeholder="e.g., 1-3, 6, 9" bind:value={months} />
                    <span class="help-text">Same as above.</span>
                </div>
                <div class="time-field">
                    <label for="days">Days:</label>
                    <input type="text" id="days" placeholder="e.g., 1-15, 20, 22-25" bind:value={days} />
                    <span class="help-text">Same as above.</span>
                </div>
                <div class="time-field">
                    <label for="hours">Hours:</label>
                    <input type="text" id="hours" placeholder="e.g., 20-23, 23-2" bind:value={hours} />
                    <span class="help-text">Valid values: [0, 23] (UTC). Each hour is an interval (e.g., 5 is 5am-6am).</span>
                </div>
            </div>
        {/if}
        <button type="submit" disabled={submitDisabled || isLoading}>Generate Plot</button>
    </form>

    {#if errorMessage}
        <div class="error-message" style="display: block;">{@html errorMessage}</div>
    {/if}
    {#if isLoading}
        <div class="loading" style="display: block;">Generating visualization...<br />(May take up to 60s if fetching new data is required)</div>
    {/if}
</div>

<div id="plotContainer">
    {#if showPlotControls}
    <div id="plotControls" class="plot-controls">
        <h3 style="margin-top: 0; margin-bottom: 10px">Plot Controls</h3>
        <div>
            <input type="checkbox" id="plotControlShowDetails" bind:checked={plotControlShowDetails} />
            <label for="plotControlShowDetails">
                Show Details <span class="inline-help-text" title="Hovering over the plot will show all details.">(You can also hover for details)</span>
            </label>
        </div>
        {#if generatedPlotMode === 'discriminated'}
        <div id="aggregateImportsContainer">
            <input type="checkbox" id="plotControlAggregateImports" bind:checked={plotControlAggregateImports} />
            <label for="plotControlAggregateImports">Aggregate Imports</label>
        </div>
        {/if}
        <div>
            <label for="plotControlPlotSize">Plot Size:</label>
            <input type="range" id="plotControlPlotSize" min="400" max="1000" bind:value={plotControlPlotSize} step="50" />
        </div>
    </div>
    {/if}
    <div id="plotArea"></div>
</div>

<style>
    .disabled { color: #cccccc; cursor: not-allowed; }
    .plot-controls { margin-bottom: 10px; }
</style>
