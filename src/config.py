# src/config.py

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

# Visualization settings
COUNTRY_COLORS = {
    'Portugal': '#006600',
    'Spain': '#FF0000'
}

SOURCE_COLORS = {
    'Biomass': '#8B4513',
    'Fossil Brown coal/Lignite': '#A0522D',
    'Fossil Coal-derived gas': '#A0522D',
    'Fossil Gas': '#8B4513',
    'Fossil Hard coal': '#A0522D',
    'Fossil Oil': '#8B0000',
    'Fossil Oil shale': '#8B0000',
    'Fossil Peat': '#8B4513',
    'Geothermal': '#800080',
    'Hydro Pumped Storage': '#000080',
    'Hydro Run-of-river and poundage': '#000080',
    'Hydro Water Reservoir': '#000080',
    'Marine': '#008080',
    'Nuclear': '#FF0000',
    'Other renewable': '#008000',
    'Solar': '#FFD700',
    'Waste': '#A0522D',
    'Wind Offshore': '#ADD8E6',
    'Wind Onshore': '#87CEEB',
    'Other': '#808080'  # Default gray for unknown sources
}
