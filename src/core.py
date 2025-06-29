from data_fetcher import ENTSOEDataFetcher, SimpleInterval, DataRequest
import analyzer
from tqdm import tqdm  # Add this import
import logging

from utils import RECORDS_START, maximum_date_end_exclusive

logger = logging.getLogger(__name__)  # Add logger


def reset_cache():
    data_fetcher = ENTSOEDataFetcher()
    data_fetcher.reset_cache()


def initialize_cache():
    data_fetcher = ENTSOEDataFetcher()
    # data_fetcher.reset_cache() // just adds data now

    # Calculate total number of years to fetch
    start = RECORDS_START
    end = maximum_date_end_exclusive()
    total_years = (end.year - start.year) + 1

    logger.info(f"Initializing cache from {start.date()} to {end.date()}")
    logger.info(f"This will fetch approximately {total_years} years of data")
    logger.info("This operation may take several minutes...")

    with tqdm(total=total_years * 4, desc="Fetching data") as pbar:

        def progress_callback():
            pbar.update(1)

        data_request = SimpleInterval(start, end)
        data_fetcher.get_data(data_request, progress_callback=progress_callback)


def generate_visualization(data_request: DataRequest, config: dict):
    """
    Core visualization logic used by both CLI and API.
    Returns a Plotly figure object or None if visualization type is invalid or an error occurs.
    """
    data_fetcher = ENTSOEDataFetcher()

    try:
        data = data_fetcher.get_data(data_request)
        if (
            data is None
            or data.generation_pt.empty
            or data.generation_es.empty
            or data.flow_pt_to_es.empty
            or data.flow_es_to_pt.empty
        ):
            raise ValueError("No data found for the specified date range.")

        aggregated, contributions = analyzer.analyze(data)
        print("data successfully generated")

        return aggregated, contributions
    except Exception as e:
        logger.exception(
            f"An error occurred during visualization generation: {e}"
        )  # Log the error with traceback
        return None, None
