# Work Package 3: Upsell Classification Findings

Target: `upsell` (binary). Rows used: 3459. Stratified 5-fold cross-validation, metrics averaged across folds.

## Class imbalance

- `upsell = 0`: 2007 (58.0%)
- `upsell = 1`: 1452 (42.0%)
- Moderate imbalance (42.0% minority class) - handled via `scale_pos_weight` (XGBoost, LightGBM) / `auto_class_weights="Balanced"` (CatBoost), computed fresh from each training fold.

## Model comparison (Accuracy / Precision / Recall / F1 / ROC-AUC)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Majority-class baseline | 0.580 | 0.000 | 0.000 | 0.000 | 0.500 |
| Business heuristic (LTV high & CAC low) | 0.642 | 0.681 | 0.279 | 0.395 | 0.592 |
| XGBoost | 0.813 | 0.774 | 0.783 | 0.778 | 0.884 |
| LightGBM | 0.811 | 0.767 | 0.788 | 0.777 | 0.883 |
| CatBoost | 0.815 | 0.772 | 0.793 | 0.782 | 0.887 |

Best ML model by F1: **CatBoost** (0.782), vs. the best baseline's 0.395 - the ML models meaningfully beat both the majority-class and business-heuristic baselines.

## Feature importance (top 8 per model)

### XGBoost

| Feature | Importance |
|---|---|
| `referred` | 97.6 |
| `ltv_months` | 14.5 |
| `purchased` | 9.4 |
| `customer_acquisition_cost` | 6.1 |
| `ad_budget` | 4.8 |
| `not_closed` | 2.6 |
| `num_leads` | 2.6 |
| `followup_2` | 2.6 |

### LightGBM

| Feature | Importance |
|---|---|
| `referred` | 9498.9 |
| `ltv_months` | 6958.6 |
| `customer_acquisition_cost` | 2377.2 |
| `purchased` | 1407.1 |
| `num_leads` | 736.4 |
| `leads_not_answered` | 662.1 |
| `followup_2` | 600.7 |
| `leads_answered` | 557.8 |

### CatBoost

| Feature | Importance |
|---|---|
| `ltv_months` | 23.7 |
| `purchased` | 22.0 |
| `referred` | 16.0 |
| `customer_acquisition_cost` | 10.7 |
| `calls_to_closed` | 4.8 |
| `leads_not_answered` | 2.9 |
| `num_leads` | 2.7 |
| `followup_1` | 2.2 |
