# Electricity Consumption Share Calculator for Portugal

## Objective
Create a program that calculates the electricity consumption share per source for Portugal, taking into account both domestic generation and imports/exports with Spain.

## Data Sources
1. ENTSO-E website (or API) for:
   - Electricity generation per source for Portugal
   - Electricity generation per source for Spain
   - Import/export data between Portugal and Spain

## Calculation Method
The program should implement the following logic:

1. If Portugal is importing electricity:
   - Retrieve national electricity generation per source for Portugal
   - Retrieve total imported electricity amount from Spain
   - Retrieve electricity generation per source for Spain
   - For each source type (solar, wind, etc.):
     - Calculate: Portuguese generation + (total import * fraction of that source in Spain's generation mix)
   - Sum all sources to get total consumption
   - Calculate the percentage share for each source

2. If Portugal is exporting electricity:
   - Use Portugal's generation share as the consumption share

## Additional Considerations
- Handle time granularity (e.g., hourly or daily calculations)
- Account for simultaneous import and export (use net values)
- Consider incorporating transmission losses if data is available

## Desired Output
- A data structure (e.g., dictionary or DataFrame) showing the consumption share percentages for each electricity source in Portugal
- Option to output results for a specific time period or generate a time series

## Programming Language
Python is preferred, but you can suggest an alternative if you think it's more suitable.

## Additional Requirements
- Include error handling for missing or inconsistent data
- Provide clear comments and documentation in the code
- Include a brief explanation of any assumptions made in the calculations

Please implement this program, explaining your approach and any key decisions made during the coding process.
