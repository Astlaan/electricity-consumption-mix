from datetime import datetime
from data_fetcher import ENTSOEDataFetcher
import analyzer
from typing import Optional

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

