# Validation and known limits

## Cross-reference against PedMedQA (not a gold-standard validation)

The filter was cross-referenced against **PedMedQA** (Jaiswal et al., *Pediatrics
Open Science* 2025; openly released under CC BY-NC-ND 4.0), an independent,
peer-reviewed, method-different pediatric subset of MedQA that labels items by
the Munich Age Classification System (age-based), where this filter is
term/subject-based. Two methods built on different principles.

**Read this honestly.** PedMedQA is a useful second opinion, **not** ground
truth: it carries its own label errors (for example, a 19-year-old labeled as an
infant). So agreement with it is a *cross-reference and a lower bound*, not a
clean validation, and in a disagreement this filter is often the correct one
(it excludes a maternal/adult item that PedMedQA let in). Do not report the
numbers below as "validated accuracy."

Cross-reference figures (deterministic, on MedQA):

| Metric vs PedMedQA | Value |
|---|---|
| Recall / sensitivity on PedMedQA pediatric items | 89.9% |
| Specificity vs the MedQA complement | 96.8% |
| Precision (lower bound; some "FPs" are PedMedQA's own misses) | 88.3% |
| Cohen's kappa (two independent methods) | 0.86 |

## The one real gap: neonates

Recall is not uniform across age bands. Before any fix:

| Age band (MACS) | Recall |
|---|---|
| Early childhood | 98.3% |
| Adolescent | 94.5% |
| Infant | 91.0% |
| **Neonate (< 3 mo)** | **75.4%** |
| No explicit age stated | 58.7% |

**Mechanism.** The adult-pregnancy gate (`is_adult_pregnancy_false_positive`)
fires on framing like "born to a 36-year-old gravida mother," and the
postnatal-child rescue only matches a child-noun followed by
patient / boy / girl / care / diagnosis / etc. So "newborn male," "male infant
is delivered," and "hours after delivery" can slip through and be dropped even
though the newborn is the real patient. `tests/test_core.py` includes this case
as a documented gap.

**A validated fix exists (opt-in, not shipped as default).** Adding a
newborn/neonatal-presence override to the adult-pregnancy gate lifted recall to
**95.6%** in a sandbox (neonate band 75.4% -> 96.0%, no-age 58.7% -> 92.7%),
recovering 153 of 272 misses. It is not the default because turning it on
changes corpus composition, which is a study-design decision the user should
make deliberately. If you want it, open an issue or wire it as a flag.

## Reproducing the cross-reference

PedMedQA is not redistributed here (respect its CC BY-NC-ND license). Download it
from its repository, then compare this filter's `is_pediatric` output on MedQA
against PedMedQA's age labels joined on the original MedQA index. A comparison
script is intentionally left to the user so no third-party data ships with this
tool.
