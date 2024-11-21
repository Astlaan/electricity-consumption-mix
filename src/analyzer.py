from data_fetcher import Data
import pandas as pd
import numpy as np
from config import PSR_COLORS, PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe, apply_to_fields

pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)     # Show all rows
pd.set_option('display.width', None)        # Set width to expand to full display
pd.set_option('display.max_colwidth', None)



def _format_date_range(df: pd.DataFrame) -> str:
    start_date = df.index.min()
    end_date = df.index.max()
    return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

def _time_aggregation(df: pd.DataFrame) -> pd.Series: # aggregate_by_source_type
    """Aggregate data by source type only."""
    # Remove columns where all values are 0
    df = df.loc[:, (df != 0).any()]
    # Fill any NaN values with 0
    df = df.fillna(0) # TODO fix

    # Group by source type (in case multiple B-codes map to same source)
    grouped_data = df.mean()

    return grouped_data

def ensure_index_and_sorting(data: Data):
    # This is handy while the stash fixing saved/loaded indexes is not fixed
    def _ensure_index_and_sorting(df):
        if 'start_time' in df.columns:
            df = df.set_index('start_time')
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')] # Remove duplicates keeping last value
        return df

    apply_to_fields(data, _ensure_index_and_sorting)
    data.assert_equal_length()

    return data

