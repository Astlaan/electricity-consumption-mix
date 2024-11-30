from typing import Tuple
from data_fetcher import Data
import pandas as pd
import numpy as np
from config import PSR_COLORS, PSR_TYPE_MAPPING
from utils import apply_to_fields
import logging

logger = logging.getLogger(__name__)

# pd.set_option('display.max_columns', None)  # Show all columns
# pd.set_option('display.max_rows', None)     # Show all rows
# pd.set_option('display.width', None)        # Set width to expand to full display
# pd.set_option('display.max_colwidth', None)


def _format_date_range(df: pd.DataFrame) -> str:
    start_date = df.index.min()
    end_date = df.index.max()
    return f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}"


def _time_aggregation(df: pd.DataFrame) -> pd.Series:  # aggregate_by_source_type
    """Aggregate data by source type only."""
    # Remove columns where all values are 0
    df = df.loc[:, (df != 0).any()]
    # Fill any NaN values with 0
    # df = df.fillna(0) # TODO fix
    # df = df.ffill()
    df = df.interpolate("linear")
    # Interpolate does not remove first NaNs, which is good.
    # Removes last NaNs similar to ffill, however, it seems that when a source gets deactivated for
    # good (ex. Fossil Hard Coal in PT), it's power becomes 0 instead of NaN in PT, ES, FR
    # France may have mislabeled a lot of its 0 MW periods as NaNs

    # Group by source type (in case multiple B-codes map to same source)
    grouped_data = df.mean()
    return grouped_data


def ensure_index_and_sorting(data: Data):
    # This is handy while the stash fixing saved/loaded indexes is not fixed
    def _ensure_index_and_sorting(df):
        if "start_time" in df.columns:
            df = df.set_index("start_time")
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        # Remove duplicates keeping last value
        df = df[~df.index.duplicated(keep="last")]
        return df

    apply_to_fields(data, _ensure_index_and_sorting)
    data.assert_equal_length()

    return data


