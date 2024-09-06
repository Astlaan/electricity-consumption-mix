import pandas as pd

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data, es_data):
        pt_gen = pt_data['generation']
        pt_imports = pt_data['imports']
        pt_exports = pt_data['exports']
        es_gen = es_data['generation']

        # Ensure 'start_time' is in datetime format
        for df in [pt_gen, pt_imports, pt_exports, es_gen]:
            if 'start_time' in df.columns:
                df['start_time'] = pd.to_datetime(df['start_time'])
            elif 'start' in df.columns:
                df['start_time'] = pd.to_datetime(df['start'])
                df = df.rename(columns={'start': 'start_time'})

        # Calculate Portugal's mix
        pt_gen_grouped = pt_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
        pt_imports_grouped = pt_imports.groupby('start_time')['quantity'].sum()
        pt_exports_grouped = pt_exports.groupby('start_time')['quantity'].sum()

        # Calculate net imports
        net_imports = pt_imports_grouped - pt_exports_grouped

        # Calculate Spain's generation mix
        es_gen_grouped = es_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
        es_total = es_gen_grouped.sum(axis=1)
        es_percentages = es_gen_grouped.div(es_total, axis=0)

        # Adjust Portugal's mix based on imports from Spain
        pt_mix = pt_gen_grouped.copy()
        for source in es_percentages.columns:
            if source in pt_mix.columns:
                pt_mix[source] += net_imports * es_percentages[source]
            else:
                pt_mix[source] = net_imports * es_percentages[source]

        # Calculate percentages
        pt_total = pt_mix.sum(axis=1)
        pt_percentages = pt_mix.div(pt_total, axis=0) * 100

        return pt_percentages
