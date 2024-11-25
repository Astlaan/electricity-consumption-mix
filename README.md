## Important note
1) Right now the data-fetcher is not capable of pulling data older than what it has cached, only more recent data.
This is fine for now since the goal is to initialize the cache (with `main.py --initialize-cache`) with the entirety of past data when it is plugged into the website.


## To-Do Fixes:
- Data is provided in MW. I have to calculate by the granularity in order to obtain MWh
- Give proper error message if user tries to provide interval for which there is no data

- There may be gaps in the data, due to information outages. How to deal with these?
- Will the mean work well if there are gaps in the data? Ex. in one of the hours, only 3 blocks exist due to data outage? (Have to check if production zero of a source is represented in the data by an absense or a zero)
- I may be forcing a conversion from NaN to 0 somewhere, check if it is sensible.
- Actual Consumption from the energy sources themselves is not being considered. Take a look at how big they are and if they really should be included 


- Try ENTSOE-py package
- Hydro Pumped Storage: how to deal with this source? (has both consumption and production)
    - Simply ignore, and only consider real energy production?
- How to deal with data gaps? (NaN)
  - Some sources don't appear at all in the data (ex. no Coal columns for Portugal)
  - Some appear but are NaN always (Offshore Wind in Portugal and Spain)
  - Some appear but are 0 most of the time
  - Sometimes whole hours have no data at all for all sources
  - df.ffill?

- Put data-cache in blob instead of root/.data_cache. Use an environment variable to specify the alternate location (ex. blob) of data cache
- How will the asynchronous read/writes on the blob work? Will it be a problem?

- Meter warning se cache não detetada
- Change to pipfile

- Charting: Select and use custom colors ( https://plotly.com/python/discrete-color/ )

- Check code TODOs

- Check why 2015-2024 Portugal consumption has more wind than hydro

## To-Do Features:
- Charting:
  - Chart with the sources aggregated by type, regardless of the country of origin (Done)
  - Chart with the sources grouped (not aggregated by type), and Country of origin is specified for each sub-slice
  - Chart with the sources group by country, and each subslice represents a type of source
- Allow the user to specify multiple intervals (eg, 1T from years 2024, 2023, 2022..., 17h-23h daily yearly, or by trimester, etc)
- Chart the Carbon/Carbon Intensity pie graph
- Use preset colors for each source (both Aggregated plot and Hierarchical)

## Possible future features:
- Sankey/Treemap diagrams
