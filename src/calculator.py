import pandas as pd
import numpy as np
import logging

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data, es_data, fr_data, include_france):
        if include_france:
            es_adjusted, es_percentages = self._adjust_spain_mix(es_data, fr_data)
        else:
            es_adjusted = es_data['generation']
            es_total = es_adjusted.sum(axis=1)
            es_percentages = es_adjusted.div(es_total, axis=0) * 100

        pt_mix, pt_percentages = self._calculate_portugal_mix(pt_data, es_adjusted)
        
        return pt_percentages, es_percentages

    def _adjust_spain_mix(self, es_data, fr_data):
        es_gen = es_data['generation']
        fr_gen = fr_data['generation']
        es_imports_fr = es_data['imports_fr']
        es_exports_fr = es_data['exports_fr']
        
        # Calculate the fraction of each source in France's generation mix
        fr_total = fr_gen.groupby('start_time')['quantity'].sum()
        fr_fractions = fr_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack().div(fr_total, axis=0)
        
        # Adjust Spain's mix based on net imports from France
        es_adjusted = es_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack()
        net_imports_fr = es_imports_fr['quantity'] - es_exports_fr['quantity']
        
        for source in es_adjusted.columns:
            if net_imports_fr.sum() > 0:  # Spain is importing from France
                es_adjusted[source] += net_imports_fr * fr_fractions[source]
            else:  # Spain is exporting to France or net exchange is zero
                es_adjusted[source] += 0  # No adjustment needed
        
        # Calculate percentages
        es_total = es_adjusted.sum(axis=1)
        es_percentages = es_adjusted.div(es_total, axis=0) * 100
        
        return es_adjusted, es_percentages

    def _calculate_portugal_mix(self, pt_data, es_adjusted):
        pt_gen = pt_data['generation'].groupby(['start_time', 'psr_type'])['quantity'].sum().unstack()
        pt_imports = pt_data['imports'].groupby('start_time')['quantity'].sum()
        pt_exports = pt_data['exports'].groupby('start_time')['quantity'].sum()
        
        # Ensure all data is numeric
        pt_gen = pt_gen.apply(pd.to_numeric, errors='coerce')
        pt_imports = pd.to_numeric(pt_imports, errors='coerce')
        pt_exports = pd.to_numeric(pt_exports, errors='coerce')
        es_adjusted = es_adjusted.apply(pd.to_numeric, errors='coerce')
        
        # Calculate the fraction of each source in Spain's adjusted mix
        es_total = es_adjusted.sum(axis=1)
        es_fractions = es_adjusted.div(es_total, axis=0)
        
        # Calculate Portugal's mix
        pt_mix = pt_gen.copy()
        net_imports = pt_imports - pt_exports
        for source in pt_gen.columns:
            if source in es_fractions.columns:
                pt_mix[source] += net_imports * es_fractions[source]
            else:
                # Use the average fraction of known sources for unknown sources
                known_fractions = es_fractions.mean(axis=1)
                pt_mix[source] += net_imports * known_fractions
                logging.warning(f"Source {source} not found in Spanish data. Using average of known sources.")
        
        # Apply transmission loss (assuming 5% loss)
        transmission_efficiency = 0.95
        pt_mix = pt_mix * transmission_efficiency
        
        # Calculate percentages
        pt_total = pt_mix.sum(axis=1)
        pt_percentages = pt_mix.div(pt_total, axis=0) * 100
        
        return pt_mix, pt_percentages
