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
    if args.start_date >= args.end_date:
        print("Error: Start date must be before end date.")
        return False
    return True

def aggregate_results(results: pd.DataFrame, granularity: str) -> pd.DataFrame:
    if results.empty:
        return pd.DataFrame(columns=list(PSR_TYPE_MAPPING.values()))
    
    # Map PSR types to their descriptions
    results = results.rename(columns=PSR_TYPE_MAPPING)
    
    if granularity == 'hourly':
        return results
    elif granularity in ['daily', 'weekly', 'monthly']:
        return results.resample(granularity[0].upper()).mean()
    else:
        raise ValueError(f"Invalid granularity: {granularity}")
