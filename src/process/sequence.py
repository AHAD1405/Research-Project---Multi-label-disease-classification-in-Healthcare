"""
- (Function) Build sequences of yearly events for each patient. Each sequence contains a history of diagnosis codes 
over a fixed number of past years and a target set of diagnosis codes for the current year.

- (The target codes) are represented as a multi-hot vector based on a provided vocabulary mapping.
The data is split into training, validation, and test sets based on the target year.

- (The input dataframe) is expected to have the following columns:
  patient_id, visit_date, code_norm

- (The output dataframes) will have the following columns:
    patient_id, target_year, hist_years(list[int]), hist_codes(list[list[str]]), target_multi_hot(list[int])

- (Temporal split) is derived from target_year.

- Parameters:
    df_events: pd.DataFrame - DataFrame with patient events.
    label_to_id: Dict[str, int] - Mapping from diagnosis codes to integer IDs for multi-hot encoding.
    history_years: int - Number of past years to include in the history.    
    min_year: int - Minimum year to consider for events.
    max_year: int - Maximum year to consider for events.
    train_until: int - Last year to include in the training set.
    val_until: int - Last year to include in the validation set.
- Returns:
    Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] - Train, validation, and test DataFrames.

"""

import pandas as pd
from typing import Dict, Tuple

def build_yearly_sequences(df_events: pd.DataFrame,
                           label_to_id: Dict[str, int],
                           history_years: int,
                           min_year: int,
                           max_year: int
                           ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Returns train/val/test dataframes with columns:
      patient_id, target_year, hist_years(list[int]), hist_codes(list[list[str]]), target_multi_hot(list[int])
    Temporal split is derived from target_year.
    """
    # derive year
    df = df_events.copy()
    df["year"] = pd.to_datetime(df["visit_date"], errors="coerce").dt.year
    df = df[(df["year"] >= min_year) & (df["year"] <= max_year)]
    # restrict to diagnosis codes in vocab for targets; history can keep all codes if you like
    df["code_in_vocab"] = df["code_norm"].isin(label_to_id)

    rows = []
    for (pid), g in df.sort_values("year").groupby("patient_id"):
        years = sorted(g["year"].unique().tolist())
        for Y in years:
            # history window: Y-history_years .. Y-1
            hist_window = list(range(Y - history_years, Y))
            if min(hist_window) < min_year:  # not enough history
                continue
            hist = []
            for y in hist_window:
                codes_y = g.loc[g["year"] == y, "code_norm"].dropna().tolist()
                hist.append(codes_y)
            # target labels = codes in year Y that are in vocab
            target_codes = g.loc[(g["year"] == Y) & (g["code_in_vocab"]), "code_norm"].unique().tolist()
            if len(target_codes) == 0:
                # allow negatives; keep to avoid bias. If you want to drop, add a continue.
                pass
            K = len(label_to_id)
            multi_hot = [0]*K
            for c in target_codes:
                multi_hot[label_to_id[c]] = 1

            rows.append({
                "patient_id": pid,
                "target_year": Y,
                "hist_years": hist_window,
                "hist_codes": hist,
                "target_multi_hot": multi_hot
            })

    df_seqs = pd.DataFrame(rows)

    # temporal split based on target_year
    train = df_seqs[df_seqs["target_year"] <= train_until]
    val   = df_seqs[(df_seqs["target_year"] > train_until) & (df_seqs["target_year"] <= val_until)]
    test  = df_seqs[df_seqs["target_year"] > val_until]

    return train.reset_index(drop=True), val.reset_index(drop=True), test.reset_index(drop=True)