def add(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.add(df2, fill_value=0)

def sub(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.sub(df2, fill_value=0)



def plot(data: Data, mode: str):
    print("FUNCTION: plot")

    # If start_time is a column, set it as index. If it's already the index, nothing changes
    data = ensure_index_and_sorting(data)

    psr_types = list(PSR_TYPE_MAPPING.keys())

    G_pt = data.generation_pt[data.generation_pt.columns.intersection(psr_types)]
    G_es = data.generation_es[data.generation_es.columns.intersection(psr_types)]
    G_fr = data.generation_fr[data.generation_fr.columns.intersection(psr_types)]
    F_pt_es = data.flow_pt_to_es["Power"].values[:, None]
    F_es_pt = data.flow_es_to_pt["Power"].values[:, None]
    F_fr_es = data.flow_fr_to_es["Power"].values[:, None]
    F_es_fr = data.flow_es_to_fr["Power"].values[:, None]

    # Without france
    # flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
    # flow_per_source_es_pt = F_es_pt * (G_es.div(G_es.sum(axis=1), axis=0))
    # consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)
    
    # With France
    flow_per_source_fr_es = F_fr_es * (G_fr.div(G_fr.sum(axis=1), axis=0)) # TODO verify [0]!!!!!!!!!!!!!!!!!!!!!!
    flow_per_source_es_fr = F_es_fr * (G_es.div(G_es.sum(axis=1), axis=0))
    G_es_prime = G_es.sub(flow_per_source_es_fr, fill_value=0).add(flow_per_source_fr_es, fill_value=0)

    flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
    flow_per_source_es_pt = F_es_pt * (G_es_prime.div(G_es_prime.sum(axis=1), axis=0))
    consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

    plot_func = globals()[f'{mode}']
    fig = plot_func(consumption_per_source)
    return fig

def plot_discriminate_by_country(data: Data, mode: str, plot_type: str):
    """
    Computes the consumption per source by isolating contributions from
    Portuguese (PT), Spanish (ES), and French (FR) generations, according to the given mathematical expression.

    Parameters:
    - data (Data): A data object containing generation and flow information.
    - mode (str): A string indicating the plotting mode.

    Returns:
    - consumption_per_source (pd.DataFrame): Total consumption per source.
    - contributions (dict): Dictionary containing individual contributions from PT, ES, and FR.
    - fig: The generated plot figure.
    """
    print("FUNCTION: plot_discriminate_by_country")
    # Ensure 'start_time' is set as index and sorted
    data = ensure_index_and_sorting(data)

    # PSR_TYPE_MAPPING is assumed to be a predefined mapping of types
    psr_types = list(PSR_TYPE_MAPPING.keys())

    # Extract generation data for PT, ES, FR
    G_pt = data.generation_pt[data.generation_pt.columns.intersection(psr_types)]
    G_es = data.generation_es[data.generation_es.columns.intersection(psr_types)]
    G_fr = data.generation_fr[data.generation_fr.columns.intersection(psr_types)]
    
    # Extract flow data for various transitions
    F_pt_es = data.flow_pt_to_es["Power"].values[:, None]    # Flow from PT to ES
    F_es_pt = data.flow_es_to_pt["Power"].values[:, None]    # Flow from ES to PT
    F_fr_es = data.flow_fr_to_es["Power"].values[:, None]    # Flow from FR to ES
    F_es_fr = data.flow_es_to_fr["Power"].values[:, None]    # Flow from ES to FR

    # Should be equivalent to this:
    # flow_per_source_fr_es = F_fr_es * (G_fr.div(G_fr.sum(axis=1), axis=0))
    # flow_per_source_es_fr = F_es_fr * (G_es.div(G_es.sum(axis=1), axis=0))
    # G_es_prime = G_es.sub(flow_per_source_es_fr, fill_value=0).add(flow_per_source_fr_es, fill_value=0)

    # flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
    # flow_per_source_es_pt = F_es_pt * (G_es_prime.div(G_es_prime.sum(axis=1), axis=0))
    # consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

    # Compute total generation for normalization
    sum_G_pt = G_pt.sum(axis=1).values[:, None] 
    sum_G_es = G_es.sum(axis=1).values[:, None]
    sum_G_fr = G_fr.sum(axis=1).values[:, None]

    # Avoid division by zero by replacing zeros with ones
    sum_G_pt[sum_G_pt == 0] = 1  # TODO is this needed?
    sum_G_es[sum_G_es == 0] = 1
    sum_G_fr[sum_G_fr == 0] = 1

    # Compute Available ES Generation
    Available_ES_Generation = sum_G_es - F_es_fr + F_fr_es
    Available_ES_Generation[Available_ES_Generation == 0] = 1  # Avoid division by zero
    # TODO is this needed?

    # ------------------------------
    # Define Individual Contributions
    # ------------------------------

    # 1. Portuguese Contribution (Gpt_contribution)
    Gpt_contribution = G_pt * (1 - F_pt_es / sum_G_pt)

    # 2. Spanish Contribution (Ges_contribution)
    # Compute ES fraction
    ES_fraction = (F_es_pt * (1 - F_es_fr / sum_G_es)) / Available_ES_Generation
    # Expand dimensions to match G_es dimensions
    ES_fraction = np.tile(ES_fraction, (1, G_es.shape[1]))
    Ges_contribution = G_es.values * ES_fraction ## TODO why values here?

    # 3. French Contribution (Gfr_contribution)
    # Compute FR fraction
    FR_fraction = (F_es_pt * (F_fr_es / sum_G_fr)) / Available_ES_Generation
    # Expand dimensions to match G_fr dimensions
    FR_fraction = np.tile(FR_fraction, (1, G_fr.shape[1]))
    Gfr_contribution = G_fr.values * FR_fraction  # TODO why values here?

    # Convert contributions to DataFrames with appropriate indices and columns
    Ges_contribution = pd.DataFrame(Ges_contribution, index=G_es.index, columns=G_es.columns)
    Gfr_contribution = pd.DataFrame(Gfr_contribution, index=G_fr.index, columns=G_fr.columns)

    # ------------------------------
    # Compute Total Consumption per Source
    # ------------------------------

    consumption_per_source = Gpt_contribution.copy()
    consumption_per_source = consumption_per_source.add(Ges_contribution, fill_value=0)
    consumption_per_source = consumption_per_source.add(Gfr_contribution, fill_value=0)

    # ------------------------------
    # Organize the Contributions into a Dictionary
    # ------------------------------
    contributions = {
        'PT': Gpt_contribution,
        'ES': Ges_contribution,
        'FR': Gfr_contribution
    }

    # ------------------------------
    # Plotting (Optional)
    # ------------------------------
    plot_func = globals().get(f'{mode}', None)
    if plot_func:
        fig = plot_func(consumption_per_source, contributions)
    else:
        raise ValueError(f"Plotting function '{mode}' not found in globals.")

    return fig



def _plot_internal_plotly_2(df: pd.DataFrame, *_):
    import plotly.express as px
    data = _time_aggregation(df)

    
    # Only plot non-zero values
    mask = data > 0
    data = data[mask]

    if data.empty:
        print("No non-zero data to plot")
        return
    
    threshold = 3
    total = data.sum()
    slice_percentages = (data / total) * 100
    
    pull_values = [0.0 if p >= threshold else 0.2 for p in slice_percentages]
    text_positions = ['inside' if p >= threshold else 'outside' for p in slice_percentages]

    # Apply PSR_TYPE_MAPPING to the names
    names = data.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x))
    colors = [PSR_COLORS.get(psr_type_name, '#808080') for psr_type_name in names] 
    
    # Create a DataFrame with our calculated percentages
    plot_df = pd.DataFrame({
        'names': names,
        'values': data.values,
        'percentages': slice_percentages
    })
    
    fig = px.pie(
        plot_df,
        values='values',
        names='names',
        title="Electricity Mix by Source Type (Averaged Power)",
        color_discrete_sequence=px.colors.qualitative.Set3,
        # color_discrete_sequence=colors,
        hole=.2,
        custom_data=['percentages']  # Include our calculated percentages
    )
    
    fig.update_traces(
        textinfo='percent+label',
        textposition=text_positions,
        pull=pull_values,
        # marker=dict(colors=colors), # TODO use custom colors
        texttemplate='%{label}<br> %{customdata[0]:.1f}% | %{value:.1f} MW',  # Use our calculated percentages
        hovertemplate="%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} MW<extra></extra>",
        textfont=dict(size=10),
        insidetextorientation='auto',
        # insidetextanchor="start"
    )
    
    fig.update_layout(
        showlegend=True,
        width=1200,
        height=900,
        title_x=0.5,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=1.9
        ),
        annotations=[dict(
            text="Source: Energy Data",
            showarrow=False,
            x=0.5,
            y=-0.1,
            xref="paper",
            yref="paper"
        )]
    )
    
    return fig


