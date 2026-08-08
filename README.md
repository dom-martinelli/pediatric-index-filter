# pediatric-index-filter

Keep the medical questions whose **primary clinical subject is a pediatric
patient**, and drop the ones that only *mention* a child.

Naive keyword filtering ("does the text contain child / infant / adolescent")
massively over-includes. A question can carry pediatric words while the patient
is an adult with a childhood history, a pregnant woman (the mother is the
patient), or a couple asking about the risk of future children. This tool
identifies the **index patient** and keeps only postnatal pediatric cases. It is
deterministic, dependency-light, and needs no API keys or model calls.

```text
A 40-year-old man with a history of childhood asthma ...   -> NOT pediatric
A 24-year-old G2P1 woman at 39 weeks' gestation ...        -> NOT pediatric
risk of having children with cystic fibrosis ...           -> NOT pediatric
A 6-year-old boy is brought to his pediatrician ...        -> pediatric
the most common cause of X in a child ...                  -> pediatric
```

## Why it exists

Built while curating a pediatric-growth question benchmark, where a keyword sweep
of a large medical-QA corpus returned far more "pediatric" hits than were real.
The filter is what turned that keyword pile into a clean pediatric core. The same
logic generalizes to any project that needs a defensible pediatric subset of a
medical-QA dataset.

The classification rule, verbatim:

> Do not classify a question as pediatric solely because it contains child terms.
> Identify the primary clinical subject and the target of the question.

Full inclusion/exclusion criteria: [docs/boundary_criteria.md](docs/boundary_criteria.md).

## Install

```bash
pip install -e .          # library only: standard-library core, no third-party deps
pip install -e ".[cli]"   # add pandas for the CSV/Parquet file CLI
```

## Use it as a library

```python
from pediatric_index_filter import is_pediatric, classify

is_pediatric("A 6-year-old boy is brought to his pediatrician.")   # True
is_pediatric("A 40-year-old with a history of childhood asthma.")  # False

label = classify("A 2-week-old infant presents with jaundice.")
label.is_pediatric      # True
label.reasons           # ('infant_or_neonatal',)
label.reason_detail     # 'Text contains infant, newborn, neonate, ... wording.'
```

Options:

- `exclude_adult_primary_subject=True` (default) drops adult-first items even when
  a pediatric term appears later. Set `False` to keep them.
- `pediatric_scope=True` tells the filter the source is already pediatric-only,
  which relaxes the clinical-context requirement on bare child terms.

## Use it on a file

```bash
python -m pediatric_index_filter \
    --input examples/sample_questions.csv \
    --text-column question \
    --output labeled.csv
```

It adds `is_pediatric_index_patient`, `pediatric_reasons`, and
`pediatric_reason_detail` columns, and prints the funnel:

```text
11 questions in -> 5 pediatric index-patient (45.5%)
```

Add `--context-column <col>` if the vignette and the question live in separate
columns, and `--keep-pediatric-only` to write just the kept rows.

## How good is it, honestly

Cross-referenced against **PedMedQA** (an independent, age-based pediatric subset
of MedQA): Cohen's kappa 0.86, recall 89.9%. But PedMedQA is a noisy second
labeler with its own errors, not a gold standard, so treat that as a lower bound,
not a validated accuracy. There is one real weak spot, a **neonatal-recall gap**
(newborns framed through the mother's pregnancy can be dropped), with a validated
opt-in fix that lifts recall to 95.6%. Details and reproduction:
[docs/validation.md](docs/validation.md).

## Scope and limits

- English medical-QA text (vignette + question).
- Postnatal-only by design: fetal/prenatal targets are excluded on purpose.
- Term/subject-based, not a language model. It is fast, transparent, and auditable
  (every decision comes with reasons), and it will miss cases that need semantic
  judgment. That tradeoff is the point.

## Tests

```bash
pip install pytest && pytest
```

The suite encodes the boundary cases, including the known neonatal gap, so it
documents the tool honestly rather than asserting behavior it does not have.

## License

MIT (see [LICENSE](LICENSE)). No third-party datasets are redistributed.
