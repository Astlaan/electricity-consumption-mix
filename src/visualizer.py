import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Optional

class ElectricityMixVisualizer:
    def __init__(self):
        # Define color schemes for different source types
        self.source_colors = {
            'Solar': '#FFD700',
            'Wind': '#87CEEB',
            'Hydro': '#4169E1',
            'Nuclear': '#FF69B4',
            'Fossil Gas': '#808080',
            'Biomass': '#228B22',
            'Geothermal': '#8B4513',
            'Other': '#A9A9A9'
        }
        
        # Define country colors for multi-level charts
        self.country_colors = {
            'Portugal': '#006600',  # Dark green
            'Spain': '#FF0000'      # Red
        }

    def _aggregate_by_source_type(self, df: pd.DataFrame) -> pd.Series:
        """Aggregate data by source type only."""
        return df.mean()  # Using mean for the time period

    def _split_by_country_and_source(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Split data into Portuguese and Spanish sources."""
        # This will need logic to identify which columns are from which country
        # based on the data structure from the calculator
        pt_sources = {}
        es_sources = {}
        
        for col in df.columns:
            if 'PT_' in col:
                pt_sources[col.replace('PT_', '')] = df[col].mean()
            elif 'ES_' in col:
                es_sources[col.replace('ES_', '')] = df[col].mean()
                
        return {'Portugal': pd.Series(pt_sources), 'Spain': pd.Series(es_sources)}

    def plot_simple_pie(self, df: pd.DataFrame, title: str = "Electricity Mix by Source Type",
                       figsize: tuple = (10, 8)) -> None:
        """Plot type 1: Simple pie chart aggregated by source type."""
        plt.figure(figsize=figsize)
        
        data = self._aggregate_by_source_type(df)
        colors = [self.source_colors.get(source, '#A9A9A9') for source in data.index]
        
        plt.pie(data, labels=data.index, colors=colors, autopct='%1.1f%%')
        plt.title(title)
        plt.axis('equal')
        plt.show()

    def plot_source_country_pie(self, df: pd.DataFrame, 
                              title: str = "Electricity Mix by Source Type and Country",
                              figsize: tuple = (12, 10)) -> None:
        """Plot type 2: Pie chart with source types split by country."""
        plt.figure(figsize=figsize)
        
        data_dict = self._split_by_country_and_source(df)
        
        # Prepare data for plotting
        labels = []
        sizes = []
        colors = []
        
        for country in ['Portugal', 'Spain']:
            country_data = data_dict[country]
            for source, value in country_data.items():
                labels.append(f"{country}\n{source}")
                sizes.append(value)
                base_color = self.source_colors.get(source, '#A9A9A9')
                # Adjust color based on country
                if country == 'Spain':
                    # Make Spanish sources slightly lighter
                    rgb = plt.matplotlib.colors.to_rgb(base_color)
                    color = tuple(min(1.0, c * 1.3) for c in rgb)
                else:
                    color = base_color
                colors.append(color)

        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.title(title)
        plt.axis('equal')
        plt.show()

    def plot_nested_pie(self, df: pd.DataFrame,
                       title: str = "Electricity Mix by Country and Source Type",
                       figsize: tuple = (14, 12)) -> None:
        """Plot type 3: Nested pie chart with country as outer ring and sources as inner ring."""
        plt.figure(figsize=figsize)
        
        data_dict = self._split_by_country_and_source(df)
        
        # Prepare outer ring (countries)
        country_sizes = [sum(data_dict[country]) for country in ['Portugal', 'Spain']]
        country_colors = [self.country_colors[country] for country in ['Portugal', 'Spain']]
        
        # Prepare inner ring (sources)
        source_sizes = []
        source_colors = []
        source_labels = []
        
        for country in ['Portugal', 'Spain']:
            for source, value in data_dict[country].items():
                source_sizes.append(value)
                source_colors.append(self.source_colors.get(source, '#A9A9A9'))
                source_labels.append(f"{country}\n{source}")

        # Plot outer ring (countries)
        plt.pie(country_sizes, colors=country_colors, radius=1.3,
               labels=['Portugal', 'Spain'], autopct='%1.1f%%')
        
        # Plot inner ring (sources)
        plt.pie(source_sizes, colors=source_colors, radius=1.0,
               labels=source_labels, autopct='%1.1f%%')
        
        plt.title(title)
        plt.axis('equal')
        plt.show()
