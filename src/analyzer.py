from data_fetcher import Data
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict
from config import SOURCE_COLORS, COUNTRY_COLORS, PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe
import plotly.express as px

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
    print("G_pt shape:", G_pt.shape)
    print("G_pt head:\n", G_pt.head())

    G_es = data.generation_es[data.generation_es.columns.intersection(PSR_TYPE_MAPPING.keys())]
    print("G_es shape:", G_es.shape)
    print("G_es head:\n", G_es.head())

    F_pt_es = data.flow_pt_to_es["Power"].values[:, None]
    print("F_pt_es shape:", F_pt_es.shape)
    print("F_pt_es head:\n", F_pt_es[:5])

    F_es_pt = data.flow_es_to_pt["Power"].values[:, None]
    print("F_es_pt shape:", F_es_pt.shape)
    print("F_es_pt head:\n", F_es_pt[:5])

    flow_per_source_pt_es = F_pt_es * (G_pt/G_pt.sum(axis=1).values[0])
    print("flow_per_source_pt_es shape:", flow_per_source_pt_es.shape)
    print("flow_per_source_pt_es head:\n", flow_per_source_pt_es[:5])

    flow_per_source_es_pt = F_es_pt * (G_es / G_es.sum(axis = 1).values[0])
    print("flow_per_source_es_pt shape:", flow_per_source_es_pt.shape)
    print("flow_per_source_es_pt head:\n", flow_per_source_es_pt[:5])
    print("flow_per_source_es_pt NUCLEAR:\n", flow_per_source_es_pt["B14"])

    print("IS EQUAL?: ", G_pt == G_pt.sub(flow_per_source_pt_es))

    consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)
    print("consumption_per_source shape:", consumption_per_source.shape)
    print("consumption_per_source head:\n", consumption_per_source.head())


    fig = _plot_internal(consumption_per_source)
    # TODO  maybe this doesn't work due to the Power column, that isn't matched in the other dfs?
    # probably fixed with the .values thing above


    # TODO: maybe this wont work since PT and ES don't have the same number of columns (ex. portugal doesnt have nuclear)

    return fig # Return the figure object



def _plot_internal(df: pd.DataFrame) -> None:
    plt.figure(figsize=(10, 8))

    df = _time_aggregation(df)

    # Only plot non-zero values
    mask = df > 0
    df = df[mask]

    if df.empty:
        print("No non-zero data to plot")
        return

    # Get colors from colormap
    colors = cmap(np.linspace(0, 1, len(df)))

    # plt.pie(df, labels=df.index, colors=colors,
    #         autopct='%1.1f%%', textprops={'fontsize': 8})
    # plt.title("Electricity Mix by Source Type")
    # plt.axis('equal')
    # plt.tight_layout()
    # plt.show()

    fig = px.pie(
        values=df.values,
        names=df.index,
        title="Electricity Mix by Source Type",
        #<br><sup>date range</sup>
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=.2 # Original was zero
    )
    
    # Update layout to match matplotlib's style
    # fig.update_traces(textinfo='percent+label+value', textposition='inside')

        # fig.update_layout(
    #     showlegend=False,
    #     width=800,
    #     height=640,
    #     title_x=0.5,
    # )

    # Determine which slices should have outside labels (e.g., less than 5%)
    threshold = 5
    print(df)
    percentages = df / df.sum() * 100
    print("percentages\n",percentages)
    pull_values = [0.0 if p >= threshold else 0.2 for p in percentages]
    text_positions = ['inside' if p >= threshold else 'outside' for p in percentages]

    fig.update_traces(
        textinfo='percent+label+value',
        textposition=text_positions,
        pull=pull_values,
        # texttemplate='%{label}<br>%{value:,.2f}<br>%{percent:.1f}%',
        texttemplate='%{label}<br>%{value:,.0f} MW<br>%{percent}',
        textfont=dict(size=10),
        insidetextorientation='horizontal'
    )

    fig.update_layout(
    showlegend=True,  # Enable legend for better readability
    width=1000,        # Slightly wider to accommodate outside labels
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



def _plot_internal_2(df: pd.DataFrame) -> None:
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
        title="Electricity Mix by Source Type",
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
    grouped_data = df.mean()

    return grouped_data
# def _plot_internal(df: pd.DataFrame) -> None:
#     plt.figure(figsize=(10, 8))

#     data = _aggregate_by_source_type(df)

#     # Only plot non-zero values
#     mask = data > 0
#     data = data[mask]

#     if data.empty:
#         print("No non-zero data to plot")
#         return

#     # Get colors from colormap
#     colors = self.cmap(np.linspace(0, 1, len(data)))

#     plt.pie(data, labels=data.index, colors=colors,
#             autopct='%1.1f%%', textprops={'fontsize': 8})
#     plt.title("Electricity Mix by Source Type")
#     plt.axis('equal')
#     plt.tight_layout()
#     plt.show()

def plot_source_country_pie(self, df: pd.DataFrame) -> None:
    plt.figure(figsize=(12, 10))

    # Clean and prepare data
    df = df.loc[:, (df != 0).any()]
    df = df.fillna(0)

    # Prepare data for plotting
    labels = []
    sizes = []
    colors = []

    for country in ["Portugal", "Spain"]:
        country_prefix = f"{country[:2]}_"
        country_columns = [col for col in df.columns if col.startswith(country_prefix)]

        for col in country_columns:
            source = col[3:]  # Remove country prefix
            value = df[col].mean()
            if value > 0:  # Only include non-zero values
                labels.append(f"{country}\n{source}")
                sizes.append(value)
                colors.append(
                    self.source_colors.get(source, self.source_colors["Other"])
                )

    if not sizes:
        print("No non-zero data to plot")
        return

    plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        textprops={"fontsize": 8},
    )
    plt.title(f"Electricity Mix by Source Type and Country")
    #<br><sup>date range</sup>
    plt.axis("equal")
    plt.tight_layout()
    plt.show()


def plot_nested_pie(self, df: pd.DataFrame) -> None:
    plt.figure(figsize=(14, 12))

    # Clean and prepare data
    df = df.loc[:, (df != 0).any()]
    df = df.fillna(0)

    # Prepare outer ring (countries)
    pt_data = df[[col for col in df.columns if col.startswith("PT_")]].mean()
    es_data = df[[col for col in df.columns if col.startswith("ES_")]].mean()
    country_sizes = [pt_data.sum(), es_data.sum()]

    if sum(country_sizes) == 0:
        print("No non-zero data to plot")
        return

    country_colors = [self.country_colors[country] for country in ["Portugal", "Spain"]]

    # Prepare inner ring (sources)
    source_sizes = []
    source_colors = []
    source_labels = []

    for country_data, country in zip([pt_data, es_data], ["Portugal", "Spain"]):
        if not country_data.empty:
            for source, value in country_data.items():
                if value > 0:  # Only include non-zero values
                    source_sizes.append(value)
                    source_colors.append(
                        self.source_colors.get(source[3:], self.source_colors["Other"])
                    )
                    source_labels.append(f"{country}\n{source[3:]}")

    # Plot outer ring (countries)
    plt.pie(
        country_sizes,
        colors=country_colors,
        radius=1.3,
        labels=["Portugal", "Spain"],
        autopct="%1.1f%%",
        textprops={"fontsize": 10},
    )

    # Plot inner ring (sources)
    if source_sizes:
        plt.pie(
            source_sizes,
            colors=source_colors,
            radius=1.0,
            labels=source_labels,
            autopct="%1.1f%%",
            textprops={"fontsize": 8},
        )

    plt.title("Electricity Mix by Country and Source Type")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()
