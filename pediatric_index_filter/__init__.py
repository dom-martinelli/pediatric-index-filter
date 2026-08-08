"""Pediatric index-patient filter.

Keep medical questions whose PRIMARY clinical subject is a pediatric patient;
drop adults-with-childhood-history, maternal/pregnancy, and pedigree items.
"""

from .core import (
    PediatricLabel,
    REASON_LABELS,
    classify,
    has_adult_primary_subject,
    is_adult_pregnancy_false_positive,
    is_pediatric,
    pediatric_reasons,
)

__version__ = "0.1.0"

__all__ = [
    "PediatricLabel",
    "REASON_LABELS",
    "classify",
    "has_adult_primary_subject",
    "is_adult_pregnancy_false_positive",
    "is_pediatric",
    "pediatric_reasons",
    "__version__",
]
