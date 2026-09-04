# Work Package 2: LTV Regression Findings

Target: `ltv_months` (continuous). Rows used: 3459. 5-fold cross-validation, metrics averaged across folds.

**Data leakage guard**: `cumulative_profit` is intentionally excluded from every feature set - it is only known after a customer's lifecycle ends, so using it here would leak the answer and produce a model that looks perfect in training but is useless in production.

## Model comparison (5-fold CV)

| Model | RMSE (mean ± std) | R² (mean ± std) |
|---|---|---|
| XGBoost | 2.909 ± 0.194 | 0.945 ± 0.008 |
| LightGBM | 2.869 ± 0.175 | 0.946 ± 0.007 |
| CatBoost | 2.873 ± 0.180 | 0.946 ± 0.007 |

Best by RMSE: **LightGBM** (2.869).

## Feature importance (top 8 per model)

### XGBoost

| Feature | Importance |
|---|---|
| `closed` | 8097.4 |
| `calls_to_closed` | 7730.4 |
| `ad_budget` | 153.5 |
| `upsell` | 59.6 |
| `customer_acquisition_cost` | 33.8 |
| `referred` | 29.3 |
| `leads_not_answered` | 24.2 |
| `followup_4` | 20.9 |

### LightGBM

| Feature | Importance |
|---|---|
| `calls_to_closed` | 3101075.6 |
| `closed` | 1011711.9 |
| `ad_budget` | 29322.9 |
| `num_leads` | 13080.5 |
| `customer_acquisition_cost` | 10633.6 |
| `leads_not_answered` | 7408.6 |
| `upsell` | 5961.4 |
| `leads_answered` | 5300.2 |

### CatBoost

| Feature | Importance |
|---|---|
| `calls_to_closed` | 66.4 |
| `customer_acquisition_cost` | 11.0 |
| `followup_3` | 3.6 |
| `followup_4` | 3.4 |
| `ad_budget` | 3.2 |
| `closed` | 3.1 |
| `followup_2` | 2.4 |
| `num_leads` | 2.0 |