def _plot_hierarchical(data_aggregated: pd.DataFrame, data_by_country: dict[str, pd.DataFrame], config: dict[str, bool|str] = None):
    import plotly.express as px
    """Creates a sunburst chart with hierarchy determined by 'by' parameter."""

    # Time-aggregate each country's data first
    total_hours = len(data_aggregated)
    data_by_country_time_aggregated = {
        country: _time_aggregation(df) for country, df in data_by_country.items()
    }

    # Calculate the total power for percentage calculations
    total_power = sum(series.sum() for series in data_by_country_time_aggregated.values())
    print(f"{total_hours=}")
    print(f"{total_power=}")
    # Create records for the hierarchical structure
    records = []

    # Add country and source records
    for country, series in data_by_country_time_aggregated.items():
        country_power = series.sum()
        country_energy = country_power * total_hours
        # print("COUNTRY:", country)
        # print("COUNTRY POWER:", country_power)
        # print("TOTAL POWER:", total_power)
        # print(f"PERCENTAGE:", country_power/total_power)
        # print(f"PERCENTAGE: {(country_power / total_power):.1f}")
        # Add country level
        records.append({
            'id': country,
            'parent': '',
            'label': country,
            'power': country_power,
            'is_leaf': False,
            'hover_text': (
                f"<b>{country}</b><br>"
                f"{(country_power / total_power * 100):.1f}% of total<br>"
                f"{country_power:.0f} MW (average)<br>"
                f"{_calc_energy_string(country_energy)}"
            )
        })

        # Add source level for each country
        for source_type, power in series.items():
            if power > 0:  # Only add non-zero values
                source_name = PSR_TYPE_MAPPING.get(source_type, source_type)
                energy = power * total_hours
                id = f"{country}/{source_name}"
                records.append({
                    'id': f"{country}/{source_name}",
                    'parent': country,
                    'label': source_name,
                    'power': power,
                    'is_leaf': True,
                    'hover_text': (
                        f"<b>{id}</b><br>"
                        f"{(power / country_power * 100):.1f}% of {country}<br>"
                        f"{(power / total_power * 100):.1f}% of total<br>"
                        f"{power:.0f} MW (average)<br>"
                        f"{_calc_energy_string(energy)}"
                    )
                })
    print(records)

    # Convert records to DataFrame
    df = pd.DataFrame(records)

    # Create sunburst chart
    fig = px.sunburst(
        df,
        ids='id',
        names='label',
        parents='parent',
        values='power',
        custom_data=['hover_text']
    )

    # Update hover template for all traces
    fig.update_traces(
        insidetextorientation='radial',    
        # textinfo='label+percent parent',  # Don't use percent, since it is relative to parent and not total
        # texttemplate='%{customdata[1]}',  # Use the custom_text for display
        hovertemplate='%{customdata[0]}<extra></extra>',
        branchvalues='total'
    )

    # Customize layout
    # fig.update_layout(
    #     width=800,
    #     height=800,
    #     title={
    #         'text': "Energy Distribution by Country and Source",
    #         'x': 0.5,
    #         'xanchor': 'center'
    #     }
    # )

    return fig


