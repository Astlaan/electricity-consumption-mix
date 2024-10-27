import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict, Optional

class ElectricityMixVisualizer:
    def __init__(self):
        self.cmap = plt.get_cmap('tab20')  # Using tab20 colormap which provides 20 distinct colors
        
        # Define country colors for multi-level charts
        self.country_colors = {
            'Portugal': '#006600',  # Dark green
            'Spain': '#FF0000'      # Red
        }

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns with all zeros and handle NaN values."""
        # Remove columns where all values are 0
        df = df.loc[:, (df != 0).any()]
        # Fill any NaN values with 0
        df = df.fillna(0)
        return df

    def _aggregate_by_source_type(self, df: pd.DataFrame) -> pd.Series:
        """Aggregate data by source type only."""
        df = self._clean_data(df)
        
        # Create a mapping from B-codes to source types
        from utils import PSR_TYPE_MAPPING
        
        # Rename columns from B-codes to source types
        renamed_data = df.rename(columns=PSR_TYPE_MAPPING)
        
        # Group by source type (in case multiple B-codes map to same source)
        grouped_data = renamed_data.mean()
        
        return grouped_data

    def _split_by_country_and_source(self, df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Split data into Portuguese and Spanish sources."""
        df = self._clean_data(df)
        pt_sources = {}
        es_sources = {}
        
        for col in df.columns:
            if col.startswith('PT_'):
                source = col[3:]
                if df[col].mean() > 0:  # Only include non-zero sources
                    pt_sources[source] = df[col].mean()
            elif col.startswith('ES_'):
                source = col[3:]
                if df[col].mean() > 0:  # Only include non-zero sources
                    es_sources[source] = df[col].mean()
                
        return {'Portugal': pd.Series(pt_sources), 'Spain': pd.Series(es_sources)}

    def plot_simple_pie(self, df: pd.DataFrame, title: str = "Electricity Mix by Source Type",
                       figsize: tuple = (10, 8)) -> None:
        """Plot type 1: Simple pie chart aggregated by source type."""
        plt.figure(figsize=figsize)
        
        data = self._aggregate_by_source_type(df)
        
        # Only plot non-zero values
        mask = data > 0
        data = data[mask]
        
        if data.empty:
            print("No non-zero data to plot")
            return
            
        # Get colors from colormap
        colors = self.cmap(np.linspace(0, 1, len(data)))
        
        plt.pie(data, labels=data.index, colors=colors, 
                autopct='%1.1f%%', textprops={'fontsize': 8})
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout()
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
            if not country_data.empty:
                for source, value in country_data.items():
                    if value > 0:  # Only include non-zero values
                        labels.append(f"{country}\n{source}")
                        sizes.append(value)
                        base_color = self.source_colors.get(source, self.source_colors['unknown'])
                        colors.append(base_color)

        if not sizes:
            print("No non-zero data to plot")
            return
            
        plt.pie(sizes, labels=labels, colors=colors, 
                autopct='%1.1f%%', textprops={'fontsize': 8})
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout()
        plt.show()

    def plot_nested_pie(self, df: pd.DataFrame,
                       title: str = "Electricity Mix by Country and Source Type",
                       figsize: tuple = (14, 12)) -> None:
        """Plot type 3: Nested pie chart with country as outer ring and sources as inner ring."""
        plt.figure(figsize=figsize)
        
        data_dict = self._split_by_country_and_source(df)
        
        # Prepare outer ring (countries)
        country_sizes = []
        for country in ['Portugal', 'Spain']:
            country_data = data_dict[country]
            if not country_data.empty:
                country_sizes.append(country_data.sum())
            else:
                country_sizes.append(0)
                
        if sum(country_sizes) == 0:
            print("No non-zero data to plot")
            return
            
        country_colors = [self.country_colors[country] for country in ['Portugal', 'Spain']]
        
        # Prepare inner ring (sources)
        source_sizes = []
        source_colors = []
        source_labels = []
        
        for country in ['Portugal', 'Spain']:
            country_data = data_dict[country]
            if not country_data.empty:
                for source, value in country_data.items():
                    if value > 0:  # Only include non-zero values
                        source_sizes.append(value)
                        source_colors.append(self.source_colors.get(source, self.source_colors['unknown']))
                        source_labels.append(f"{country}\n{source}")

        # Plot outer ring (countries)
        plt.pie(country_sizes, colors=country_colors, radius=1.3,
               labels=['Portugal', 'Spain'], autopct='%1.1f%%', 
               textprops={'fontsize': 10})
        
        # Plot inner ring (sources)
        if source_sizes:
            plt.pie(source_sizes, colors=source_colors, radius=1.0,
                   labels=source_labels, autopct='%1.1f%%', 
                   textprops={'fontsize': 8})
        
        plt.title(title)
        plt.axis('equal')
        plt.tight_layout()
        plt.show()
