import pandas as pd

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data: dict, es_data: dict) -> pd.DataFrame:
        pt_gen = pt_data.get('generation', pd.DataFrame())
        pt_imports = pt_data.get('imports', pd.DataFrame())
        pt_exports = pt_data.get('exports', pd.DataFrame())
        es_gen = es_data.get('generation', pd.DataFrame())

        if pt_gen.empty and es_gen.empty:
            return pd.DataFrame()

        self._ensure_datetime_format([pt_gen, pt_imports, pt_exports, es_gen])

        pt_gen_grouped = self._group_generation_data(pt_gen)
        es_gen_grouped = self._group_generation_data(es_gen)

        net_imports = self._calculate_net_imports(pt_imports, pt_exports)
        es_percentages = self._calculate_percentages(es_gen_grouped)

        pt_mix = self._adjust_portugal_mix(pt_gen_grouped, net_imports, es_percentages)
        pt_percentages = self._calculate_percentages(pt_mix)

        return self._clean_output(pt_percentages)

    def _ensure_datetime_format(self, dataframes):
        for df in dataframes:
            if not df.empty:
                if 'start_time' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start_time'])
                elif 'start' in df.columns:
                    df['start_time'] = pd.to_datetime(df['start'])
                    df = df.rename(columns={'start': 'start_time'})

    def _group_generation_data(self, df):
        return df.groupby(['start_time', 'psr_type'])['quantity'].sum().unstack(fill_value=0) if not df.empty else pd.DataFrame()

    def _calculate_net_imports(self, imports, exports):
        imports_grouped = imports.groupby('start_time')['quantity'].sum() if not imports.empty else pd.Series(dtype=float)
        exports_grouped = exports.groupby('start_time')['quantity'].sum() if not exports.empty else pd.Series(dtype=float)
        return imports_grouped - exports_grouped

    def _calculate_percentages(self, df):
        if df.empty:
            return pd.DataFrame()
        total = df.sum(axis=1)
        return df.div(total, axis=0) * 100

    def _adjust_portugal_mix(self, pt_mix, net_imports, es_percentages):
        for source in es_percentages.columns:
            if source in pt_mix.columns:
                pt_mix[source] += net_imports * es_percentages[source]
            else:
                pt_mix[source] = net_imports * es_percentages[source]
        return pt_mix

    def _clean_output(self, df):
        df[df < 0] = 0
        df = df.div(df.sum(axis=1), axis=0) * 100
        df.index.name = None
        df.columns.name = None
        return df.rename(columns={'psr_type': None})
