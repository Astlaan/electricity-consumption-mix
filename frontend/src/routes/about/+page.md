# About

This website allows visualizing Portugal's electricity consumption patterns, taking into account both domestic generation and international exchanges.

## Why?
The Portuguese electrical grid operator, [REN](https://ren.pt/), makes available some of the Portuguese electricity consumption data via its [REN Data Hub](https://datahub.ren.pt/) page. This website aims to provide some functionality that the REN Data Hub doesn't provide:

1. **Imports discriminated by source.** In the REN Data Hub, imported electricity is displayed in an aggregated fashion, which does not allow users to know the true consumption by source of electricity. Access to this information became increasingly important in recent years, due to the increasing reliance of Portugal on imported electricity, which at times constitutes >40% of the consumed amount. This is furthermore of interest in order to analyze the carbon intensity of domestic consumption when accounting for imports.

2. **Ability to select custom/complex time intervals.** Currently, the REN Data Hub only allows the selection of specific days or specific months for which to inspect data. It does not allow the selection of other custom intervals. Selecting these can be useful to inspect how the electricity mix varies in specific contexts, like Winter or Summer (of potentially across multiple years), at nighttime (e.g. 8pm–6am), Winter nighttime, etc.

This website does not aim to replicate all the functionality that REN Data Hub or even others like [Electricity Maps](https://app.electricitymaps.com/) (which is quite nice) already provide. Rather, it is meant to provide *some* of the functionality they don't provide, such as the above referred discriminated imports and custom/complex intervals.

This is a personal project made in order to obtain some perspectives that are important in order to evaluate the current electrical system policy in Portugal. 

## Methodology

### Data Source
The data is sourced from ENTSO-E, the European Network of Transmission System Operators for Electricity. This website has access to all the data since 15/01/2015 (roughly the legal start of the ENTSO-E data collection program), and is capable of fetching all the data till the present time minus ~2 hours, by making use of the ENTSO-E API.


#### Approximations:

In order to tackle this problem, some approximations were made:

1. **The generated power is assumed to be distributed homogeneously throughout the grid, per country**. For example: taking Spain in isolation, we make the assumption that the mix of electricity provided in any location in the country simply corresponds to the overall mix for the country.

   a. **Corollary:** The source mix of a cross-border export is the same as the mix of electricity in the grid of the exporting country. This assumption follows directly from the assumption above.
   
   b. This assumption greatly simplifies the problem, which would otherwise require taking the topology of the grid into account (and data that is likely not available). Such a project would be of a whole other scope. 


2. **Cross-border flows are assumed to be acyclic.** If there is, for a given border (eg. Spain-France), at any point in time, non-zero flows in both directions, then the exports are assumed not to interfere with the imports. I.e. if Spain is both importing and exporting from/to France at a given time, then the mix of the France $\to$ Spain flow is assumed to have the same distribution as France's generation. As such, we are discarding any "loop" effects, of flows that enter a country and go back to the country of origin due to subpar transmission infrastructure in that country. This is the case, for example, with Germany, where often electricity is transmitted between the southern and northern regions via a detour through France/Belgium/Netherlands, due to the relatively weak north-south domestic transmission axis.
   a. This is in general a reasonable approximation to do in the case of the Portugal-Spain flows due to the good domestic transmission networks of both countries. In fact, for each border, flows in only one of the directions were observed for the hourly data on record. For the PT-ES and ES-FR data, simultaneous flows in both directions were observed in only 2.2% and 1.6% of the hourly data points, respectively.
   b.  However, Spain $\to$ Portugal flows will consider a recalculated Spanish grid mix that takes the France$\to$Spain flows into account.

3. **Only the contributions of Portugal's, Spain's and France's generation were considered.**
   a. Portugal's electricity imports are sizeable. In 2023, around 23% of the electricity was imported. However, in this case, the french contribution represented only 0.5% of the supply. Even in times of extreme imports, like some time periods of 21/11/2024 when total imports reached a staggering 48% of consumption, the French contribution was responsible for &lt;5% of the supply. As such, the approximation should have a small impact.  

4. **Resampling of Spanish/French generation/cross-border flow data to hourly granularity**, from their original 15 minutes granularity. The need to resample follows from the different Market Time Unit (MTU), which define the granularity of data. The MTU is of 1 hour for Portugal, and 15 minutes for Spain and France. The downsampling of Spain/French data was performed by doing a mean aggregation of each hour's four 15 minutes blocks.

### Model and calculation

From the ENTSO-E API it is possible to request data and process it into the following variables:

- $G_{t,s}^{X}$: the generation matrix for country $X$. The lines $t$ represent the time (each hour) and the columns $s$ represent the sources. 
- $F_t^{A \to B}$: A vector representing the (non-netted) cross-border total flows from country A to country B. This vector contains one element for each hour being considered.

We retrieve the generation matrices for Portugal, Spain and France, and the flow vectors for Portugal-Spain and Spain-France (in both direction for each case).

Based on the data above, and on the approximations described in the previous section, we devised a simple model where, for each country:

1. The relative weight of each source for each hourly timestamp is calculated by $\frac{G_{t,s}^{X}}{\sum_{s} G_{t,s}^{X}}$ (for each country X). 
2. The exports per source are calculated by applying the relative weights to the total exports, e.g. $F_{t}^{FR \to ES}\frac{G_{t,s}^{FR}}{\sum_{s} G_{t,s}^{FR}}$ in the case of the exports from France to Spain.
3. The imports per source are calculated in a similar fashion, e.g. $F_{t}^{ES \to FR}\frac{G_{t,s}^{ES}}{\sum_{s} G_{t,s}^{ES}}$ in the case of imports from Spain to France.
3. The effective source mix on the grid is calculated by subtracting the exports (per source and time) from the country's generation, and the imports are added.

We start by calculating the above for the Spain-France pair, in order to calculate the intermediary grid mix for Spain, $G_{t,s}^{ES'}$ (notice the prime symbol '). We calculate the interactions for Portugal-Spain using that intermediary spanish grid mix. These two steps are represented in the expressions below:

$$
G_{t,s}^{ES'} = G_{t,s}^{ES} - F_{t}^{ES \to FR}\frac{G_{t,s}^{ES}}{\sum_{s} G_{t,s}^{ES}} + F_{t}^{FR \to ES}\frac{G_{t,s}^{FR}}{\sum_{s} G_{t,s}^{FR}}
$$

$$
C_{t,s}^{PT} = G_{t,s}^{PT} - F_{t}^{PT \to ES}\frac{G_{t,s}^{PT}}{\sum_{s} G_{t,s}^{PT}} + F_{t}^{ES \to PT}\frac{G_{t,s}^{ES'}}{\sum_{s} G_{t,s}^{ES'}}
$$

Where $C_{t,s}^{PT}$ is the resulting Portuguese electricity aggregated consumption matrix, indexed by time (hourly) and source. Merging these two expressions, and factorizing the numerator generation terms we get:

$$
\begin{aligned}
C_{t,s}^{PT} &= \left( 1 - \frac{F_{t}^{PT \to ES}}{\sum_{s} G_{t,s}^{PT}} \right) G_{t,s}^{PT} & \text{(Portuguese Contribution)} \newline
   &+ \frac{F_{t}^{ES \to PT} \left( 1 - \frac{F_{t}^{ES \to FR}}{\sum_{s} G_{t,s}^{ES}} \right)}{\sum_{s} G_{t,s}^{ES} - F_{t}^{ES \to FR} + F_{t}^{FR \to ES}} G_{t,s}^{ES} & \text{(Spanish Contribution)} \newline
   &+ \frac{F_{t}^{ES \to PT} \cdot \frac{F_{t}^{FR \to ES}}{\sum_{s} G_{t,s}^{FR}}}{\sum_{s} G_{t,s}^{ES} - F_{t}^{ES \to FR} + F_{t}^{FR \to ES}} G_{t,s}^{FR} & \text{(French Contribution)}
\end{aligned}
$$

We can then use the whole expression to plot the aggregated electricity consumption mix in Portugal accounting for the exports, or we can use each of the terms in order to plot the Portuguese electricity consumption mix with the discriminated generation contributions from each of the countries. 


## Features

1. **Time intervals definition**:

   a. **Simple Interval Mode**: Select a simple time range for which to retrieve data and analyze.
   
   b. **Advanced Pattern Mode**: Allows specifying custom intervals, by applying constrains to data, to the years, months, days and hours fields.

2. **Plot Types**:

   a. **Aggregated**: Shows the overall consumption mix for Portugal, with the contributions by different countries all aggregated and grouped by source.
   
   b. **Discriminated**: Displays the consumption mix grouped by country, and then by source. 


## Notes

- **Hydro Pumped Storage consumption is not accounted for**. For now, only source generation values are represented. This means that, while Hydro Pumped Storage generation is accounted into the graph, the consumption value relative to the upstream pumping of water ("charging the reservoir") is not represented.

- **Missing data handling:** there are some hour timestamps where no data was registered, for some 
sources. Missing data is estimated via linear interpolation.


## Authors

- Diogo Valada (Owner): [LinkedIn](https://www.linkedin.com/in/diogovalada/)
