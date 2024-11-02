from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
import analyzer
from typing import Optional
from tqdm import tqdm  # Add this import
import asyncio  # Add this import
import logging

from utils import RECORDS_START, current_day_start

logger = logging.getLogger(__name__) # Add logger

def initialize_cache():
    data_fetcher = ENTSOEDataFetcher()
    data_fetcher.reset_cache()
    
    # Calculate total number of years to fetch
    start = RECORDS_START
    end = current_day_start()
    total_years = (end.year - start.year) + 1
    
    logger.info(f"Initializing cache from {start.date()} to {end.date()}")
    logger.info(f"This will fetch approximately {total_years} years of data")
    logger.info("This operation may take several minutes...")
    
    with tqdm(total=total_years * 4, desc="Fetching data") as pbar:
        def progress_callback():
            pbar.update(1)
        
        data_fetcher.get_data(RECORDS_START, current_day_start(), progress_callback=progress_callback)

def generate_visualization(start_date: datetime, 
                         end_date: datetime, 
                         visualize_type: str = "simple",
                         reset_cache: bool = False) -> Optional[object]:
    """
    Core visualization logic used by both CLI and API.
    Returns a Plotly figure object or None if visualization type is invalid or an error occurs.
    """
    data_fetcher = ENTSOEDataFetcher()
    
    if reset_cache:
        data_fetcher.reset_cache()

    try:
        data = data_fetcher.get_data(start_date, end_date)
        if (data is None or 
            data.generation_pt.empty or 
            data.generation_es.empty or 
            data.flow_pt_to_es.empty or 
            data.flow_es_to_pt.empty):
            logger.warning("No data found for the specified date range.")
            return None

        if visualize_type == "simple":
            return analyzer.plot(data)
        elif visualize_type == "country-source":
            # TODO: Implement when needed
            pass
        elif visualize_type == "source-country":
            # TODO: Implement when needed
            pass
        else:
            logger.error(f"Invalid visualization type: {visualize_type}")
            return None # Handle invalid visualize_type
    except Exception as e:
        logger.exception(f"An error occurred during visualization generation: {e}") # Log the error with traceback
        return None

