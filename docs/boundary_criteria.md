# Boundary criteria

## The decision rule

> Do not classify a question as pediatric solely because it contains
> child / children / adolescent / newborn wording. Identify the **primary
> clinical subject** and the target of the question.

A question belongs in the pediatric core when the primary clinical subject is a
newborn, infant, child, or adolescent **after birth**, and the question tests
diagnosis, management, mechanism, prevention, interpretation, or counseling for
that postnatal pediatric patient. This is a **postnatal-only** definition: it
excludes fetal/prenatal targets by design (see the tradeoff below).

## Include

- Explicit postnatal pediatric patients: newborns, infants, children, adolescents.
- Neonatal physiology and postnatal newborn care: Apgar scoring, respiratory
  distress, VLBW infant management, neonatal lab interpretation.
- Normal child development and developmental-milestone questions.
- Explicit pediatric targeting: "in a child," "in children," "in pediatric populations."
- Congenital or pediatric conditions when the subject is a postnatal child.
- Caregiver or parent decision-making when it directly affects a child's care.

## Exclude

- **Adult primary subject**, including "in adults" and adult professional decisions.
- **Adult with a childhood history** when the current subject is an adult and
  childhood is only background ("40-year-old with a history of childhood asthma").
- Broad/mixed-age or adult-heavy populations where pediatric relevance is only
  an incidental term.
- **Fetal-only, prenatal, maternal pregnancy, labor/delivery, and postpartum**
  items when the primary subject is not a liveborn child (the mother is the patient).
- Prenatal genetic counseling about an unborn child (inheritance risk before birth).
- **Offspring / next-generation risk** questions ("risk of having children with X").
- Generic genetics / inheritance without a named pediatric patient or decision.
- Education/examiner-performance or study-methodology items where pediatrics is
  incidental context.

## Ambiguity sources the filter is built to survive

- Family-relationship language: `child of`, `having children`, `grandchildren`.
- Adult childhood history: `as a child`, `since childhood`.
- Pregnancy / fetal / labor / delivery / postpartum framing.
- Disease or code names that contain pediatric terms.
- Population/public-health wording about children with no individual patient.

## How the code implements it

Two gates run first and can veto an item outright:

1. `is_adult_pregnancy_false_positive` — an adult age or reproductive/obstetric
   context (`gravida`, `para`, `pregnant`, `contraception`, ...) **without** an
   explicit postnatal-child target drops the item (the mother is the patient).
2. `has_adult_primary_subject` — an adult age (>= 18) appearing in the opening
   and **before** any pediatric age cue drops the item (adult-first).

If neither vetoes, the item is kept when it carries an explicit under-18 age, an
infant/neonatal term, a child/adolescent term in a clinical context, or a
pediatric-care setting. See `pediatric_index_filter/core.py`.

## Known tradeoff

The postnatal-only rule may exclude clinically relevant fetal/perinatal content
(congenital-anomaly screening, fetal monitoring, delivery planning for neonatal
outcomes). That is a deliberate scoping choice, not a bug. A later version could
tag those as `fetal_perinatal_relevant` instead of folding them into the core.
