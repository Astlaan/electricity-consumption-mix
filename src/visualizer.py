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
            'Other': '#A9A9A9',
            'unknown': '#A9A9A9' #Added to handle unknown source types gracefully
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
        pt_sources = {}
        es_sources = {}
        
        for col in df.columns:
            if col.startswith('PT_'):
                pt_sources[col[3:]] = df[col].mean()
            elif col.startswith('ES_'):
                es_sources[col[3:]] = df[col].mean()
                
        return {'Portugal': pd.Series(pt_sources), 'Spain': pd.Series(es_sources)}

    def plot_simple_pie(self, df: pd.DataFrame, title: str = "Electricity Mix by Source Type",
                       figsize: tuple = (10, 8)) -> None:
        """Plot type 1: Simple pie chart aggregated by source type."""
        plt.figure(figsize=figsize)
        
        data = self._aggregate_by_source_type(df)
        colors = [self.source_colors.get(source, self.source_colors['unknown']) for source in data.index]
        
        plt.pie(data, labels=data.index, colors=colors, autopct='%1.1f%%', textprops={'fontsize': 8}) #Improved text size
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout() # Prevents labels from overlapping
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
                base_color = self.source_colors.get(source, self.source_colors['unknown'])
                colors.append(base_color)

        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', textprops={'fontsize': 8}) #Improved text size
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout() # Prevents labels from overlapping
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
                source_colors.append(self.source_colors.get(source, self.source_colors['unknown']))
                source_labels.append(f"{country}\n{source}")

        # Plot outer ring (countries)
        plt.pie(country_sizes, colors=country_colors, radius=1.3,
               labels=['Portugal', 'Spain'], autopct='%1.1f%%', textprops={'fontsize': 10}) #Improved text size
        
        # Plot inner ring (sources)
        plt.pie(source_sizes, colors=source_colors, radius=1.0,
               labels=source_labels, autopct='%1.1f%%', textprops={'fontsize': 8}) #Improved text size
        
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout() # Prevents labels from overlapping
        plt.show()
