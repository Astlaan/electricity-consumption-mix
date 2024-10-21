## To-Do:
- Data is provided in MW. I have to calculate by the granularity in order to obtain MWh
- Give proper error message if user tries to provide interval for which there is no data
- Allow the user to specify multiple intervals (eg, 1T from years 2024, 2023, 2022...)
- The datafetcher tests should rely on the async functions, now that the others are deleted

## Notes:
- Currently, cross-border physical flows are being accounted for in a net way. It appears that often, net flow matches the physical flows. However, this could be improved in the future to account for the actual physical flows.