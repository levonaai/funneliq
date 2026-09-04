"""Generate the Work Package 1 (EDA) findings report.

Reads the local funnel_marketing_data.csv (never committed - see
.gitignore) and writes docs/eda_findings.md. Re-run any time the CSV
changes:

    python -m analysis.eda
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from analysis.data_cleaning import (
    BUDGET_TIER_HIGH,
    BUDGET_TIER_LOW,
    BUDGET_TIER_MEDIUM,
    BUDGET_TIER_UNDEFINED,
    CleaningReport,
    assign_budget_tier,
    clean,
    load_raw,
)

CSV_PATH = "funnel_marketing_data.csv"
OUTPUT_PATH = Path("docs/eda_findings.md")
TIER_ORDER = [BUDGET_TIER_LOW, BUDGET_TIER_MEDIUM, BUDGET_TIER_HIGH, BUDGET_TIER_UNDEFINED]


def correlation_with_profit(df: pd.DataFrame) -> pd.Series:
    numeric = df.select_dtypes("number").copy()
    numeric["referred"] = df["referred"].map({"Yes": 1, "No": 0})
    corr = numeric.corr(numeric_only=True)["cumulative_profit"].drop("cumulative_profit")
    return corr.reindex(corr.abs().sort_values(ascending=False).index)


def conversion_by_budget_tier(df: pd.DataFrame) -> pd.DataFrame:
    tiered = df.assign(budget_tier=assign_budget_tier(df["ad_budget"]))
    tiered["conversion_rate"] = tiered["closed"] / tiered["num_leads"]
    tiered["leads_per_1000_budget"] = tiered["num_leads"] / tiered["ad_budget"] * 1000

    summary = tiered.groupby("budget_tier").agg(
        rows=("ad_budget", "size"),
        avg_ad_budget=("ad_budget", "mean"),
        avg_num_leads=("num_leads", "mean"),
        avg_leads_per_1000_budget=("leads_per_1000_budget", "mean"),
        avg_conversion_rate=("conversion_rate", "mean"),
    )
    return summary.reindex([t for t in TIER_ORDER if t in summary.index])


def render_report(report: CleaningReport, corr: pd.Series, tiers: pd.DataFrame) -> str:
    lines = ["# Work Package 1: EDA & Data Cleaning Findings", ""]

    lines += [
        "## Data cleaning",
        "",
        f"- Raw rows: {report.raw_rows}",
        f"- Exact duplicate rows dropped: {report.duplicates_dropped}",
        (
            f"- `cumulative_profit` filled with 0.0 (non-purchasers, matching "
            f"the 335/337 pattern for that group): {report.profit_zero_filled}"
        ),
        (
            f"- Rows dropped for a genuinely missing `cumulative_profit` or "
            f"`ltv_months` with no safe default: {report.rows_dropped_missing_target}"
        ),
        f"- **Clean rows used below: {report.clean_rows}**",
        "",
        "See `analysis/data_cleaning.py` for the exact, reproducible rules.",
        "",
    ]

    lines += ["## Correlation with `cumulative_profit`", ""]
    lines += ["| Feature | Correlation |", "|---|---|"]
    for feature, value in corr.items():
        lines.append(f"| `{feature}` | {value:+.3f} |")
    lines.append("")

    top = corr.index[0]
    lines += [
        (
            f"Strongest relationship: `{top}` ({corr.iloc[0]:+.3f}). Features "
            "with correlation near 0 (e.g. `purchased`/`upsell` flags once "
            "already conditioned on conversion) contribute little on their "
            "own and are candidates to deprioritize in later feature selection."
        ),
        "",
    ]

    lines += ["## Conversion analysis by ad budget tier", ""]
    lines += [
        (
            "Conversion rate = `closed / num_leads`. Tiers per the PRD: Low "
            "(<=1500), Medium (2000-5000), High (>5000); rows with a budget "
            "strictly between 1500 and 2000 fall outside the PRD's tier "
            "definition and are reported separately rather than forced into "
            "a neighboring bucket."
        ),
        "",
        "| Budget tier | Rows | Avg budget | Avg leads | Avg leads per $1,000 | Avg conversion rate |",
        "|---|---|---|---|---|---|",
    ]
    for tier_name, row in tiers.iterrows():
        lines.append(
            f"| {tier_name} | {int(row['rows'])} | {row['avg_ad_budget']:,.0f} | "
            f"{row['avg_num_leads']:.1f} | {row['avg_leads_per_1000_budget']:.2f} | "
            f"{row['avg_conversion_rate']:.1%} |"
        )
    lines.append("")

    defined_tiers = tiers.loc[[t for t in [BUDGET_TIER_LOW, BUDGET_TIER_MEDIUM, BUDGET_TIER_HIGH] if t in tiers.index]]
    leads_per_1000 = defined_tiers["avg_leads_per_1000_budget"]
    is_diminishing = leads_per_1000.iloc[0] > leads_per_1000.iloc[-1] and leads_per_1000.is_monotonic_decreasing
    verdict = (
        "Yes - leads generated per marketing dollar decline as budget tier "
        "increases, i.e. diminishing returns."
        if is_diminishing
        else "Not strictly monotonic across tiers - returns do not fall "
        "cleanly with budget size in this dataset."
    )
    lines += [
        f"**Diminishing returns on ad spend?** {verdict} Leads-per-$1,000 by "
        "tier: "
        + ", ".join(f"{name}={value:.2f}" for name, value in leads_per_1000.items())
        + ".",
        "",
    ]

    conversion_rates = defined_tiers["avg_conversion_rate"]
    peak_tier = conversion_rates.idxmax()
    if peak_tier != defined_tiers.index[-1]:
        lines += [
            (
                f"**Conversion rate is not monotonic with budget**: it peaks "
                f"at {peak_tier} ({conversion_rates.loc[peak_tier]:.1%}) "
                f"rather than at the highest budget tier "
                f"({defined_tiers.index[-1]}, {conversion_rates.iloc[-1]:.1%}). "
                "More ad spend buys more raw leads, but not proportionally "
                "more closed deals - high-budget campaigns appear to bring in "
                "a lower-quality or harder-to-close lead mix."
            ),
            "",
        ]

    return "\n".join(lines)


def main() -> None:
    if not Path(CSV_PATH).exists():
        print(f"CSV not found at '{CSV_PATH}' - EDA needs the local dataset.", file=sys.stderr)
        sys.exit(1)

    raw = load_raw(CSV_PATH)
    clean_df, report = clean(raw)

    corr = correlation_with_profit(clean_df)
    tiers = conversion_by_budget_tier(clean_df)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(render_report(report, corr, tiers), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH} ({report.clean_rows} clean rows).")


if __name__ == "__main__":
    main()
