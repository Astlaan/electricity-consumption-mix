<script lang="ts">
    import { onMount } from 'svelte';

    // Forward declare Plotly if types are not readily available or for simplicity initially
    // For a more robust solution, one might install @types/plotly.js or define custom types
    declare let Plotly: any; 

    // Form state variables
    let plotMode = 'discriminated'; // 'discriminated', 'aggregated', 'areas'
    let timeMode = 'simple'; // 'simple', 'advanced'

    // Simple mode inputs
    let startDate = '2024-01-01T00:00';
    let endDate = '2024-01-01T02:00';
    let startDateMin = '';
    let endDateMin = '';
    let startDateMax = '';
    let endDateMax = '';

    // Advanced mode inputs
    let years = '';
    let months = '';
    let days = '';
    let hours = '';

    // UI state
    let isLoading = false;
    let errorMessage = '';
    let errorDetails: string[] = [];
    let submitDisabled = false;

    // Plot related state
    let currentPlotData: any = null;
    let showPlotControls = false;
    let plotControlShowDetails = true; // Default based on original logic for pie/sunburst
    let plotControlPlotSize = 800;

    // --- Helper Functions from original JS ---
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
        const startDateObj = new Date(startDate + 'Z');
        const endDateObj = new Date(endDate + 'Z');
        let errors: string[] = [];

        if (isNaN(startDateObj.getTime()) || isNaN(endDateObj.getTime())) {
            errors.push("Please insert valid dates");
            errorDetails = errors;
            errorMessage = errors.join('<br>'); // Keep a general message
            submitDisabled = true;
            return false;
        }

        if (startDateObj.getUTCMinutes() !== 0) {
            errors.push("Start time must be on the hour (00 minutes)");
        }
        if (endDateObj.getUTCMinutes() !== 0) {
            errors.push("End time must be on the hour (00 minutes)");
        }

        const [minStartDateVal, minEndDateVal, maxStartDateVal, maxEndDateVal] = getDateBounds();

        if (startDateObj < minStartDateVal) {
            errors.push(`Start date cannot be earlier than ${minStartDateVal.toUTCString().replace("GMT", "UTC")}`);
        }
        if (endDateObj < minEndDateVal) {
            errors.push(`End date cannot be earlier than ${minEndDateVal.toUTCString().replace("GMT", "UTC")}`);
        }
        if (startDateObj > maxStartDateVal) {
            errors.push(`Start date cannot be later than ${maxStartDateVal.toUTCString().replace("GMT", "UTC")}`);
        }
        if (endDateObj > maxEndDateVal) {
            errors.push(`End date cannot be later than ${maxEndDateVal.toUTCString().replace("GMT", "UTC")}`);
        }
        if (startDateObj >= endDateObj) {
            errors.push("End date must be after start date");
        }

        if (plotMode === "areas") {
            const timeDifference = (endDateObj.getTime() - startDateObj.getTime()) / (1000 * 60 * 60);
            if (timeDifference < 2) {
                errors.push("Time-based charts: Interval must span at least 2 hours.");
            }
            if (timeDifference > 7 * 24) {
                errors.push("Time-based charts: Interval must span at most 7 days (168 hours).");
            }
        }

        if (errors.length > 0) {
            errorDetails = errors;
            errorMessage = errors.join('<br>');
            submitDisabled = true;
            return false;
        } else {
            errorDetails = [];
            errorMessage = '';
            submitDisabled = false;
            return true;
        }
    }

    async function handleSubmit() {
        if (timeMode === 'simple' && !validateDates()) {
            return;
        }
        // TODO: Add validation for advanced mode if necessary

        isLoading = true;
        errorMessage = '';
        errorDetails = [];
        submitDisabled = true;
        currentPlotData = null; // Clear previous plot
        showPlotControls = false;

        try {
            let requestData;
            if (timeMode === 'simple') {
                requestData = {
                    mode: 'simple',
                    plot_mode: plotMode,
                    start_date: startDate,
                    end_date: endDate
                };
            } else {
                requestData = {
                    mode: 'advanced',
                    plot_mode: plotMode,
                    years: years,
                    months: months,
                    days: days,
                    hours: hours
                };
            }

            const response = await fetch('/api/generate_plot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });

            const textResponse = await response.text();
            let data;
            try {
                data = JSON.parse(textResponse);
            } catch (parseError) {
                throw new Error(textResponse || 'Invalid server response');
            }

            if (!response.ok) {
                if (response.status === 504) throw new Error("Error: Backend timeout");
                throw new Error(data.error || 'Failed to generate visualization');
            }

            if (data.plot) {
                currentPlotData = JSON.parse(data.plot);
                // const plotType = currentPlotData.data[0].type;
                // plotControlShowDetails = plotType === "pie" ? true : plotType === "sunburst" ? false : plotControlShowDetails;
                updatePlot(); // Initial plot render
                showPlotControls = true;
                // Scroll to plot - Svelte way would be to bind to an element and call scrollIntoView
                // For now, manual scroll or user scrolls.
            } else {
                throw new Error('No plot data received');
            }

        } catch (error: any) {
            errorMessage = error.message;
            console.error('Error:', error);
        } finally {
            isLoading = false;
            // Re-enable submit button only if not in simple mode with errors
            if (timeMode !== 'simple' || validateDates()) {
                 submitDisabled = false;
            }
        }
    }
    
    function updatePlot() {
        if (!currentPlotData || typeof Plotly === 'undefined') return;

        const dataForPlotly = structuredClone(currentPlotData.data);
        const layoutForPlotly = structuredClone(currentPlotData.layout);

        layoutForPlotly.height = plotControlPlotSize;
        delete layoutForPlotly.width; // Let Plotly handle width responsively or based on container

        if (plotControlShowDetails) {
            if (dataForPlotly[0].type === "pie")
                layoutForPlotly.texttemplate = "%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} MW";
            else if (dataForPlotly[0].type === "sunburst")
                dataForPlotly[0].texttemplate = "%{label}<br>%{customdata[0]:.1f}%";
        } else {
            dataForPlotly[0].texttemplate = "%{label}";
        }

        if (dataForPlotly[0].type === "sunburst") {
            const colors = { "PT": "#80b1d3", "ES": "#fb8072", "FR": "#b3de69" };
            if (!dataForPlotly[0].marker) dataForPlotly[0].marker = {};
            dataForPlotly[0].marker.colors = dataForPlotly[0].labels.map((label: string) => 
                dataForPlotly[0].parents.includes(label) ? (colors as any)[label] : null
            );
        }

        if (dataForPlotly[0].type === "scatter") {
            layoutForPlotly.hovermode = "x";
            layoutForPlotly.hoverlabel = { namelength: -1 };
            layoutForPlotly.xaxis = { showspikes: true };
        }
        
        // Ensure the plotArea div exists and is visible before plotting
        const plotAreaEl = document.getElementById('plotArea');
        if (plotAreaEl) {
             Plotly.newPlot('plotArea', dataForPlotly, layoutForPlotly, { responsive: true });
        }
    }

    onMount(() => {
        setFormDateBounds();
        validateDates(); // Initial validation

        // Trigger change for initially selected plotMode
        if (plotMode === 'areas') {
            timeMode = 'simple';
            // advancedModeRadio.disabled = true; // Will be handled by reactive $: block
        }

        // Plotly resize handling
        let lastViewportWidth = window.innerWidth;
        let lastViewportHeight = window.innerHeight;
        let lastZoomLevel = window.devicePixelRatio;

        const handleResize = () => {
            const currentViewportWidth = window.innerWidth;
            const currentViewportHeight = window.innerHeight;
            const currentZoomLevel = window.devicePixelRatio;

            if (currentZoomLevel !== lastZoomLevel) {
                lastZoomLevel = currentZoomLevel;
                return;
            }
            if (currentViewportWidth !== lastViewportWidth || currentViewportHeight !== lastViewportHeight) {
                const plotAreaEl = document.getElementById('plotArea');
                if (plotAreaEl && plotAreaEl.children.length > 0 && currentPlotData) {
                     Plotly.Plots.resize('plotArea');
                }
                lastViewportWidth = currentViewportWidth;
                lastViewportHeight = currentViewportHeight;
            }
        };
        window.addEventListener('resize', handleResize);
        
        window.onbeforeunload = function () {
            window.scrollTo(0, 0);
        };

        return () => { // Cleanup
            window.removeEventListener('resize', handleResize);
            window.onbeforeunload = null;
        };
    });

    // Reactive statements to handle logic that depends on state changes
    $: if (timeMode === 'simple') {
        validateDates();
    } else { // advanced mode
        errorMessage = ''; // Clear errors when switching to advanced
        errorDetails = [];
        submitDisabled = false;
    }

    $: if (plotMode === 'areas') {
        timeMode = 'simple'; // Force simple mode
        // No direct DOM disable, use Svelte's disabled attribute on the input
    }
    // No need for an else here to re-enable, as the disabled attribute will react to plotMode

    $: if (currentPlotData) { // When plot data is available, re-render plot if controls change
        updatePlot();
    }

</script>

<h1>Portugal Electricity Consumption Mix</h1>

<div class="form-container">
    <div class="mode-selector">
        <input type="radio" id="discriminated" name="plotModeRadio" value="discriminated" bind:group={plotMode} />
        <label for="discriminated">Average by Country and Source</label>
        <input type="radio" id="aggregated" name="plotModeRadio" value="aggregated" bind:group={plotMode} />
        <label for="aggregated">Average by Source</label>
        <input type="radio" id="areas" name="plotModeRadio" value="areas" bind:group={plotMode} />
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
                    <span class="help-text">Empty means no constraint (all years considered). Ranges (eg. 2020-2023) are inclusive</span>
                </div>
                <div class="time-field">
                    <label for="months">Months:</label>
                    <input type="text" id="months" placeholder="e.g., 1-3, 3, 6, 9" bind:value={months} />
                    <span class="help-text">Same as above</span>
                </div>
                <div class="time-field">
                    <label for="days">Days:</label>
                    <input type="text" id="days" placeholder="e.g., 1-15, 20, 22-25" bind:value={days} />
                    <span class="help-text">Same as above</span>
                </div>
                <div class="time-field">
                    <label for="hours">Hours:</label>
                    <input type="text" id="hours" placeholder="e.g., 20-23, 23-2" bind:value={hours} />
                    <span class="help-text">
                        Valid values: [0, 23]. (UTC timezone!)
                        <br />Each selected hour represents the interval from that hour's start, till the start of the next hour.
                        <br />5 represents the interval from 5am-6am
                        <br />14-17 represents the interval 2pm-6pm.
                    </span>
                </div>
            </div>
        {/if}
        <button type="submit" disabled={submitDisabled || isLoading}>Generate Plot</button>
    </form>

    {#if errorMessage}
        <div class="error-message" style="display: block;">
            {@html errorMessage} 
            <!-- Or loop through errorDetails if you prefer -->
            <!-- {#each errorDetails as errorItem}
                <div class="error-item">{errorItem}</div>
            {/each} -->
        </div>
    {/if}

    {#if isLoading}
        <div class="loading" style="display: block;">Generating visualization...<br />(May take up to 60s if fetching new data is required)</div>
    {/if}
</div>

<div id="plotContainer">
    {#if showPlotControls}
    <div id="plotControls" class="plot-controls" style="display: block;"> <!-- Ensure this is styled to be visible -->
        <h3 style="margin-top: 0; margin-bottom: 10px">Plot Controls</h3>
        <div>
            <input type="checkbox" id="plotControlShowDetails" bind:checked={plotControlShowDetails} />
            <label for="plotControlShowDetails">
                Show Details <span class="inline-help-text" title="Hovering over the plot will show all details.">(You can also hover for the plot for all details)</span>
            </label>
        </div>
        <div>
            <label for="plotControlPlotSize">Plot Size:</label>
            <input type="range" id="plotControlPlotSize" min="400" max="1000" bind:value={plotControlPlotSize} step="50" />
        </div>
    </div>
    {/if}
    <div id="plotArea"></div> <!-- Plotly will target this -->
</div>

<!-- Footer placeholder from layout -->

<style>
    /* Page-specific styles can go here, or be in the global styles in +layout.svelte if truly global */
    /* For example, if #plotContainer or #advancedControls styles are only for this page, move them from layout */
    /* Styles for .disabled class on label */
    .disabled {
        color: #cccccc;
        cursor: not-allowed;
    }
    /* Ensure plotControls is visible when it should be */
    .plot-controls {
        margin-bottom: 10px; /* Example styling */
    }
</style>
