# Work Package 5: Follow-Up Funnel Analysis Findings

Rows used: 3459.

## Funnel stage totals

| Stage | Total | Drop-off from prior stage |
|---|---|---|
| `followup_1` | 75,967 | - |
| `followup_2` | 56,467 | 25.7% |
| `followup_3` | 45,962 | 18.6% |
| `followup_4` | 41,194 | 10.4% |
| `followup_5` | 29,157 | 29.2% |

## Q1: Where does anomalous drop-off occur?

**`followup_4` -> `followup_5`** (29.2% drop-off). Every earlier transition shrinks (attrition falls as the remaining cohort gets more engaged) - this is the one transition where drop-off jumps back up instead of continuing to fall, breaking the expected pattern.

## Q2: Average follow-up cycles for closed deals

**5.0 follow-up cycles**, always. Verified directly: `followup_5 == not_closed + closed` holds for 100% of rows in this dataset - a deal is only ever recorded as closed (or not_closed) after completing all five follow-ups.

## Policy recommendation

Since no deal can close before completing all 5 follow-ups, the `followup_4` -> `followup_5` transition is where the most-engaged remaining leads are being lost right before the point that determines whether they can close at all. **Recommendation**: pilot a change specifically at this touchpoint (e.g. a different channel, a personal call instead of an automated message, or a shortened gap before it) for a sample of leads, and compare their stage-5 survival rate against the current process before rolling out a change to the full funnel.
