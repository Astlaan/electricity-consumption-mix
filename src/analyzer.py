from typing import Tuple
from data_types import Data
import pandas as pd
import numpy as np
from config import PSR_TYPE_MAPPING
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
    """Temporal aggregation of data."""
    grouped_data = df.mean()
    return grouped_data


def remove_empty_columns(df: pd.DataFrame):
    df = df.loc[:, (df != 0).any()]
    return df


def prepare_data(data: Data):
    # This is handy while the stash fixing saved/loaded indexes is not fixed
    def _ensure_index_and_sorting(df: pd.DataFrame):
        if "start_time" in df.columns:
            df = df.set_index("start_time")
            df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        # Remove duplicates keeping last value
        df = df[~df.index.duplicated(keep="last")]
        return df

    def _interpolate_missing_data(df: pd.DataFrame):
        # Remove columns where all values are 0
        df = df.interpolate("linear")
        # Interpolate does not remove first NaNs, which is good.
        # Removes last NaNs similar to ffill, however, it seems that when a source gets deactivated for
        # good (ex. Fossil Hard Coal in PT), it's power becomes 0 instead of NaN in PT, ES, FR
        # France may have mislabeled a lot of its 0 MW periods as NaNs
        return df

    apply_to_fields(data, _ensure_index_and_sorting)
    apply_to_fields(data, _interpolate_missing_data)
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
    data = prepare_data(data)

    # PSR_TYPE_MAPPING is assumed to be a predefined mapping of types
    psr_types = list(PSR_TYPE_MAPPING.keys())

    # Extract generation data for PT, ES, FR
    G_pt = data.generation_pt[data.generation_pt.columns.intersection(psr_types)]
    G_es = data.generation_es[data.generation_es.columns.intersection(psr_types)]
    G_fr = data.generation_fr[data.generation_fr.columns.intersection(psr_types)]

    # Extract flow data for various transitions
    # Flow from PT to ES
    F_pt_es = data.flow_pt_to_es["Power"].to_numpy()[:, np.newaxis]
    # Flow from ES to PT
    F_es_pt = data.flow_es_to_pt["Power"].to_numpy()[:, np.newaxis]
    # Flow from FR to ES
    F_fr_es = data.flow_fr_to_es["Power"].to_numpy()[:, np.newaxis]
    # Flow from ES to FR
    F_es_fr = data.flow_es_to_fr["Power"].to_numpy()[:, np.newaxis]

    # Should be equivalent to this:
    # flow_per_source_fr_es = F_fr_es * (G_fr.div(G_fr.sum(axis=1), axis=0))
    # flow_per_source_es_fr = F_es_fr * (G_es.div(G_es.sum(axis=1), axis=0))
    # G_es_prime = G_es.sub(flow_per_source_es_fr, fill_value=0).add(flow_per_source_fr_es, fill_value=0)

    # flow_per_source_pt_es = F_pt_es * (G_pt.div(G_pt.sum(axis=1), axis=0))
    # flow_per_source_es_pt = F_es_pt * (G_es_prime.div(G_es_prime.sum(axis=1), axis=0))
    # consumption_per_source = G_pt.sub(flow_per_source_pt_es, fill_value=0).add(flow_per_source_es_pt, fill_value=0)

    # Compute total generation for normalization
    sum_G_pt = G_pt.sum(axis=1).to_numpy()[:, np.newaxis]
    sum_G_es = G_es.sum(axis=1).to_numpy()[:, np.newaxis]
    sum_G_fr = G_fr.sum(axis=1).to_numpy()[:, np.newaxis]

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
    aggregated = remove_empty_columns(aggregated)

    # ------------------------------
    # Organize the Contributions into a Dictionary
    # ------------------------------
    contributions = {
        "PT": remove_empty_columns(Gpt_contribution),
        "ES": remove_empty_columns(Ges_contribution),
        "FR": remove_empty_columns(Gfr_contribution),
    }
    return aggregated, contributions
