# About Portugal Electricity Consumption Mix

This tool visualizes Portugal's electricity consumption patterns, taking into account both domestic generation and international exchanges.

## Why?
The Portuguese electrical grid operator, [REN](https://ren.pt/), makes available some of the Portuguese electricity consumption data via its [REN Data Hub](https://datahub.ren.pt/) page. This website aims to provide some functionality that the REN Data Hub doesn't provide:

1. **Imports discriminated by source.** In the REN Data Hub, imported electricity is displayed in an aggregated fashion, which does not allow users to know the true consumption by source of electricity. Access to this information became increasingly important in recent years, due to the increasing reliance of Portugal on imported electricity, which at times constitutes >40% of the consumed amount. This is furthermore of interest in order to analyze the carbon intensity of domestic consumption when accounting for imports.

2. **Ability to select custom/complex time intervals.** Currently, the REN Data Hub only allows the selection of specific days or specific months for which to inspect data. It does not allow the selection of other custom intervals. Selecting these can be useful to inspect how the electricity mix varies in specific contexts, like Winter or Summer (of potentially across multiple years), at nighttime (e.g. 8pm–6am), Winter nighttime, etc.

This website does not aim to replicate all the functionality that REN Data Hub or even others like [Electricity Maps](https://app.electricitymaps.com/) (which is quite nice) already provide. Rather, it is meant to provide *some* of the functionality they don't provide, such as the above referred discriminated imports and custom/complex intervals.

This is a personal project made in order to obtain some perspectives that are important in order to evaluate the current electrical system policy in Portugal. 

## Methodology

### Data Source
The data is sourced from ENTSO-E, the European Network of Transmission System Operators for Electricity. This website has access to all the data since 15/01/2015 (roughly the legal start of the ENTSO-E data collection program), and is capable of fetching all the data till the present time minus ~2 hours, by making use of the ENTSO-E API.


### Calculations



The consumption mix is calculated using the following formula:

In order to tackle this problem, some approximations were made:

#### Approximations:
1. **The generated power is assumed to be distributed homogeneously throughout the grid, per country**. For example: taking Spain in isolation, we make the assumption that the mix of electricity provided in any location in the country simply corresponds to the overall mix for the country.

   a. **Corollary:** The source mix of a cross-border export is the same as the mix of electricity in the grid of the exporting country. This assumption follows directly from the assumption above.
   b. This assumption greatly simplifies the problem, which would otherwise require taking the topology of the grid into account (and data that is likely not available). Such a project would be of a whole other scope. 


2. **Cross-border flows are assumed to be acyclic.** If there is, for a given border (eg. Spain-France), at any point in time, non-zero flows in both directions, then the exports are assumed not to interfere with the imports. I.e. if Spain is both importing and exporting from/to France at a given time, then the mix of the France $\to$ Spain flow is assumed to have the same distribution as France's generation. As such, we are discarding any "loop" effects, of flows that enter a country and go back to the country of origin due to subpar transmission infrastructure in that country. This is the case, for example, with Germany, where often electricity is transmitted between the southern and northern regions via a detour through France/Belgium/Netherlands, due to the relatively weak north-south domestic transmission axis.
   a. This is in general a reasonable approximation to do in the case of the Portugal-Spain flows due to the good domestic transmission networks of both countries. In fact, for each border, flows in only one of the directions were observed for the hourly data on record. For the PT-ES and ES-FR data, simultaneous flows in both directions were observed in only 2.2% and 1.6% of the hourly data points, respectively.
   b.  However, Spain $\to$ Portugal flows will consider a recalculated Spanish grid mix that takes the France$\to$Spain flows into account.

3. **Only the contributions of Portugal's, Spain's and France's generation were considered.**
   a. Portugal's electricity imports are sizeable. In 2023, around 23% of the electricity was imported. However, in this case, the french contribution represented only 0.5% of the supply. Even in times of extreme imports, like some time periods of 21-Nov-2024 when total imports reached a staggering 48% of consumption, the french contribution was responsible for <5% of the supply. As such, the approximation is deemed to be reasonable.  

4. **Resampling of Spanish/French generation/cross-border flow data to hourly granularity**, from their original 15 minutes granularity. The need to resample follows from the different `Market Time Unit`(MTU), which define the granularity of data. The MTU is of 1 hour for Portugal, and 15 minutes for Spain and France. The downsampling of Spain/French data was performed by doing a mean aggregation of each hour's four 15 minutes blocks.




$$
C^{PT} =
\begin{aligned}
    &\left( 1 - \frac{F_{t}^{PT \to ES}}{\sum_{s} G_{t,s}^{PT}} \right) G_{t,s}^{PT} \quad \text{(Portuguese Component)} \\
    &+ \frac{F_{t}^{ES \to PT} \left( 1 - \frac{F_{t}^{ES \to FR}}{\sum_{s} G_{t,s}^{ES}} \right)}{\sum_{s} G_{t,s}^{ES} - F_{t}^{ES \to FR} + F_{t}^{FR \to ES}} G_{t,s}^{ES} \quad \text{(Spanish Component)} \\
    &+ \frac{F_{t}^{ES \to PT} \cdot \frac{F_{t}^{FR \to ES}}{\sum_{s} G_{t,s}^{FR}}}{\sum_{s} G_{t,s}^{ES} - F_{t}^{ES \to FR} + F_{t}^{FR \to ES}} G_{t,s}^{FR} \quad \text{(French Component)}
\end{aligned}
$$

Where:
- $G_{t,s}^{PT}$, $G_{t,s}^{ES}$, $G_{t,s}^{FR}$ are the generation matrices for Portugal, Spain, and France, respectively. The lines $t$ represent the time (each hour) and the columns $s$ represent the sources. 
- $F_t^{A \to B}$ represents the (non-netted) cross-border total flows vector from country A to country B. This vector contains one element for each hour being considered. 

## Features

1. **Simple Interval Mode**: Select a specific time range to analyze
2. **Advanced Pattern Mode**: Analyze patterns across multiple years, months, days, or hours
3. **Plot Types**:
   - Simple Plot: Shows the overall consumption mix
   - Discriminate by Country: Separates domestic generation from international exchanges

## Time Patterns

### Simple Interval
Select a specific start and end date/time to analyze the consumption mix during that period. The tool enforces:
- Dates must be within available data range (2015-01-15 to present)
- Times must be on the hour (00 minutes)
- End date must be after start date

### Advanced Pattern
Analyze recurring patterns by specifying:
- Years: e.g., "2020-2023" or "2015, 2017, 2020-2023"
- Months: e.g., "1-3, 6, 9" (Jan-Mar, Jun, Sep)
- Days: e.g., "1-15, 20, 22-25"
- Hours: e.g., "20-23" (8PM-11PM UTC)

## Technical Details

The application uses:
- ENTSO-E API for data retrieval
- Python backend for data processing
- Plotly for interactive visualizations
