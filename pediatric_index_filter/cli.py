"""Command-line interface: apply the pediatric index-patient filter to any
CSV or Parquet file of questions.

Example
-------
    python -m pediatric_index_filter --input questions.csv \
        --text-column question --context-column context \
        --output labeled.csv

Adds three columns to every row and prints a funnel (N in -> N pediatric):
    is_pediatric_index_patient   bool
    pediatric_reasons            pipe-joined reason keys
    pediatric_reason_detail      human-readable explanation
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import REASON_LABELS, pediatric_reasons


def _load(path: Path):
    import pandas as pd

    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _build_text(row, text_column: str, context_column: str | None) -> str:
    question = "" if row.get(text_column) is None else str(row.get(text_column) or "")
    if context_column:
        context = "" if row.get(context_column) is None else str(row.get(context_column) or "")
        parts = []
        if context.strip():
            parts.append(f"Context: {context.strip()}")
        if question.strip():
            parts.append(f"Question: {question.strip()}")
        return "\n\n".join(parts)
    return question


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="pediatric_index_filter",
        description="Keep questions whose primary clinical subject is a pediatric patient.",
    )
    p.add_argument("--input", required=True, type=Path, help="CSV or Parquet file of questions.")
    p.add_argument("--text-column", required=True, help="Column holding the question text.")
    p.add_argument("--context-column", default=None, help="Optional column with vignette/context text.")
    p.add_argument("--output", type=Path, default=None, help="Where to write the labeled file (default: <input>.labeled.csv).")
    p.add_argument(
        "--keep-pediatric-only",
        action="store_true",
        help="Write only the rows classified as pediatric index-patient.",
    )
    p.add_argument(
        "--include-adult-primary",
        action="store_true",
        help="Do NOT drop items whose index patient is an adult (default is to drop them).",
    )
    p.add_argument(
        "--pediatric-scope",
        action="store_true",
        help="Assert the whole input is pediatric-scoped (relaxes the clinical-context requirement on bare child terms).",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.input.exists():
        print(f"error: input not found: {args.input}", file=sys.stderr)
        return 2

    df = _load(args.input)
    if args.text_column not in df.columns:
        print(f"error: --text-column {args.text_column!r} not in {list(df.columns)}", file=sys.stderr)
        return 2

    reasons_col, flag_col, detail_col = "pediatric_reasons", "is_pediatric_index_patient", "pediatric_reason_detail"
    reason_lists = [
        pediatric_reasons(
            _build_text(row, args.text_column, args.context_column),
            exclude_adult_primary_subject=not args.include_adult_primary,
            pediatric_scope=args.pediatric_scope,
        )
        for _, row in df.iterrows()
    ]
    df[flag_col] = [bool(r) for r in reason_lists]
    df[reasons_col] = ["|".join(r) for r in reason_lists]
    df[detail_col] = ["; ".join(REASON_LABELS[k] for k in r) for r in reason_lists]

    n_in = len(df)
    n_ped = int(df[flag_col].sum())
    out_df = df[df[flag_col]] if args.keep_pediatric_only else df
    out_path = args.output or args.input.with_suffix("").with_name(args.input.stem + ".labeled.csv")
    out_df.to_csv(out_path, index=False)

    pct = (100.0 * n_ped / n_in) if n_in else 0.0
    print(f"{n_in} questions in -> {n_ped} pediatric index-patient ({pct:.1f}%)")
    print(f"wrote {len(out_df)} rows to {out_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
