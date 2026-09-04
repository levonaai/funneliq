# Work Package 4: Super-Customer Score Findings

Target: `referred` (binary - did the customer refer someone else). Rows used: 3459. CatBoost only, using its native categorical handling for a new `budget_tier` feature (Low/Medium/High, no manual encoding). Stratified 5-fold CV for every grid point.

## Hyperparameter search

| learning_rate | depth | iterations | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|---|---|
| 0.03 | 4 | 200 | 0.826 | 0.794 | 0.743 | 0.768 | 0.873 |
| 0.1 | 4 | 200 | 0.820 | 0.772 | 0.760 | 0.766 | 0.871 |
| 0.05 | 4 | 200 | 0.824 | 0.789 | 0.744 | 0.766 | 0.873 |
| 0.05 | 6 | 400 | 0.819 | 0.768 | 0.763 | 0.765 | 0.871 |
| 0.05 | 4 | 400 | 0.821 | 0.779 | 0.752 | 0.765 | 0.872 |
| 0.03 | 6 | 400 | 0.821 | 0.778 | 0.751 | 0.765 | 0.873 |
| 0.03 | 4 | 400 | 0.822 | 0.786 | 0.744 | 0.764 | 0.874 |
| 0.05 | 6 | 200 | 0.821 | 0.780 | 0.749 | 0.764 | 0.873 |
| 0.03 | 6 | 200 | 0.822 | 0.789 | 0.738 | 0.763 | 0.874 |
| 0.1 | 6 | 200 | 0.813 | 0.758 | 0.762 | 0.760 | 0.867 |
| 0.1 | 4 | 400 | 0.813 | 0.758 | 0.759 | 0.758 | 0.867 |
| 0.1 | 6 | 400 | 0.809 | 0.749 | 0.760 | 0.755 | 0.861 |

**Best configuration** (learning_rate=0.03, depth=4, iterations=200): F1=0.768, ROC-AUC=0.873.

This configuration is retrained on the full cleaned dataset and saved to `models\super_customer_score.cbm` for the scoring pipeline (`app/scoring.py`, `POST /api/score-lead`).

**Caveat**: this dataset's rows are campaign/cohort aggregates, not individual-lead records, so several training features (e.g. `closed`, `purchased`) describe outcomes a genuinely new lead wouldn't have yet. See this module's docstring.