def add(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.add(df2, fill_value=0)


def sub(df1: pd.DataFrame, df2: pd.DataFrame):
    df1.sub(df2, fill_value=0)


# def plot_old(data: Data, mode: str):
#     logger.debug("FUNCTION: plot")

#     # If start_time is a column, set it as index. If it's already the index, nothing changes
#     data = ensure_index_and_sorting(data)

#     psr_types = list(PSR_TYPE_MAPPING.keys())

#     G_pt = data.generation_pt[data.generation_pt.columns.intersection(psr_types)]
#     G_es = data.generation_es[data.generation_es.columns.intersection(psr_types)]
#     G_fr = data.generation_fr[data.generation_fr.columns.intersection(psr_types)]
#     F_pt_es = data.flow_pt_to_es["Power"].values[:, None]
#     F_es_pt = data.flow_es_to_pt["Power"].values[:, None]
#     F_fr_es = data.flow_fr_to_es["Power"].values[:, None]
#     F_es_fr = data.flow_es_to_fr["Power"].values[:, None]

#     # Without france
#     # flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
#     # flow_per_source_es_pt = F_es_pt * (G_es.div(G_es.sum(axis=1), axis=0))
#     # consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

#     # With France
#     flow_per_source_fr_es = F_fr_es * (G_fr.div(G_fr.sum(axis=1), axis=0)) # TODO verify [0]!!!!!!!!!!!!!!!!!!!!!!
#     flow_per_source_es_fr = F_es_fr * (G_es.div(G_es.sum(axis=1), axis=0))
#     G_es_prime = G_es.sub(flow_per_source_es_fr, fill_value=0).add(flow_per_source_fr_es, fill_value=0)

#     flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
#     flow_per_source_es_pt = F_es_pt * (G_es_prime.div(G_es_prime.sum(axis=1), axis=0))
#     consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

#     plot_func = globals()[f'{mode}']
#     fig = plot_func(consumption_per_source)
#     return fig


def analyze(data: Data) -> Tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    # Ensure 'start_time' is set as index and sorted
    data = ensure_index_and_sorting(data)

    # PSR_TYPE_MAPPING is assumed to be a predefined mapping of types
    psr_types = list(PSR_TYPE_MAPPING.keys())

    # Extract generation data for PT, ES, FR
    G_pt = data.generation_pt[data.generation_pt.columns.intersection(psr_types)]
    G_es = data.generation_es[data.generation_es.columns.intersection(psr_types)]
    G_fr = data.generation_fr[data.generation_fr.columns.intersection(psr_types)]

    # Extract flow data for various transitions
    # Flow from PT to ES
    F_pt_es = data.flow_pt_to_es["Power"].values[:, None]
    # Flow from ES to PT
    F_es_pt = data.flow_es_to_pt["Power"].values[:, None]
    # Flow from FR to ES
    F_fr_es = data.flow_fr_to_es["Power"].values[:, None]
    # Flow from ES to FR
    F_es_fr = data.flow_es_to_fr["Power"].values[:, None]

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
    # Avoid division by zero
    Available_ES_Generation[Available_ES_Generation == 0] = 1
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
    Ges_contribution = G_es.values * ES_fraction  # TODO why values here?

    # 3. French Contribution (Gfr_contribution)
    # Compute FR fraction
    FR_fraction = (F_es_pt * (F_fr_es / sum_G_fr)) / Available_ES_Generation
    # Expand dimensions to match G_fr dimensions
    FR_fraction = np.tile(FR_fraction, (1, G_fr.shape[1]))
    Gfr_contribution = G_fr.values * FR_fraction  # TODO why values here?

    # Convert contributions to DataFrames with appropriate indices and columns
    Ges_contribution = pd.DataFrame(
        Ges_contribution, index=G_es.index, columns=G_es.columns
    )
    Gfr_contribution = pd.DataFrame(
        Gfr_contribution, index=G_fr.index, columns=G_fr.columns
    )

    # ------------------------------
    # Compute Total Consumption per Source
    # ------------------------------

    aggregated = Gpt_contribution.copy()
    aggregated = aggregated.add(Ges_contribution, fill_value=0)
    aggregated = aggregated.add(Gfr_contribution, fill_value=0)

    # ------------------------------
    # Organize the Contributions into a Dictionary
    # ------------------------------
    contributions = {
        "PT": Gpt_contribution,
        "ES": Ges_contribution,
        "FR": Gfr_contribution,
    }
    return aggregated, contributions


def plot(data: Data, config: dict):
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

    aggregated, contributions = analyze(data)

    # ------------------------------
    # Plotting
    # ------------------------------

    match config["plot_mode"]:
        case "aggregated":
            fig = _plot_aggregated(aggregated)
        case "discriminated":
            fig = _plot_hierarchical(aggregated, contributions, config)
        case _:
            raise ValueError(f"plot_mode {config["plot_mode"]} is not supported.")
    return fig


def _plot_aggregated(df: pd.DataFrame, *_):
    import plotly.express as px

    data = _time_aggregation(df)

    # Only plot non-zero values
    mask = data > 0
    data = data[mask]

    if data.empty:
        logger.info("No non-zero data to plot")
        return

    threshold = 3
    total = data.sum()
    slice_percentages = (data / total) * 100

    pull_values = [0.0 if p >= threshold else 0.1 for p in slice_percentages]
    text_positions = [
        "inside" if p >= threshold else "outside" for p in slice_percentages
    ]

    # Apply PSR_TYPE_MAPPING to the names
    names = data.index.map(lambda x: PSR_TYPE_MAPPING.get(x, x))
    colors = [PSR_COLORS.get(psr_type_name, "#808080") for psr_type_name in names]

    # Create a DataFrame with our calculated percentages
    plot_df = pd.DataFrame(
        {"names": names, "values": data.values, "percentages": slice_percentages}
    )

    # plot_df["hover_text"] = plot_df.apply()

    fig = px.pie(
        plot_df,
        values="values",
        names="names",
        color_discrete_sequence=px.colors.qualitative.Set3,
        # color_discrete_sequence=colors,
        hole=0,
        custom_data=["percentages"],  # Include our calculated percentages
    )

    fig.update_traces(
        textinfo="percent+label",
        textposition=text_positions,
        pull=pull_values,
        # marker=dict(colors=colors), # TODO use custom colors
        # Use our calculated percentages
        texttemplate="%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} " + "MW",
        hovertemplate="%{label}<br>%{customdata[0]:.1f}% | %{value:.1f} " + "MW",
        # textfont=dict(size=10),
        insidetextorientation="auto",
        # insidetextorientation='radial',
        # insidetextanchor="start"
    )

    fig.update_layout(
        showlegend=False,
        # width=1200,
        # height=900,
        width=900,
        height=800,
        # yaxis=dict(domain=[0.1, 0.9]),
        title={
            "text": "Portugal's Electricity Mix by Source Type",
            "x": 0.45,
            "y": 0.99,
        },
        # margin=dict(t=0, b=0, l=0, r=0),
        # legend=dict(
        #     orientation="v",
        #     yanchor="middle",
        #     y=0.5,
        #     xanchor="right",
        #     x=1.9
        # ),
    )

    _apply_figure_global_settings(fig)
    return fig


def _plot_hierarchical(
    data_aggregated: pd.DataFrame,
    data_by_country: dict[str, pd.DataFrame],
    config: dict[str, bool | str],
):
    import plotly.express as px

    """Creates a sunburst chart with hierarchy determined by 'by' parameter."""

    # Time-aggregate each country's data first
    total_hours = len(data_aggregated)
    data_by_country_time_aggregated = {
        country: _time_aggregation(df) for country, df in data_by_country.items()
    }

    # Calculate the total power for percentage calculations
    total_power = sum(
        series.sum() for series in data_by_country_time_aggregated.values()
    )
    logger.debug(f"{total_hours=}")
    logger.debug(f"{total_power=}")
    # Create records for the hierarchical structure
    records = []

    # Add country and source records
    for country, series in data_by_country_time_aggregated.items():
        country_power = series.sum()
        country_energy = country_power * total_hours
        percentage = country_power / total_power * 100
        # logger.debug("COUNTRY:", country)
        # logger.debug("COUNTRY POWER:", country_power)
        # logger.debug("TOTAL POWER:", total_power)
        # logger.debug(f"PERCENTAGE:", country_power/total_power)
        # logger.debug(f"PERCENTAGE: {(country_power / total_power):.1f}")
        # Add country level

        records.append(
            {
                "id": country,
                "parent": "",
                "label": country,
                "power": country_power,
                "is_leaf": False,
                "percentage": percentage,
                "hover_text": (
                    f"<b>{country}</b><br>"
                    f"{percentage:.1f}% of total<br>"
                    f"{country_power:.0f} MW (average)<br>"
                    # f"{country_power:.0f} " + _overlined('MW')  + "<br>"
                    f"{_calc_energy_string(country_energy)}"
                ),
            }
        )

        # Add source level for each country
        for source_type, power in series.items():
            if power > 0:  # Only add non-zero values
                source_name = PSR_TYPE_MAPPING.get(source_type, source_type)  # type: ignore
                energy = power * total_hours
                percentage = power / total_power * 100
                id = f"{country}/{source_name}"
                records.append(
                    {
                        "id": f"{country}/{source_name}",
                        "parent": country,
                        "label": source_name,
                        "power": power,
                        "is_leaf": True,
                        "percentage": percentage,
                        "hover_text": (
                            f"<b>{id}</b><br>"
                            f"{(power / country_power * 100):.1f}% of {country}<br>"
                            f"{percentage:.1f}% of total<br>"
                            f"{power:.0f} MW (average)<br>"
                            f"{_calc_energy_string(energy)}"
                        ),
                    }
                )
    logger.debug(records)

    # Convert records to DataFrame
    df = pd.DataFrame(records)

    # Create sunburst chart
    fig = px.sunburst(
        df,
        ids="id",
        names="label",
        parents="parent",
        values="power",
        custom_data=["percentage", "hover_text"],
        # title="Portugal's Electricity Mix by Source Type",
    )

    # Update hover template for all traces
    fig.update_traces(
        insidetextorientation="radial",
        # textinfo='label+percent parent',  # Don't use percent, since it is relative to parent and not total
        # texttemplate='%{customdata[1]}',  # Use the custom_text for display
        hovertemplate="%{customdata[1]}<extra></extra>",
        branchvalues="total",
    )

    # Customize layout
    fig.update_layout(
        width=700,
        height=800,
        title={
            "text": "Portugal's Electricity Mix by Source Type",
            "x": 0.5,
            "y": 0.99,
        },
    )

    _apply_figure_global_settings(fig)
    return fig


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
    formatted_value = format(value, ".4g")

    # Return the formatted string
    return f"{formatted_value} {unit}"


def _apply_figure_global_settings(fig):
    fig.update_layout(
        autosize=True,
        margin=dict(t=50, b=100, l=0, r=0),
        annotations=[
            dict(
                text="Source: https://portugal-electricity-mix.vercel.app<br>Data: ENTSO-E (European Network of Transmission System Operators for Electricity)",
                showarrow=False,
                x=0.5,
                y=-0.1,
            )
        ],
    )


def _overlined(string: str):
    # return f"&#772;{string}"
    # return f"\\overline{{\\text{{{string}}}}}"
    # return f"\u0305{string}"
    # return f"<i>{string}</i>"
    # return "M\u0305W\u0305"
    return f"<span style='text-decoration: overline;'>{string}</span>"
