"""Pediatric index-patient filter: decide whether a medical question's PRIMARY
clinical subject is a pediatric patient (birth through adolescence).

The rule is deliberately not "does the text mention a child." A question mentions
children for many reasons that are not pediatric care: an adult with a childhood
history ("40-year-old with a history of childhood asthma"), a pregnant adult
(the mother is the patient), a pedigree/offspring-risk question, or a disease
name that happens to contain a pediatric term. This filter identifies the
primary clinical subject and keeps only postnatal pediatric patients.

The regexes and gate logic in this module are lifted verbatim from the filter
validated in the Growth-MedQA project (cross-referenced against PedMedQA; see
docs/validation.md). Do not "improve" the patterns without re-validating: the
behavior, including a known neonatal-recall gap, is a measured quantity.

Pure standard library (``re`` only). No pandas, no network, no I/O.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = [
    "pediatric_reasons",
    "is_pediatric",
    "classify",
    "has_adult_primary_subject",
    "is_adult_pregnancy_false_positive",
    "PediatricLabel",
    "REASON_LABELS",
]

REASON_LABELS = {
    "explicit_age_under_18": "Text contains an explicit age under 18 years.",
    "infant_or_neonatal": "Text contains infant, newborn, neonate, baby, or month-old wording.",
    "child_or_adolescent_terms": "Text uses child, children, adolescent, teen, boy, girl, or school-age language in a clinical context.",
    "pediatric_care_setting": "Text refers to pediatric care, a pediatrician, well-child care, or a pediatric setting.",
    "pediatric_dataset_scope": "The source dataset/config is explicitly pediatric in scope (caller-asserted).",
}

# --- age patterns -----------------------------------------------------------
AGE_UNDER_18_RE = re.compile(
    r"\b(?P<age>1[0-7]|[1-9])\s*(?:-| )?"
    r"(?P<unit>year|years|yr|yrs|y)(?:-| )?old\b",
    re.I,
)
ADULT_AGE_RE = re.compile(
    r"\b(?P<age>[1-9]\d{1,2})\s*(?:-| )?"
    r"(?P<unit>year|years|yr|yrs|y)(?:-| )?old\b",
    re.I,
)
MONTH_OLD_RE = re.compile(r"\b\d{1,2}\s*(?:-| )?(?:month|months|mo|mos)(?:-| )?old\b", re.I)

# --- pediatric subject cues -------------------------------------------------
INFANT_RE = re.compile(
    r"\b(?:newborns?|neonates?|neonatal|infants?|infancy|babies|baby|toddlers?)\b", re.I
)
CHILD_RE = re.compile(
    r"\b(?:child|children|adolescent|adolescents|teen|teens|teenager|teenagers|"
    r"boy|boys|girl|girls|school-aged|school aged|preschool|kindergarten)\b",
    re.I,
)
PED_CARE_RE = re.compile(
    r"\b(?:pediatric|paediatric|pediatrician|paediatrician|well-child|well child|"
    r"children'?s hospital|pediatric airway|paediatric airway)\b",
    re.I,
)
CLINICAL_CONTEXT_RE = re.compile(
    r"\b(?:patient|physician|clinic|hospital|emergency|diagnos|disease|disorder|syndrome|"
    r"deficien|infection|vaccine|vaccination|immuni[sz]ation|treatment|therapy|surgery|"
    r"symptom|examination|laboratory|x-ray|radiograph|genetic|congenital|neonatal|"
    r"cystic fibrosis|asthma|diabetes|seizure|fever|pain|vomit|diarrhea|cough|rash)\b",
    re.I,
)

# --- false-positive gates ---------------------------------------------------
NON_PATIENT_CHILD_RE = re.compile(
    r"\b(?:adult children|healthy children|future children|have children|having children|"
    r"bear children|childbearing|grandchildren)\b",
    re.I,
)
NON_PATIENT_INFANT_RE = re.compile(
    r"\b(?:have|having|had|has|not having|not haveing)\s+(?:a\s+)?baby\b|"
    r"\bbaby oil\b|"
    r"\bfuture babies\b|"
    r"\bwhat will my babies\b",
    re.I,
)
ADULT_PREGNANCY_CONTEXT_RE = re.compile(
    r"\bpositive pregnancy test\b|\bpregnan(?:cy|t)\b|\blast menstrual period\b|"
    r"\bcontraception\b|\bsexual partners?\b|\bobstetric\b|\bgravida\b|\bpara\b",
    re.I,
)
POSTNATAL_CHILD_TARGET_RE = re.compile(
    r"\b(?:newborn|neonate|neonatal|infant|toddler|child|children|adolescent|teenager|"
    r"pediatric|paediatric)\s+(?:patient|boy|girl|care|diagnosis|management|assessment|"
    r"treatment|disease|condition|population|clinic|ward|visit)\b|"
    r"\b(?:in|among)\s+(?:children|adolescents|pediatric patients|paediatric patients)\b",
    re.I,
)


@dataclass(frozen=True)
class PediatricLabel:
    """Result of classifying one piece of text."""

    is_pediatric: bool
    reasons: tuple[str, ...]

    @property
    def reason_detail(self) -> str:
        return "; ".join(REASON_LABELS[r] for r in self.reasons)


def has_adult_primary_subject(text: str) -> bool:
    """True when an adult age (>= 18) is the index patient.

    Fires when an adult age appears in the opening of the vignette AND appears
    before any pediatric age cue. This is the "40-year-old with a childhood
    history of X" case: the adult is the patient, the child term is background.
    """
    prefix = text[:500]
    adult_match = next(
        (m for m in ADULT_AGE_RE.finditer(prefix) if int(m.group("age")) >= 18), None
    )
    if adult_match is None:
        return False
    pediatric_positions = [
        m.start()
        for pattern in (AGE_UNDER_18_RE, MONTH_OLD_RE, INFANT_RE)
        for m in pattern.finditer(prefix)
    ]
    return not pediatric_positions or adult_match.start() < min(pediatric_positions)


def is_adult_pregnancy_false_positive(text: str) -> bool:
    """True when the subject is a pregnant/reproductive adult (the mother), not
    a postnatal child. Guards against obstetric and maternal-fetal vignettes
    that carry neonatal terms only as context."""
    adult_match = next(
        (m for m in ADULT_AGE_RE.finditer(text[:3000]) if int(m.group("age")) >= 18), None
    )
    pregnancy_only_reproductive_history = (
        ADULT_PREGNANCY_CONTEXT_RE.search(text) is not None
        and POSTNATAL_CHILD_TARGET_RE.search(text) is None
    )
    return (
        (adult_match is not None or pregnancy_only_reproductive_history)
        and ADULT_PREGNANCY_CONTEXT_RE.search(text) is not None
    )


def pediatric_reasons(
    text: str,
    *,
    exclude_adult_primary_subject: bool = True,
    pediatric_scope: bool = False,
) -> list[str]:
    """Return the list of reasons the text is a pediatric index-patient question.

    An empty list means "not pediatric" (an adult, a mother, a pedigree, or a
    non-clinical mention). A non-empty list means the primary clinical subject
    is a postnatal pediatric patient.

    Parameters
    ----------
    exclude_adult_primary_subject:
        When True (default), drop items whose index patient is an adult even if
        a pediatric term appears later (childhood history, "his daughter").
    pediatric_scope:
        Set True when the caller already knows the source is pediatric-only; it
        relaxes the clinical-context requirement on bare child/adolescent terms.
    """
    if is_adult_pregnancy_false_positive(text):
        return []
    if exclude_adult_primary_subject and has_adult_primary_subject(text):
        return []

    reasons: list[str] = []
    if pediatric_scope:
        reasons.append("pediatric_dataset_scope")
    if AGE_UNDER_18_RE.search(text):
        reasons.append("explicit_age_under_18")
    if MONTH_OLD_RE.search(text) or (
        INFANT_RE.search(text) and not NON_PATIENT_INFANT_RE.search(text)
    ):
        reasons.append("infant_or_neonatal")
    if (
        CHILD_RE.search(text)
        and not NON_PATIENT_CHILD_RE.search(text)
        and (pediatric_scope or CLINICAL_CONTEXT_RE.search(text))
    ):
        reasons.append("child_or_adolescent_terms")
    if PED_CARE_RE.search(text):
        reasons.append("pediatric_care_setting")

    return list(dict.fromkeys(reasons))


def classify(
    text: str,
    *,
    exclude_adult_primary_subject: bool = True,
    pediatric_scope: bool = False,
) -> PediatricLabel:
    """Classify one text and return a :class:`PediatricLabel`."""
    reasons = pediatric_reasons(
        text,
        exclude_adult_primary_subject=exclude_adult_primary_subject,
        pediatric_scope=pediatric_scope,
    )
    return PediatricLabel(is_pediatric=bool(reasons), reasons=tuple(reasons))


def is_pediatric(text: str, **kwargs) -> bool:
    """Convenience boolean wrapper around :func:`pediatric_reasons`."""
    return bool(pediatric_reasons(text, **kwargs))
