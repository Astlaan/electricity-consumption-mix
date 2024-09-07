import pandas as pd

import pandas as pd
import numpy as np

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data, es_data, fr_data=None, include_french_contribution=False):
        pt_gen = pt_data.get('generation', pd.DataFrame())
        pt_imports = pt_data.get('imports', pd.DataFrame())
        pt_exports = pt_data.get('exports', pd.DataFrame())
        es_gen = es_data.get('generation', pd.DataFrame())
        es_imports_fr = es_data.get('imports_fr', pd.DataFrame())
        es_exports_fr = es_data.get('exports_fr', pd.DataFrame())

        # Handle empty DataFrames
        if pt_gen.empty and es_gen.empty:
            return pd.DataFrame(), None

        # Ensure 'start_time' is in datetime format
        for df in [pt_gen, pt_imports, pt_exports, es_gen, es_imports_fr, es_exports_fr]:
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

        # Calculate net imports for Portugal
        pt_net_imports = pt_imports_grouped - pt_exports_grouped

        # Calculate Spain's generation mix
        if not es_gen.empty:
            es_gen_grouped = es_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
        else:
            es_gen_grouped = pd.DataFrame()

        # Calculate net imports for Spain from France
        es_imports_fr_grouped = es_imports_fr.groupby('start_time')['quantity'].sum() if not es_imports_fr.empty else pd.Series(dtype=float)
        es_exports_fr_grouped = es_exports_fr.groupby('start_time')['quantity'].sum() if not es_exports_fr.empty else pd.Series(dtype=float)
        es_net_imports_fr = es_imports_fr_grouped - es_exports_fr_grouped

        # Adjust Spain's mix if French contribution is included
        if include_french_contribution and fr_data:
            fr_gen = fr_data.get('generation', pd.DataFrame())
            if not fr_gen.empty:
                fr_gen_grouped = fr_gen.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
                fr_total = fr_gen_grouped.sum(axis=1)
                fr_percentages = fr_gen_grouped.div(fr_total, axis=0)

                # Adjust Spain's mix based on imports from France
                for source in fr_percentages.columns:
                    if source in es_gen_grouped.columns:
                        es_gen_grouped[source] += es_net_imports_fr * fr_percentages[source]
                    else:
                        es_gen_grouped[source] = es_net_imports_fr * fr_percentages[source]

        # Calculate Spain's percentages
        es_total = es_gen_grouped.sum(axis=1)
        es_percentages = es_gen_grouped.div(es_total, axis=0)

        # Adjust Portugal's mix based on imports from Spain
        pt_mix = pt_gen_grouped.copy() if not pt_gen_grouped.empty else pd.DataFrame()
        for source in es_percentages.columns:
            if source in pt_mix.columns:
                pt_mix[source] += pt_net_imports * es_percentages[source]
            else:
                pt_mix[source] = pt_net_imports * es_percentages[source]

        # Calculate percentages for Portugal
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
        es_percentages.index.name = None
        es_percentages.columns.name = None

        return pt_percentages.rename(columns={'psr_type': None}), es_percentages.rename(columns={'psr_type': None}) * 100
