import json
import pandas as pd
from typing import Optional

"""
    This function create a vocabulary mapping for medical codes based on 
    their prevalence in a dataset of events.
    Args:
        df_events: pd.DataFrame - dataframe with at least columns ["patient_id", "code_norm"]
        min_patients: int - minimum number of unique patients a code must appear in to be included
        top_k: Optional[int] - if set, only the top_k most prevalent codes are included
        out_json: str - if set, the vocabulary is saved to this JSON file
    Returns:
        dict - mapping from code to integer index   
"""
def build_label_vocab(df_events: pd.DataFrame,
                      min_patients: int = 100,
                      top_k: Optional[int] = None,
                      out_json: str = None) -> dict:
    # patient-level prevalence per code
    grp = df_events.groupby(["code_norm"])["patient_id"].nunique().sort_values(ascending=False) # count unique patients per code(labela)
    grp = grp[grp >= min_patients]
    if top_k is not None:
        grp = grp.head(top_k)
        
    vocab = {code: i for i, code in enumerate(grp.index.tolist())}  # create a list of labels that meet the criteria

    if out_json: # save to json
        with open(out_json, "w") as f:
            json.dump({"label_to_id": vocab}, f, indent=2)
    return vocab