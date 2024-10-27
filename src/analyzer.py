import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict
from config import SOURCE_COLORS, COUNTRY_COLORS, PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe

class ElectricityMixAnalyzer:
    def __init__(self):
        # Visualization settings
        self.cmap = plt.get_cmap('tab20')
        self.country_colors = COUNTRY_COLORS
        self.source_colors = SOURCE_COLORS

    def analyze_and_visualize(self, pt_data: dict, es_data: dict, viz_type: str = 'simple') -> None:
        """Main method to analyze data and create visualization"""
        results = self._calculate_mix(pt_data, es_data)
        
        if results.empty:
            print("No data to visualize")
            return
            
        if viz_type == 'simple':
            self._plot_simple_pie(results)
        elif viz_type == 'detailed':
            self._plot_source_country_pie(results)
        elif viz_type == 'nested':
            self._plot_nested_pie(results)
        else:
            print(f"Unsupported visualization type: {viz_type}")


    def _calculate_mix(self, pt_data: dict, es_data: dict) -> pd.DataFrame:
        pt_gen = pt_data.get('generation', pd.DataFrame())
        pt_imports = pt_data.get('imports', pd.DataFrame())
        pt_exports = pt_data.get('exports', pd.DataFrame())
        es_gen = es_data.get('generation', pd.DataFrame())

        if pt_gen.empty and es_gen.empty:
            print("Both Portuguese and Spanish generation data are empty")
            return pd.DataFrame()

        self._ensure_datetime_format([pt_gen, pt_imports, pt_exports, es_gen])

        pt_gen_grouped = self._group_generation_data(pt_gen)
        es_gen_grouped = self._group_generation_data(es_gen)

        net_imports = self._calculate_net_imports(pt_imports, pt_exports)

        es_percentages = self._calculate_percentages(es_gen_grouped)

        pt_mix = self._adjust_portugal_mix(pt_gen_grouped, net_imports, es_percentages)

        pt_percentages = self._calculate_percentages(pt_mix)

        result = self._clean_output(pt_percentages)

        return result

    def _ensure_datetime_format(self, dataframes):
        for df in dataframes:
            if not df.empty:
                if 'start_time' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start_time'])
                elif 'start' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start'])
                    df = df.rename(columns={'start': 'start_time'})
                df['hour'] = df['start_time'].dt.floor('H')

    def _group_generation_data(self, df):
        if df.empty:
            return pd.DataFrame()
        
        # Add hour column if not present
        if 'hour' not in df.columns:
            df['hour'] = df['start_time'].dt.floor('H')
        
        # Check if data is already pivoted (B01, B02, etc. as columns)
        psr_columns = get_active_psr_in_dataframe(df)
        if psr_columns:
            # Data is already pivoted, just set index to hour and select PSR columns
            return df.set_index('hour')[psr_columns]
        
        # If not pivoted, use the original grouping logic (should not happen with new format)
        raise ValueError("Unexpected data format: PSR types should be pre-pivoted in the input DataFrame")


    def _calculate_net_imports(self, imports, exports):
        if imports.empty and exports.empty:
            return pd.Series(dtype=float)
        
        # Use 'Power' column instead of 'quantity'
        imports['hour'] = imports['start_time'].dt.floor('H')
        exports['hour'] = exports['start_time'].dt.floor('H')
        imports_grouped = imports.groupby('hour')['Power'].sum()
        exports_grouped = exports.groupby('hour')['Power'].sum()
        net_imports = imports_grouped.sub(exports_grouped, fill_value=0)
        return net_imports

    def _calculate_percentages(self, df):
        if df.empty:
            return pd.DataFrame()
        total = df.sum(axis=1)
        return df.div(total, axis=0) * 100

    def _adjust_portugal_mix(self, pt_mix, net_imports, es_percentages):
        adjusted_mix = pt_mix.copy()
        common_hours = adjusted_mix.index.intersection(net_imports.index).intersection(es_percentages.index)
        
        for source in es_percentages.columns:
            if source in adjusted_mix.columns:
                adjusted_mix.loc[common_hours, source] += net_imports.loc[common_hours] * es_percentages.loc[common_hours, source] / 100
            else:
                adjusted_mix.loc[common_hours, source] = net_imports.loc[common_hours] * es_percentages.loc[common_hours, source] / 100
        
        return adjusted_mix.fillna(0)  # Fill NaN values with 0

    def _clean_output(self, df):
        df[df < 0] = 0
        row_sums = df.sum(axis=1)
        df = df.div(row_sums, axis=0).fillna(0) * 100
        df = df.round(6)  # Round to 6 decimal places
        df = df.div(df.sum(axis=1), axis=0).fillna(0) * 100  # Normalize again to ensure sum is exactly 100
        df = df[df.sum(axis=1) > 0]  # Remove rows where sum is 0
        df.index.name = None
        df.columns.name = None
        return df

    def _plot_simple_pie(self, df: pd.DataFrame) -> None:
        plt.figure(figsize=(10, 8))
        
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
        plt.title("Electricity Mix by Source Type")
        plt.axis('equal')
        plt.tight_layout()
        plt.show()

    def _aggregate_by_source_type(self, df: pd.DataFrame) -> pd.Series:
        """Aggregate data by source type only."""
        # Remove columns where all values are 0
        df = df.loc[:, (df != 0).any()]
        # Fill any NaN values with 0
        df = df.fillna(0)
        
        # Group by source type (in case multiple B-codes map to same source)
        grouped_data = df.mean()
        
        return grouped_data

    def _plot_source_country_pie(self, df: pd.DataFrame) -> None:
        plt.figure(figsize=(12, 10))
        
        # Clean and prepare data
        df = df.loc[:, (df != 0).any()]
        df = df.fillna(0)
        
        # Prepare data for plotting
        labels = []
        sizes = []
        colors = []
        
        for country in ['Portugal', 'Spain']:
            country_prefix = f"{country[:2]}_"
            country_columns = [col for col in df.columns if col.startswith(country_prefix)]
            
            for col in country_columns:
                source = col[3:]  # Remove country prefix
                value = df[col].mean()
                if value > 0:  # Only include non-zero values
                    labels.append(f"{country}\n{source}")
                    sizes.append(value)
                    colors.append(self.source_colors.get(source, self.source_colors['Other']))

        if not sizes:
            print("No non-zero data to plot")
            return
            
        plt.pie(sizes, labels=labels, colors=colors, 
                autopct='%1.1f%%', textprops={'fontsize': 8})
        plt.title("Electricity Mix by Source Type and Country")
        plt.axis('equal')
        plt.tight_layout()
        plt.show()

    def _plot_nested_pie(self, df: pd.DataFrame) -> None:
        plt.figure(figsize=(14, 12))
        
        # Clean and prepare data
        df = df.loc[:, (df != 0).any()]
        df = df.fillna(0)
        
        # Prepare outer ring (countries)
        pt_data = df[[col for col in df.columns if col.startswith('PT_')]].mean()
        es_data = df[[col for col in df.columns if col.startswith('ES_')]].mean()
        country_sizes = [pt_data.sum(), es_data.sum()]
                
        if sum(country_sizes) == 0:
            print("No non-zero data to plot")
            return
            
        country_colors = [self.country_colors[country] for country in ['Portugal', 'Spain']]
        
        # Prepare inner ring (sources)
        source_sizes = []
        source_colors = []
        source_labels = []
        
        for country_data, country in zip([pt_data, es_data], ['Portugal', 'Spain']):
            if not country_data.empty:
                for source, value in country_data.items():
                    if value > 0:  # Only include non-zero values
                        source_sizes.append(value)
                        source_colors.append(self.source_colors.get(source[3:], self.source_colors['Other']))
                        source_labels.append(f"{country}\n{source[3:]}")

        # Plot outer ring (countries)
        plt.pie(country_sizes, colors=country_colors, radius=1.3,
               labels=['Portugal', 'Spain'], autopct='%1.1f%%', 
               textprops={'fontsize': 10})
        
        # Plot inner ring (sources)
        if source_sizes:
            plt.pie(source_sizes, colors=source_colors, radius=1.0,
                   labels=source_labels, autopct='%1.1f%%', 
                   textprops={'fontsize': 8})
        
        plt.title("Electricity Mix by Country and Source Type")
        plt.axis('equal')
        plt.tight_layout()
        plt.show()
