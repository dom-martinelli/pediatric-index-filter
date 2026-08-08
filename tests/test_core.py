"""Boundary tests. These encode the filter's intended behavior, including one
known limitation (the neonatal-recall gap), so the suite documents the tool
honestly rather than asserting behavior it does not have.
"""

from pediatric_index_filter import classify, is_pediatric, pediatric_reasons


# --- INCLUDE: the primary clinical subject is a postnatal child --------------

def test_school_age_child_at_pediatrician():
    text = "A 6-year-old boy is brought to his pediatrician for a well-child visit."
    label = classify(text)
    assert label.is_pediatric
    assert "explicit_age_under_18" in label.reasons
    assert "pediatric_care_setting" in label.reasons


def test_neonate_by_infant_term():
    assert is_pediatric("A 2-week-old infant presents with poor feeding and jaundice.")


def test_adolescent():
    assert is_pediatric("A 14-year-old girl is evaluated for short stature and delayed puberty.")


def test_child_with_clinical_context():
    # child + a clinical-context term, no explicit age
    assert is_pediatric("A child presents to the emergency department with fever and a rash.")


def test_bare_child_no_context_needs_scope():
    # A bare "in a child" question about a condition not in the clinical lexicon,
    # with no age, is NOT kept by default (documented no-age recall gap), but IS
    # kept when the caller asserts the source is pediatric-scoped.
    text = "What is the most common cause of renal artery stenosis in a child?"
    assert not is_pediatric(text)
    assert is_pediatric(text, pediatric_scope=True)


# --- EXCLUDE: a pediatric term appears, but the patient is not a child --------

def test_adult_with_childhood_history_excluded():
    text = "A 40-year-old man with a history of childhood asthma presents with dyspnea."
    assert not is_pediatric(text)


def test_pregnant_adult_is_the_patient_excluded():
    text = "A 24-year-old woman, gravida 2 para 1, at 39 weeks' gestation presents in latent labor."
    assert not is_pediatric(text)


def test_postpartum_mother_excluded():
    text = ("A 25-year-old woman develops palpitations and heat intolerance after "
            "delivering her child; TSH is suppressed.")
    assert not is_pediatric(text)


def test_pedigree_offspring_risk_excluded():
    text = ("A couple who are both carriers ask about the risk of having children "
            "with cystic fibrosis.")
    assert not is_pediatric(text)


def test_adult_primary_before_pediatric_mention_excluded():
    # adult age comes first; the child is background
    text = "A 55-year-old woman recalls that as a child she had rheumatic fever; she now has dyspnea."
    assert not is_pediatric(text)


# --- KNOWN LIMITATION: neonatal-recall gap -----------------------------------

def test_known_neonatal_gap_is_dropped():
    """A real newborn patient framed through the mother's gravida status is
    dropped by the adult-pregnancy gate. This is the documented ~75% neonate
    recall gap (see docs/validation.md). The test asserts current behavior so
    the limitation is visible, not hidden."""
    text = ("A newborn male born to a 36-year-old gravida 3 mother develops "
            "respiratory distress shortly after birth.")
    assert not is_pediatric(text)  # KNOWN GAP, not desired behavior


# --- API surface -------------------------------------------------------------

def test_reasons_are_deduplicated_and_known():
    from pediatric_index_filter import REASON_LABELS
    reasons = pediatric_reasons("A 3-year-old child in the pediatric clinic.")
    assert reasons == list(dict.fromkeys(reasons))
    assert all(r in REASON_LABELS for r in reasons)
