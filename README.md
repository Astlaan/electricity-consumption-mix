## To-Do:
- Data is provided in MW. I have to calculate by the granularity in order to obtain MWh
- Give proper error message if user tries to provide interval for which there is no data

- There may be gaps in the data, due to information outages. How to deal with these?
- Will the mean work well if there are gaps in the data? Ex. in one of the hours, only 3 blocks exist due to data outage? (Have to check if production zero of a source is represented in the data by an absense or a zero)

## To-Do Features:
- Charting:
  - Chart with the sources aggregated by type, regardless of the country of origin
  - Chart with the sources grouped (not aggregated by type), and Country of origin is specified for each sub-slice
  - Chart with the sources group by country, and each subslice represents a type of source
- Allow the user to specify multiple intervals (eg, 1T from years 2024, 2023, 2022..., 17h-23h daily yearly, or by trimester, etc)

## Notes:
- Currently, cross-border physical flows are being accounted for in a net way. It appears that often, net flow matches the physical flows. However, this could be improved in the future to account for the actual physical flows.