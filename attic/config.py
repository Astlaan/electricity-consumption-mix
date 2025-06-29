# src/config.py
try:
    from plotly.colors import qualitative

    Set3 = qualitative.Set3
except ImportError:
    from bokeh.palettes import Set3_12 as Set3

PSR_TYPE_MAPPING = {
    "B01": "Biomass",
    "B02": "Fossil Brown coal/Lignite",
    "B03": "Fossil Coal-derived gas",
    "B04": "Fossil Gas",
    "B05": "Fossil Hard coal",
    "B06": "Fossil Oil",
    "B07": "Fossil Oil shale",
    "B08": "Fossil Peat",
    "B09": "Geothermal",
    "B10": "Hydro Pumped Storage",
    "B11": "Hydro Run-of-river and poundage",
    "B12": "Hydro Water Reservoir",
    "B13": "Marine",
    "B14": "Nuclear",
    "B15": "Other renewable",
    "B16": "Solar",
    "B17": "Waste",
    "B18": "Wind Offshore",
    "B19": "Wind Onshore",
    "B20": "Other",
}

# Visualization settings
COUNTRY_COLORS = {"Portugal": "#006600", "Spain": "#FF0000"}

PSR_COLORS = {
    "Biomass": Set3[1],  # #ffffb3 - Light yellow (for biomass's organic nature)
    "Fossil Brown coal/Lignite": Set3[7],  # #fccde5 - Pink (closest to brown)
    "Fossil Coal-derived gas": Set3[
        6
    ],  # #b3de69 - Light green (as an alternative to red-brown)
    "Fossil Gas": Set3[3],  # #fb8072 - Salmon (for gas)
    "Fossil Hard coal": Set3[8],  # #d9d9d9 - Light grey (for coal-like color)
    "Fossil Oil": Set3[11],  # #ffed6f - Yellow (closest to black for oil)
    "Fossil Oil shale": Set3[9],  # #bc80bd - Purple (as an alternative shade)
    "Fossil Peat": Set3[7],  # #fccde5 - Pink (similar to Biomass for thematic link)
    "Geothermal": Set3[5],  # #fdb462 - Orange (for geothermal heat)
    "Hydro Pumped Storage": Set3[0],  # #8dd3c7 - Pale green-blue (for water storage)
    "Hydro Run-of-river and poundage": Set3[
        4
    ],  # #80b1d3 - Light blue (for flowing water)
    "Hydro Water Reservoir": Set3[
        0
    ],  # #8dd3c7 - Pale green-blue (same as Pumped Storage)
    "Marine": Set3[0],  # #8dd3c7 - Pale green-blue (for marine environments)
    "Nuclear": Set3[7],  # #fb8072 - Salmon (to indicate a unique source)
    "Other renewable": Set3[2],  # #bebada - Light purple (for other renewables)
    "Solar": Set3[1],  # #ffed6f - Bright yellow (for sunshine)
    "Waste": Set3[9],  # #bc80bd - Purple (indicating waste)
    "Wind Offshore": Set3[10],  # #ccebc5 - Very light green (for offshore wind)
    "Wind Onshore": Set3[6],  # #b3de69 - Light green (for onshore wind)
    "Other": Set3[8],  # #d9d9d9 - Light grey (for other unspecified sources)
}

# Set3 colors. Only 12 unfortunately.
# ['rgb(141,211,199)', 'rgb(255,255,179)', 'rgb(190,186,218)', 'rgb(251,128,114)', 'rgb(128,177,211)', 'rgb(253,180,98)', 'rgb(179,222,105)', 'rgb(252,205,229)', 'rgb(217,217,217)', 'rgb(188,128,189)', 'rgb(204,235,197)', 'rgb(255,237,111)']
