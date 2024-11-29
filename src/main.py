import logging
import sys
from pathlib import Path

from time_pattern import AdvancedPattern

# Add the project root directory to Python path
sys.path.append(str(Path(__file__).parent))

from data_fetcher import SimpleInterval
from core import reset_cache, initialize_cache, generate_visualization

logging.getLogger("matplotlib").setLevel(logging.WARNING)

import argparse
from datetime import datetime

def main():
    args = parse_arguments()

    if args.reset_cache:
        reset_cache()

    if args.initialize_cache:
        initialize_cache()

    if args.start_date and args.end_date:
        data_request = SimpleInterval(args.start_date, args.end_date)
    elif args.pattern:
        data_request = args.pattern
    else:
        print("No date parameters provided. Shutting down.")
        return
    
    config = dict(
        plot_mode=args.plot_mode if args.plot_mode else "aggregated"
    )
    

    fig = generate_visualization(
        data_request,
        config=config
    )
    
    if fig is not None:
        if str(type(fig).__module__).startswith('plotly'):
            print("BACKEND: Plotly")
            fig.show()  # type: ignore # Show Plotly figure in browser
        elif str(type(fig).__module__).startswith('bokeh'):
            print("BACKEND: Bokeh")
            from bokeh.plotting import show  # type: ignore
            show(fig)  # type: ignore # Show Bokeh figure in browser
        else:
            print("BACKEND: Matplotlib")
            # Save matplotlib figure to HTML and open in browser
            import mpld3 # type: ignore
            import webbrowser
            import tempfile
            import os
            
            # Create temporary HTML file
            temp_path = os.path.join(tempfile.gettempdir(), 'matplotlib_figure.html')
            html_str = mpld3.fig_to_html(fig)
            with open(temp_path, 'w') as f:
                f.write(html_str)
            
            # Open in browser
            webbrowser.open('file://' + temp_path)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Electricity Consumption Share Calculator for Portugal"
    )
    parser.add_argument(
        "--start_date",
        required=False,
        type=parse_datetime,
        help="Start date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--end_date",
        required=False,
        type=parse_datetime,
        help="End date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--pattern",
        required=False,
        type=parse_pattern,
        help="End date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)",
    )
    parser.add_argument(
        "--plot_calc_function",
        default="plot_discriminate_by_country",
        help="Plot calculating function",
    )
    # parser.add_argument(
    #     "--backend",
    #     help="Type of visualization to generate",
    # )
    parser.add_argument(
        "--plot-mode",
        help="Type of plot",
    )
    parser.add_argument(
        "--reset-cache", action="store_true", help="Reset the data cache"
    ) 
    parser.add_argument(
        "--initialize-cache", action="store_true", help="Initialize the data cache"
    ) 
    return parser.parse_args()


def parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid date or datetime format: {value}. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS."
            )
        
def parse_pattern(string):
    fields = string.split("|")
    assert len(fields) == 4
    return AdvancedPattern(*fields)


if __name__ == "__main__":
    main()

# Example usage:
# python src\main.py --start_date 2015-01-01 --end_date 2015-12-31 --visualization simple
