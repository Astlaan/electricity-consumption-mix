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
        fr_total = fr_gen.sum(axis=1)
        fr_fractions = fr_gen.div(fr_total, axis=0)
        
        # Adjust Spain's mix based on imports from France
        es_adjusted = es_gen.copy()
        for source in es_gen.columns:
            es_adjusted[source] += es_imports_fr * fr_fractions[source]
        
        return es_adjusted

    def _calculate_portugal_mix(self, pt_data, es_adjusted):
        pt_gen = pt_data['generation']
        pt_imports = pt_data['imports']
        
        # Calculate the fraction of each source in Spain's adjusted mix
        es_total = es_adjusted.sum(axis=1)
        es_fractions = es_adjusted.div(es_total, axis=0)
        
        # Calculate Portugal's mix
        pt_mix = pt_gen.copy()
        for source in pt_gen.columns:
            pt_mix[source] += pt_imports * es_fractions[source]
        
        # Calculate percentages
        pt_total = pt_mix.sum(axis=1)
        pt_percentages = pt_mix.div(pt_total, axis=0) * 100
        
        return pt_percentages
