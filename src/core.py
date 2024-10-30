from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
import analyzer
from typing import Optional
from tqdm import tqdm  # Add this import
import asyncio  # Add this import

from utils import RECORDS_START, current_day_start

def initialize_cache():
    data_fetcher = ENTSOEDataFetcher()
    data_fetcher.reset_cache()
    
    # Calculate total number of years to fetch
    start = RECORDS_START
    end = current_day_start()
    total_years = (end.year - start.year) + 1
    
    print(f"Initializing cache from {start.date()} to {end.date()}")
    print(f"This will fetch approximately {total_years} years of data")
    print("This operation may take several minutes...")
    
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
        if visualize_type == "simple":
            return analyzer.plot(data)
        elif visualize_type == "country-source":
            # TODO: Implement when needed
            pass
        elif visualize_type == "source-country":
            # TODO: Implement when needed
            pass
        else:
            return None # Handle invalid visualize_type
    except Exception as e:
        print(f"An error occurred: {e}") # Log the error for debugging
        return None

