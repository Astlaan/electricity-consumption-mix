import pandas as pd

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data, es_data):
        pt_gen = pt_data.get('generation', pd.DataFrame())
        pt_imports = pt_data.get('imports', pd.DataFrame())
        pt_exports = pt_data.get('exports', pd.DataFrame())
        es_gen = es_data.get('generation', pd.DataFrame())

        # Handle empty DataFrames
        if pt_gen.empty and es_gen.empty:
            return pd.DataFrame()

        # Ensure 'start_time' is in datetime format
        for df in [pt_gen, pt_imports, pt_exports, es_gen]:
            if not df.empty:
                if 'start_time' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start_time'])
                elif 'start' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start'])
                    df = df.rename(columns={'start': 'start_time'})

        # Calculate Portugal's mix
        if not pt_gen.empty:
            pt_gen_grouped = pt_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
        else:
            pt_gen_grouped = pd.DataFrame()

        pt_imports_grouped = pt_imports.groupby('start_time')['quantity'].sum() if not pt_imports.empty else pd.Series(dtype=float)
        pt_exports_grouped = pt_exports.groupby('start_time')['quantity'].sum() if not pt_exports.empty else pd.Series(dtype=float)

        # Calculate net imports
        net_imports = pt_imports_grouped - pt_exports_grouped

        # Calculate Spain's generation mix
        if not es_gen.empty:
            es_gen_grouped = es_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
            es_total = es_gen_grouped.sum(axis=1)
            es_percentages = es_gen_grouped.div(es_total, axis=0)
        else:
            es_percentages = pd.DataFrame()

        # Adjust Portugal's mix based on imports from Spain
        pt_mix = pt_gen_grouped.copy() if not pt_gen_grouped.empty else pd.DataFrame()
        for source in es_percentages.columns:
            if source in pt_mix.columns:
                pt_mix[source] += net_imports * es_percentages[source]
            else:
                pt_mix[source] = net_imports * es_percentages[source]

        # Calculate percentages
        if not pt_mix.empty:
            pt_total = pt_mix.sum(axis=1)
            pt_percentages = pt_mix.div(pt_total, axis=0) * 100

            # Replace negative values with 0 and recalculate percentages
            pt_percentages[pt_percentages < 0] = 0
            pt_percentages = pt_percentages.div(pt_percentages.sum(axis=1), axis=0) * 100
        else:
            pt_percentages = pd.DataFrame()

        # Reset the index name to None and rename the columns
        pt_percentages.index.name = None
        pt_percentages.columns.name = None
        return pt_percentages.rename(columns={'psr_type': None})
