import pandas as pd

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data: dict, es_data: dict) -> pd.DataFrame:
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
        df['hour'] = df['start_time'].dt.floor('H')
        print(df)
        try:
            grouped = df.groupby(['hour', 'psr_type'])['quantity'].sum().unstack(fill_value=0)
        except:
            print("Failed grouping by psr")
            print(df)
        return grouped

    def _calculate_net_imports(self, imports, exports):
        if imports.empty and exports.empty:
            return pd.Series(dtype=float)
        imports['hour'] = imports['start_time'].dt.floor('H')
        exports['hour'] = exports['start_time'].dt.floor('H')
        imports_grouped = imports.groupby('hour')['quantity'].sum()
        exports_grouped = exports.groupby('hour')['quantity'].sum()
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
