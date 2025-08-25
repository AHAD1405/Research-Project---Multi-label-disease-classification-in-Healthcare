"""
Convert MIMIC-III or MIMIC-IV diagnoses into unified events schema:
patient_id | visit_id | visit_date | code | coding_system
args:
    --version {iii,iv}       MIMIC version
    --diagnoses PATH         Path to DIAGNOSES table (CSV/Parquet)
    --admissions PATH        Path to ADMISSIONS table (CSV/Parquet)
    --out PATH               Output Parquet path
    [--keep_dots]           Keep dots in ICD codes (default: remove)
Output:
    Parquet file with columns: patient_id, visit_id, visit_date, code, coding_system
"""

import os, re, argparse
import pandas as pd

def read_any(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in (".parquet", ".pq"):
        return pd.read_parquet(path)
    return pd.read_csv(path, dtype=str, low_memory=False)

def norm_code(code: str, dotless: bool = True) -> str:
    if not isinstance(code, str): return ""
    c = re.sub(r"[^A-Za-z0-9\.]", "", code.strip().upper())
    return c.replace(".", "") if dotless else c

# ---------- MIMIC-III ----------
def mimic3_to_events(diagnoses_path, admissions_path, out_path, keep_dots=False):
    d = read_any(diagnoses_path)
    a = read_any(admissions_path)
    d.columns = [c.lower() for c in d.columns]
    a.columns = [c.lower() for c in a.columns]
    for req in ("subject_id","hadm_id","icd9_code"):
        if req not in d.columns: raise ValueError(f"MIMIC-III diagnoses missing {req}")
    for req in ("hadm_id","admittime"):
        if req not in a.columns: raise ValueError(f"MIMIC-III admissions missing {req}")

    # Join to get admit date
    m = d.merge(a[["hadm_id","admittime"]], how="left", on="hadm_id")
    m["visit_date"] = pd.to_datetime(m["admittime"], errors="coerce").dt.date.astype(str)
    m["code"] = m["icd9_code"].map(lambda x: norm_code(x, dotless=not keep_dots))
    m["coding_system"] = "ICD9"
    events = m.loc[m["code"].notna() & (m["code"] != ""), ["subject_id","hadm_id","visit_date","code","coding_system"]]
    events = events.rename(columns={"subject_id":"patient_id","hadm_id":"visit_id"}).drop_duplicates()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    events.to_parquet(out_path, index=False)
    print(f"[OK] Wrote {len(events):,} events -> {out_path}")
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", required=True, choices=["iii","iv"], help="MIMIC version")
    ap.add_argument("--diagnoses", required=True, help="Path to DIAGNOSES table (CSV/Parquet)")
    ap.add_argument("--admissions", required=True, help="Path to ADMISSIONS table (CSV/Parquet)")
    ap.add_argument("--out", required=True, help="Output Parquet path")
    ap.add_argument("--keep_dots", action="store_true", help="Keep dots in ICD codes")
    args = ap.parse_args()

    mimic3_to_events(args.diagnoses, args.admissions, args.out, keep_dots=args.keep_dots)


if __name__ == "__main__":
    main()