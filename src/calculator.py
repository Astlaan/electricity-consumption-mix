import pandas as pd
import numpy as np

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data, es_data, fr_data, include_france):
        if include_france:
            es_adjusted = self._adjust_spain_mix(es_data, fr_data)
        else:
            es_adjusted = es_data['generation']

        pt_mix = self._calculate_portugal_mix(pt_data, es_adjusted)
        return pt_mix

    def _adjust_spain_mix(self, es_data, fr_data):
        es_gen = es_data['generation']
        fr_gen = fr_data['generation']
        es_imports_fr = es_data['imports_fr']
        
        # Calculate the fraction of each source in France's generation mix
        fr_total = fr_gen.groupby('start_time')['quantity'].sum()
        fr_fractions = fr_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack().div(fr_total, axis=0)
        
        # Adjust Spain's mix based on imports from France
        es_adjusted = es_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack()
        for source in es_adjusted.columns:
            es_adjusted[source] += es_imports_fr['quantity'] * fr_fractions[source]
        
        return es_adjusted

    def _calculate_portugal_mix(self, pt_data, es_adjusted):
        pt_gen = pt_data['generation'].groupby(['start_time', 'psr_type'])['quantity'].sum().unstack()
        pt_imports = pt_data['imports'].groupby('start_time')['quantity'].sum()
        
        # Ensure all data is numeric
        pt_gen = pt_gen.apply(pd.to_numeric, errors='coerce')
        pt_imports = pd.to_numeric(pt_imports, errors='coerce')
        es_adjusted = es_adjusted.apply(pd.to_numeric, errors='coerce')
        
        # Calculate the fraction of each source in Spain's adjusted mix
        es_total = es_adjusted.sum(axis=1)
        es_fractions = es_adjusted.div(es_total, axis=0)
        
        # Calculate Portugal's mix
        pt_mix = pt_gen.copy()
        for source in pt_gen.columns:
            if source in es_fractions.columns:
                pt_mix[source] += pt_imports * es_fractions[source]
            else:
                # Use the average fraction of known sources for unknown sources
                known_fractions = es_fractions.mean(axis=1)
                pt_mix[source] += pt_imports * known_fractions
                logging.warning(f"Source {source} not found in Spanish data. Using average of known sources.")
        
        # Calculate percentages
        pt_total = pt_mix.sum(axis=1)
        pt_percentages = pt_mix.div(pt_total, axis=0) * 100
        
        return pt_percentages