def _plot_internal_bokeh_2(df: pd.DataFrame, *_):
    from bokeh.plotting import figure
    from bokeh.transform import cumsum
    from bokeh.palettes import Set3
    from math import pi
    from bokeh.models import ColumnDataSource, Title, Label

    data = _time_aggregation(df)
    
    # Only plot non-zero values
    mask = data > 0
    data = data[mask]

    if data.empty:
        print("No non-zero data to plot")
        return

    # Prepare data
    total = data.sum()
    source_data = pd.DataFrame({
        'source': data.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x)),
        'value': data.values,
        'percentage': data / total * 100,
        'angle': data.values / total * 2 * pi,
        'color': Set3[12][:len(data)] if len(data) <= 12 else (Set3[8] * (len(data) // 8 + 1))[:len(data)]
    })
    
    source_data['start_angle'] = source_data['angle'].cumsum().shift(fill_value=0)
    source_data['end_angle'] = source_data['start_angle'] + source_data['angle']
    
    source = ColumnDataSource(source_data)

    # Modify the figure creation to keep original size
    p = figure(height=700, width=800,  # Return to original dimensions
              tools="hover", tooltips="@source: @value{0,0.0} MW (@percentage{0.1}%)",
              x_range=(-1.5, 1.5), y_range=(-1.5, 1.5))

    # Draw the outer wedges
    p.wedge(x=0, y=0,
            start_angle='start_angle',
            end_angle='end_angle',
            radius=1.0,
            color='color',
            legend_field='source',
            source=source)
    
    # Draw the inner circle to create the donut hole
    p.circle(x=0, y=0, radius=0.3, fill_color="white", line_color=None)

    # Customize appearance
    p.axis.visible = False
    p.grid.grid_line_color = None
    p.outline_line_color = None # type: ignore
    
    # Add title
    p.add_layout(Title(text="Electricity Mix by Source Type (Averaged Power)", text_font_size="16px"), 'above')
    
    # Add source attribution
    source_label = Label(x=0, y=-1.5, text="Source: ENTSO-E",  # Changed y from -1.3 to -1.5
                        text_align='center', text_baseline='top')
    p.add_layout(source_label)
    
    # Modify the legend settings to move it slightly more to the right
    p.legend.location = "right"
    p.legend.click_policy = "hide"
    p.legend.border_line_color = None
    p.legend.background_fill_alpha = 0.7
    p.legend.glyph_height = 20
    p.legend.glyph_width = 20
    p.legend.label_text_font_size = '10pt'
    p.legend.margin = 20  # Add margin to move legend further right

    return p


def _calc_energy_string(energy_in_MWh: float) -> str:
        # Define conversion factors
        GWh_FACTOR = 1000
        TWh_FACTOR = 1000000
        
        # Determine the appropriate unit
        if energy_in_MWh >= TWh_FACTOR:
            # Convert to TWh
            value = energy_in_MWh / TWh_FACTOR
            unit = "TWh"
        elif energy_in_MWh >= GWh_FACTOR:
            # Convert to GWh
            value = energy_in_MWh / GWh_FACTOR
            unit = "GWh"
        else:
            # Keep in MWh
            value = energy_in_MWh
            unit = "MWh"
        
        # Format the value to ensure at least 4 significant figures
        # We use .4g for general format with at least 4 significant digits
        formatted_value = format(value, '.4g')
        
        # Return the formatted string
        return f"{formatted_value} {unit}"