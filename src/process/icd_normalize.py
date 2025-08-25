"""
ICD code normalization and validation functions.
args:
    - code: str, the ICD code to normalize
    - system: str, either 'ICD9' or 'ICD10'
    - dotless: bool, if True, remove dots from the code
returns:
    - normalized code: str
"""

import re

def normalize_icd(code: str, system: str, dotless: bool = True) -> str:
    if not isinstance(code, str):
        return ""
    c = code.strip().upper().replace(" ", "")
    # remove non-alphanum except dot
    c = re.sub(r"[^A-Z0-9\.]", "", c)
    if dotless:
        c = c.replace(".", "")
    # optional: pad/truncate rules if your data is messy
    return c

def is_valid_diag(code: str) -> bool:
    return bool(code)  # expand with ICD patterns if you need stricter control