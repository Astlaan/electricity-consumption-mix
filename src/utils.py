from datetime import datetime
import pandas as pd

PSR_TYPE_MAPPING = {
    'B01': 'Biomass',
    'B02': 'Fossil Brown coal/Lignite',
    'B03': 'Fossil Coal-derived gas',
    'B04': 'Fossil Gas',
    'B05': 'Fossil Hard coal',
    'B06': 'Fossil Oil',
    'B07': 'Fossil Oil shale',
    'B08': 'Fossil Peat',
    'B09': 'Geothermal',
    'B10': 'Hydro Pumped Storage',
    'B11': 'Hydro Run-of-river and poundage',
    'B12': 'Hydro Water Reservoir',
    'B13': 'Marine',
    'B14': 'Nuclear',
    'B15': 'Other renewable',
    'B16': 'Solar',
    'B17': 'Waste',
    'B18': 'Wind Offshore',
    'B19': 'Wind Onshore',
    'B20': 'Other',
}

def validate_inputs(args):
    try:
        start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
        if start_date >= end_date:
            print("Error: Start date must be before end date.")
            return False
        return True
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD.")
        return False

def aggregate_results(results, granularity):
    if granularity == 'hourly':
        aggregated = results
    elif granularity == 'daily':
        aggregated = results.resample('D').mean()
    elif granularity == 'weekly':
        aggregated = results.resample('W').mean()
    elif granularity == 'monthly':
        aggregated = results.resample('M').mean()
    else:
        raise ValueError(f"Invalid granularity: {granularity}")
    
    aggregated.columns = [PSR_TYPE_MAPPING.get(col, col) for col in aggregated.columns]
    return aggregated
