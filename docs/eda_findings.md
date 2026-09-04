# Work Package 1: EDA & Data Cleaning Findings

## Data cleaning

- Raw rows: 3500
- Exact duplicate rows dropped: 10
- `cumulative_profit` filled with 0.0 (non-purchasers, matching the 335/337 pattern for that group): 2
- Rows dropped for a genuinely missing `cumulative_profit` or `ltv_months` with no safe default: 31
- **Clean rows used below: 3459**

See `analysis/data_cleaning.py` for the exact, reproducible rules.

## Correlation with `cumulative_profit`

| Feature | Correlation |
|---|---|
| `ltv_months` | +0.845 |
| `upsell` | +0.651 |
| `referred` | +0.583 |
| `calls_to_closed` | -0.558 |
| `purchased` | +0.364 |
| `customer_acquisition_cost` | -0.255 |
| `leads_not_answered` | -0.250 |
| `ad_budget` | -0.212 |
| `closed` | +0.206 |
| `not_closed` | -0.155 |
| `num_leads` | -0.141 |
| `followup_1` | -0.051 |
| `leads_answered` | -0.050 |
| `followup_2` | -0.050 |
| `followup_3` | -0.049 |
| `followup_4` | -0.047 |
| `followup_5` | -0.045 |
| `calls_to_not_closed` | +0.038 |

Strongest relationship: `ltv_months` (+0.845). Features with correlation near 0 (e.g. `purchased`/`upsell` flags once already conditioned on conversion) contribute little on their own and are candidates to deprioritize in later feature selection.

## Conversion analysis by ad budget tier

Conversion rate = `closed / num_leads`. Tiers per the PRD: Low (<=1500), Medium (2000-5000), High (>5000); rows with a budget strictly between 1500 and 2000 fall outside the PRD's tier definition and are reported separately rather than forced into a neighboring bucket.

| Budget tier | Rows | Avg budget | Avg leads | Avg leads per $1,000 | Avg conversion rate |
|---|---|---|---|---|---|
| Low (<=1500) | 763 | 1,085 | 20.3 | 19.71 | 4.6% |
| Medium (2000-5000) | 1702 | 3,212 | 39.6 | 12.88 | 8.2% |
| High (>5000) | 994 | 9,926 | 77.8 | 8.28 | 5.4% |

**Diminishing returns on ad spend?** Yes - leads generated per marketing dollar decline as budget tier increases, i.e. diminishing returns. Leads-per-$1,000 by tier: Low (<=1500)=19.71, Medium (2000-5000)=12.88, High (>5000)=8.28.

**Conversion rate is not monotonic with budget**: it peaks at Medium (2000-5000) (8.2%) rather than at the highest budget tier (High (>5000), 5.4%). More ad spend buys more raw leads, but not proportionally more closed deals - high-budget campaigns appear to bring in a lower-quality or harder-to-close lead mix.
