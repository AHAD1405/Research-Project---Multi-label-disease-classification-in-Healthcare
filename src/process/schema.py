from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class EventRow:
    patient_id: str
    visit_id: str
    visit_date: str   # ISO
    code: str
    coding_system: Literal["ICD9","ICD10"]