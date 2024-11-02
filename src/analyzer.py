from data_fetcher import Data
import pandas as pd
import numpy as np
from typing import Dict
from config import SOURCE_COLORS, COUNTRY_COLORS, PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe
# import plotly.express as px # Import px (commented for now)
import matplotlib.pyplot as plt

pd.set_option('display.max_columns', None)  # Show all columns
pd.set_option('display.max_rows', None)     # Show all rows
pd.set_option('display.width', None)        # Set width to expand to full display
pd.set_option('display.max_colwidth', None)

cmap = plt.get_cmap('tab20')

def ensure_index_and_sorting(data: Data):
    # This is handy while the stash fixing saved/loaded indexes is not fixed
    def _ensure_index_and_sorting(df):
        if 'start_time' in df.columns:
            df = df.set_index('start_time')
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')] # Remove duplicates keeping last value
        return df

    data.generation_pt = _ensure_index_and_sorting(data.generation_pt)
    data.generation_es = _ensure_index_and_sorting(data.generation_es)
    data.flow_pt_to_es = _ensure_index_and_sorting(data.flow_pt_to_es)
    data.flow_es_to_pt = _ensure_index_and_sorting(data.flow_es_to_pt)

    # Verify all dataframes have identical indexes
    ref_index = data.generation_pt.index
    for df_name, df in [('generation_es', data.generation_es),
                       ('flow_pt_to_es', data.flow_pt_to_es),
                       ('flow_es_to_pt', data.flow_es_to_pt)]:
        if not df.index.equals(ref_index):
            raise ValueError(f"Index mismatch in {df_name} compared to generation_pt")

    return data

def add(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.add(df2, fill_value=0)

def sub(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.sub(df2, fill_value=0)



def plot(data: Data):

    # If start_time is a column, set it as index. If it's already the index, nothing changes
    data = ensure_index_and_sorting(data)

    G_pt = data.generation_pt[data.generation_pt.columns.intersection(PSR_TYPE_MAPPING.keys())]
    G_es = data.generation_es[data.generation_es.columns.intersection(PSR_TYPE_MAPPING.keys())]
    F_pt_es = data.flow_pt_to_es["Power"].values[:, None]
    F_es_pt = data.flow_es_to_pt["Power"].values[:, None]
    flow_per_source_pt_es = F_pt_es * (G_pt/G_pt.sum(axis=1).values[0])
    flow_per_source_es_pt = F_es_pt * (G_es / G_es.sum(axis = 1).values[0])
    consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

    fig = _plot_internal_matplotlib(consumption_per_source)
    return fig 



def _plot_internal_matplotlib_2(df: pd.DataFrame) -> plt.Figure:
    plt.clf()
    plt.close('all')
    fig = plt.figure(figsize=(10, 8))
    
    df = _time_aggregation(df)

    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return fig

    # Rename the index using PSR_TYPE_MAPPING
    df.index = df.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x))

    # Get colors from colormap
    colors = cmap(np.linspace(0, 1, len(df)))

    plt.pie(df, labels=df.index, colors=colors,
            autopct='%1.1f%%', textprops={'fontsize': 8})
    plt.title("Electricity Mix by Source Type")
    plt.axis('equal')
    plt.tight_layout()
    result = fig
    plt.close(fig)  # Clean up
    return result

def _plot_internal_matplotlib(df: pd.DataFrame) -> plt.Figure:
    plt.clf()
    plt.close('all')
    fig = plt.figure(figsize=(10, 7))
    
    df = _time_aggregation(df)

    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return fig

    # Rename the index using PSR_TYPE_MAPPING
    df.index = df.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x))

    # Calculate percentages and determine which slices should be pulled out
    percentages = df / df.sum() * 100
    threshold = 5
    pull_values = [0.2 if p < threshold else 0.0 for p in percentages]
    
    def make_autopct(values, pcts):
        def my_autopct(pct):
            # Find the closest percentage value (to handle floating point comparison)
            idx = min(range(len(pcts)), key=lambda i: abs(pcts[i] - pct))
            return f'{pct:.1f}%\n{values.iloc[idx]:.0f} MW'
        return my_autopct

    # Create pie chart with a hole (donut chart)
    wedges, texts, autotexts = plt.pie(
        df, 
        labels=df.index,
        colors=cmap(np.linspace(0, 1, len(df))),
        autopct=make_autopct(df, percentages),
        pctdistance=0.85,
        wedgeprops=dict(width=0.5),  # Creates donut hole
        explode=pull_values,  # Pull out small slices
        textprops={'fontsize': 8}
    )

    # Adjust text positions based on percentage
    for i, p in enumerate(percentages):
        if p < threshold:
            # Move text outward for small slices
            texts[i].set_position((1.5 * texts[i].get_position()[0], 
                                 1.5 * texts[i].get_position()[1]))
            autotexts[i].set_position((1.5 * autotexts[i].get_position()[0], 
                                     1.5 * autotexts[i].get_position()[1]))

    plt.title("Electricity Mix by Source Type", pad=20)
    
    # Add source annotation at bottom
    plt.annotate(
        "Source: ENTSO-E",
        xy=(0.5, -0.1),
        xycoords='figure fraction',
        ha='center',
        va='center'
    )

    plt.axis('equal')
    plt.tight_layout()
    
    result = fig
    plt.close(fig)  # Clean up
    return result

def _plot_internal_plotly(df: pd.DataFrame) -> None:
    df = _time_aggregation(df)

    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return

    # Determine which slices should have outside labels (e.g., less than 5%)
    threshold = 5
    percentages = df / df.sum() * 100
    pull_values = [0.0 if p >= threshold else 0.2 for p in percentages]
    text_positions = ['inside' if p >= threshold else 'outside' for p in percentages]

    # Commented out plotly-specific code for now
    # fig = px.pie(
    #     values=df.values,
    #     names=df.index,
    #     title="Electricity Mix by Source Type",
    #     color_discrete_sequence=px.colors.qualitative.Set3,
    #     hole=.2
    # )
    fig = None  # Placeholder while plotly is disabled

    fig.update_traces(
        textinfo='percent+label+value',
        textposition=text_positions,
        pull=pull_values,
        texttemplate='%{label}<br>%{value:,.0f} MW<br>%{percent}',
        textfont=dict(size=10),
        insidetextorientation='horizontal'
    )

    fig.update_layout(
        showlegend=True,
        width=1000,
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
            text="Source: ENTSO-E",
            showarrow=False,
            x=0.5,
            y=-0.1,
            xref="paper",
            yref="paper"
        )]
    )
    
    return fig

def _format_date_range(df: pd.DataFrame) -> str:
    start_date = df.index.min()
    end_date = df.index.max()
    return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"

def _time_aggregation(df: pd.DataFrame) -> pd.Series: # aggregate_by_source_type
    """Aggregate data by source type only."""
    # Remove columns where all values are 0
    df = df.loc[:, (df != 0).any()]
    # Fill any NaN values with 0
    df = df.fillna(0)

    # Group by source type (in case multiple B-codes map to same source)
    grouped_data = df.sum()

    return grouped_data
