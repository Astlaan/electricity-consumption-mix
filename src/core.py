from datetime import datetime
from data_fetcher import ENTSOEDataFetcher, SimpleInterval, DataRequest
import analyzer
from typing import Optional
from tqdm import tqdm  # Add this import
import asyncio  # Add this import
import logging

from utils import RECORDS_START, maximum_date_end_exclusive

logger = logging.getLogger(__name__) # Add logger

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

def generate_visualization(
        data_request: DataRequest, 
        backend: str,
        plot_calc_function: str,
        plot_type = "simple"):
    """
    Core visualization logic used by both CLI and API.
    Returns a Plotly figure object or None if visualization type is invalid or an error occurs.
    """
    data_fetcher = ENTSOEDataFetcher()

    try:
        data = data_fetcher.get_data(data_request)
        if (data is None or 
            data.generation_pt.empty or 
            data.generation_es.empty or 
            data.flow_pt_to_es.empty or 
            data.flow_es_to_pt.empty):
            logger.warning("No data found for the specified date range.")
            return None
        
        if plot_calc_function == "plot":
            if plot_type != "simple":
                raise ValueError("plot_calc_function 'plot' only supports plot_type 'simple'")
            fig = analyzer.plot(data, backend)
        elif plot_calc_function == "plot_discriminate_by_country":
            fig = analyzer.plot_discriminate_by_country(data, backend, plot_type)
        else:
            logger.warning(f"Invalid plot type: {plot_calc_function}")
            return None
            
        return fig
    except Exception as e:
        logger.exception(f"An error occurred during visualization generation: {e}") # Log the error with traceback
        return None
