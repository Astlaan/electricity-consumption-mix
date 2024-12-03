from dataclasses import dataclass, fields
import pandas as pd


@dataclass
class Data:
    generation_pt: pd.DataFrame
    generation_es: pd.DataFrame
    generation_fr: pd.DataFrame
    flow_pt_to_es: pd.DataFrame
    flow_es_to_pt: pd.DataFrame
    flow_fr_to_es: pd.DataFrame
    flow_es_to_fr: pd.DataFrame

    def assert_equal_length(self) -> None:
        """Validate that all dataframes in this Data instance have matching indices."""
        # Get the first dataframe to use as reference
        first_field = fields(self)[0]
        ref_df = getattr(self, first_field.name)
        ref_index = ref_df.index

        # Compare all other dataframes to the reference
        for field in fields(self)[1:]:
            df = getattr(self, field.name)
            if not df.index.equals(ref_index):
                raise ValueError(
                    f"Index mismatch in {field.name} compared to {first_field.name}"
                )
