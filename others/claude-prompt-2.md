# Electricity Consumption Share Calculator for Portugal (Extended Version)

## Objective
Create a program that calculates the electricity consumption share per source for Portugal, taking into account domestic generation, imports/exports with Spain, and the impact of the Spanish-French interconnection.

## Data Sources
1. ENTSO-E website (or API) for:
   - Electricity generation per source for Portugal, Spain, and France
   - Import/export data between Portugal-Spain and Spain-France

## Calculation Method
The program should implement the following logic:

1. Calculate Spain's electricity mix:
   a. If Spain is importing from France:
      - Retrieve Spanish electricity generation per source
      - Retrieve total imported electricity amount from France
      - Retrieve French electricity generation per source
      - For each source type (solar, wind, etc.):
        - Calculate: Spanish generation + (French import * fraction of that source in France's generation mix)
      - Sum all sources to get total Spanish consumption
      - Calculate the percentage share for each source in Spain
   b. If Spain is exporting to France:
      - Use Spain's generation share as its consumption share

2. Calculate Portugal's electricity mix:
   a. If Portugal is importing from Spain:
      - Retrieve Portuguese electricity generation per source
      - Retrieve total imported electricity amount from Spain
      - For each source type:
        - Calculate: Portuguese generation + (Spanish import * fraction of that source in Spain's consumption mix from step 1)
      - Sum all sources to get total Portuguese consumption
      - Calculate the percentage share for each source in Portugal
   b. If Portugal is exporting to Spain:
      - Use Portugal's generation share as its consumption share

## Additional Considerations
- Handle time granularity (e.g., hourly or daily calculations)
- Account for simultaneous import and export (use net values) for both interconnections
- Consider incorporating transmission losses if data is available
- Ensure consistent handling of time zones across the three countries

## Desired Output
- A data structure (e.g., dictionary or DataFrame) showing the consumption share percentages for each electricity source in Portugal
- Option to output results for a specific time period or generate a time series
- Include intermediate results for Spain's adjusted mix for transparency

## Programming Language
Python is preferred, but you can suggest an alternative if you think it's more suitable.

## Additional Requirements
- Include error handling for missing or inconsistent data
- Provide clear comments and documentation in the code
- Include a brief explanation of any assumptions made in the calculations
- Implement the calculation as a multi-step process, allowing for verification of intermediate results (e.g., Spain's adjusted mix)

Please implement this program, explaining your approach and any key decisions made during the coding process. Also, provide suggestions for handling potential edge cases or data inconsistencies across the three countries.
