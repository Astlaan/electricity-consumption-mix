import pandas as pd
import logging

logger = logging.getLogger(__name__)

class ElectricityMixCalculator:
    def calculate_mix(self, pt_data: dict, es_data: dict) -> pd.DataFrame:
        logger.debug("Starting calculate_mix method")
        pt_gen = pt_data.get('generation', pd.DataFrame())
        pt_imports = pt_data.get('imports', pd.DataFrame())
        pt_exports = pt_data.get('exports', pd.DataFrame())
        es_gen = es_data.get('generation', pd.DataFrame())

        logger.debug(f"Input data shapes: pt_gen={pt_gen.shape}, pt_imports={pt_imports.shape}, pt_exports={pt_exports.shape}, es_gen={es_gen.shape}")

        if pt_gen.empty and es_gen.empty:
            logger.warning("Both Portuguese and Spanish generation data are empty")
            return pd.DataFrame()

        self._ensure_datetime_format([pt_gen, pt_imports, pt_exports, es_gen])

        pt_gen_grouped = self._group_generation_data(pt_gen)
        es_gen_grouped = self._group_generation_data(es_gen)
        logger.debug(f"Grouped data shapes: pt_gen_grouped={pt_gen_grouped.shape}, es_gen_grouped={es_gen_grouped.shape}")

        net_imports = self._calculate_net_imports(pt_imports, pt_exports)
        logger.debug(f"Net imports shape: {net_imports.shape}")

        es_percentages = self._calculate_percentages(es_gen_grouped)
        logger.debug(f"Spanish percentages shape: {es_percentages.shape}")

        pt_mix = self._adjust_portugal_mix(pt_gen_grouped, net_imports, es_percentages)
        logger.debug(f"Adjusted Portuguese mix shape: {pt_mix.shape}")

        pt_percentages = self._calculate_percentages(pt_mix)
        logger.debug(f"Portuguese percentages shape: {pt_percentages.shape}")

        result = self._clean_output(pt_percentages)
        logger.debug(f"Final result shape: {result.shape}")
        logger.debug(f"Sum of percentages: {result.sum(axis=1)}")

        return result

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
                pt_mix[source] += net_imports * es_percentages[source] / 100
            else:
                pt_mix[source] = net_imports * es_percentages[source] / 100
        return pt_mix.fillna(0)  # Fill NaN values with 0

    def _clean_output(self, df):
        df[df < 0] = 0
        row_sums = df.sum(axis=1)
        df = df.div(row_sums, axis=0).fillna(0) * 100
        df = df.round(6)  # Round to 6 decimal places
        df = df.div(df.sum(axis=1), axis=0) * 100  # Normalize again to ensure sum is exactly 100
        df.index.name = None
        df.columns.name = None
        return df.rename(columns={'psr_type': None})
