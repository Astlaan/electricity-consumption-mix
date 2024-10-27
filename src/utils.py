from datetime import datetime
from typing import Any, Dict
import pandas as pd
from config import PSR_TYPE_MAPPING


def validate_inputs(args):
    if args.start_date >= args.end_date:
        print("Error: Start date must be before end date.")
        return False
    return True


def get_active_psr_in_dataframe(df):
    return [col for col in df.columns if col in PSR_TYPE_MAPPING]


def get_cache_filename(params: Dict[str, Any]) -> str:
    """Generate cache filename based on data type and countries."""
    document_type = params.get("documentType")
    in_domain = params.get("in_Domain", "")
    out_domain = params.get("out_Domain", "")

    if document_type == "A75":  # Generation data
        if "PT" in in_domain:
            return "generation_pt"
        elif "ES" in in_domain:
            return "generation_es"
    elif document_type == "A11":  # Flow data
        if "PT" in out_domain and "ES" in in_domain:
            return "flow_pt_to_es"
        elif "ES" in out_domain and "PT" in in_domain:
            return "flow_es_to_pt"

    raise ValueError(f"Unsupported combination of document type and domains")
