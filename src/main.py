import logging

logging.getLogger("matplotlib").setLevel(logging.WARNING)

import argparse
from datetime import datetime
import core

def main():
    args = parse_arguments()

    if args.initialize_cache:
        core.initialize_cache()
        return

    if args.start_date is None or args.end_date is None:
        print("Error: --start_date and --end_date are required when not using --initialize-cache")
        return
    
    fig = core.generate_visualization(
        start_date=args.start_date,
        end_date=args.end_date,
        visualize_type=args.visualize,
        reset_cache=args.reset_cache
    )
    
    if fig is not None:
        if str(type(fig).__module__).startswith('plotly'):
            print("BACKEND: Plotly")
            fig.show()  # Show Plotly figure in browser
        elif str(type(fig).__module__).startswith('bokeh'):
            print("BACKEND: Bokeh")
            from bokeh.plotting import show 
            show(fig)  # Show Bokeh figure in browser
        else:
            print("BACKEND: Matplotlib")
            # Save matplotlib figure to HTML and open in browser
            import mpld3
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
        "--visualize",
        # choices=["none", "simple", "country-source", "source-country"],
        default="none",
        help="Type of visualization to generate",
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


if __name__ == "__main__":
    main()

# Example usage:
# python src\main.py --start_date 2015-01-01 --end_date 2015-12-31 --visualization simple
