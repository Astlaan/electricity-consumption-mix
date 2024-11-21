from data_fetcher import Data
import pandas as pd
import numpy as np
from config import PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe, apply_to_fields

pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)     # Show all rows
pd.set_option('display.width', None)        # Set width to expand to full display
pd.set_option('display.max_colwidth', None)



def _format_date_range(df: pd.DataFrame) -> str:
    start_date = df.index.min()
    end_date = df.index.max()
    return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

def _time_aggregation(df: pd.DataFrame) -> pd.DataFrame: # aggregate_by_source_type
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

def plot_discriminate_by_country(data: Data, mode: str):
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
        fig = plot_func(consumption_per_source)
    else:
        raise ValueError(f"Plotting function '{mode}' not found in globals.")

    return fig



def _plot_internal_plotly_2(df: pd.DataFrame) -> None:
    import plotly.express as px
    df = _time_aggregation(df)

    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return

    # Calculate percentages
    percentages = df / df.sum() * 100
    
    # Determine which slices should have outside labels (e.g., less than 5%)
    threshold = 5
    pull_values = [0.0 if p >= threshold else 0.2 for p in percentages]
    text_positions = ['inside' if p >= threshold else 'outside' for p in percentages]

    fig = px.pie(
        values=df.values,
        names=df.index,
        title="Electricity Mix by Source Type (Averaged Power)",
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=.2
    )
    
    # Update traces with more sophisticated label positioning
    fig.update_traces(
        textinfo='percent+label+value',
        textposition=text_positions,
        pull=pull_values,
        texttemplate='%{label}<br>%{value:,.2f}<br>%{percent:.1f}%',
        textfont=dict(size=10),
        insidetextorientation='horizontal'
    )
    
    fig.update_layout(
        showlegend=True,  # Enable legend for better readability
        width=900,        # Slightly wider to accommodate outside labels
        height=700,
        title_x=0.5,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=1.1
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


def _plot_internal_bokeh_2(df: pd.DataFrame):
    from bokeh.plotting import figure
    from bokeh.transform import cumsum
    from bokeh.palettes import Set3
    from math import pi
    from bokeh.models import ColumnDataSource, Title, Label

    df = _time_aggregation(df)
    
    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return

    # Prepare data
    total = df.sum()
    source_data = pd.DataFrame({
        'source': df.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x)),
        'value': df.values,
        'percentage': df / total * 100,
        'angle': df.values / total * 2 * pi,
        'color': Set3[12][:len(df)] if len(df) <= 12 else (Set3[8] * (len(df) // 8 + 1))[:len(df)]
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
    p.outline_line_color = None
    
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

def _plot_hierarchical(data_aggregated: pd.DataFrame, data_by_country: dict[str, pd.DataFrame], config: dict[str, bool|str] = None):
    import plotly.express as px
    """Creates a sunburst chart with hierarchy determined by 'by' parameter."""

    # Time-aggregate each country's data first
    
    total_hours = len(data_aggregated)
    data_by_country_time_aggregated = {
        country: _time_aggregation(df) 
        for country, df in data_by_country.items()
    }

    # Convert dictionary of Series into a single DataFrame
    df_list = []
    for country, series in data_by_country_time_aggregated.items():
        # Convert series to DataFrame
        df = pd.DataFrame({
            'power': series,
            'country': country,
            'source': series.index
        })
        df_list.append(df)

    # Concatenate all DataFrames and calculate extras
    combined_df = pd.concat(df_list, ignore_index=True)
    combined_df['source'] = combined_df['source'].map(lambda x: PSR_TYPE_MAPPING.get(x, x))
    combined_df['national_percentage'] = combined_df.groupby('country')['power'].transform(lambda x: x/x.sum() * 100)
    combined_df['global_percentage'] = combined_df['power']/combined_df['power'].sum() * 100
    combined_df['energy'] = combined_df['power'] * total_hours
    combined_df['energy_string'] = combined_df['energy'].map(_calc_energy_string)

    
    print(combined_df)


    fig = px.sunburst(combined_df, path=['country', 'source'], values='power', custom_data=['power', 'global_percentage', 'national_percentage', 'energy_string'])

    # Add a second hover template for child nodes only
    fig.update_traces(insidetextorientation='radial')


    # fig.update_traces(
    #     hovertemplate='<b>%{id}</b><br>' +
    #                   '%{customdata[2]:.1f}% of %{parent}<br>' +
    #                   '%{customdata[1]:.1f}% of total<br>' +
    #                   '%{customdata[0]:.0f} MW (average)<br>' +
    #                   '%{customdata[3]}' +
    #                   '<extra></extra>',
    #     level = 0
    # )    

    # fig.update_traces(
    #     hovertemplate='<b>%{id}</b><br>' +
    #                   '%{customdata[1]:.1f}% of total<br>' +
    #                   '%{customdata[0]:.0f} MW (average)<br>' +
    #                   '%{customdata[3]}' +
    #                   '<extra></extra>',
    #     level = 1
    # )
    
    fig.update_traces(hovertemplate=hovertemplate)

    
    # import sys
    # sys.exit()
    return fig