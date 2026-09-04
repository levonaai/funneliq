# FunnelIQ - Capstone Project PRD & Specifications

## Project Overview
FunnelIQ is a hands-on, self-guided capstone project designed to transform raw marketing and sales data from **Northbound Media** into a deployed, secure, and production-ready Business Intelligence (BI) tool. 

The project leverages the dataset `funnel_marketing_data.csv` (~3,500 records) and is divided into two core layers:
1. **Infrastructure Pillars** (Version control, database & auth, cloud deployment).
2. **Analytical Work Packages** (Data cleaning, ML modeling with Gradient Boosting, business intelligence tools).

---

## Part A: Infrastructure Pillars

> **Strategy Note:** Deploy a minimal empty boilerplate first (e.g., a simple FastAPI/Flask app returning `"Hello"` with a health check) before adding complex models and business logic.

### Pillar 1: Version Control & Automation (GitHub)
* **Repository Setup:** Public repository containing a structured `README.md` with an overview, architecture diagram, execution instructions, and a link to the live app.
* **Git Workflow:** Proper branch management using feature branches, at least one Pull Request (PR), and a clean, descriptive commit history.
* **Security & Quality:**
  * Strict `.gitignore` preventing exposure of API keys, `.env` environment files, or raw dataset files.
  * **CI/CD:** GitHub Actions pipeline running automatic code linting and unit testing on every `push`.

### Pillar 2: Database & Authentication (Supabase)
* **Data Management:**
  * Provision a Supabase project and define a relational schema stored as `schema.sql` in the repository.
  * Automated and reproducible Python ingestion script to load `funnel_marketing_data.csv` into Postgres (no manual uploads).
* **Database Security:** Enable Row Level Security (RLS) to restrict data access to authenticated users only.
* **Authentication Flow:**
  * Secure Login UI (Email/Password at minimum).
  * Frontend uses Supabase `public anon key`.
  * Backend verifies user `JWT` and securely holds the Supabase `Service Role` key.

### Pillar 3: Cloud Deployment (Railway)
* Public deployment of the Backend API (FastAPI / Flask) and Dashboard application.
* Connect GitHub repository to Railway for automated Continuous Deployment (CD) on push.
* Set all sensitive keys as Environment Variables in the Railway interface.
* Expose a dedicated `/health` endpoint for uptime check.

---

## Part B: Analytical Work Packages (ML & Insights)

Analytical models are built using Gradient Boosting algorithms (**XGBoost**, **LightGBM**, **CatBoost**).

### Work Package 1: Exploratory Data Analysis (EDA) & Data Cleaning
* **Data Ingestion & Cleaning:** Deterministic handling of missing values and incomplete rows.
* **Correlation Analysis:** Examine feature correlations relative to `cumulative_profit`.
* **Conversion Analysis:** Map conversion rates (`closed / num_leads`) and analyze return curves between advertising budget (`ad_budget`) and leads generated (`num_leads`) across three budget tiers:
  * Low: $\le 1500$
  * Medium: $2000 - 5000$
  * High: $> 5000$
* **Deliverable:** Summary findings documented in the `README.md` or a dedicated `/docs` directory.

### Work Package 2: LTV Regression Model (Customer Lifetime in Months)
* **Task:** Regression modeling targeting `ltv_months`.
* **Modeling & Evaluation:** Train XGBoost, LightGBM, and CatBoost using 5-Fold Cross-Validation evaluated on **RMSE** and **$R^2$**.
* **Feature Importance:** Extract and compare key driving features across all models.
* ⚠️ **CRITICAL DATA LEAKAGE WARNING:** Do **NOT** use `cumulative_profit` as an input feature for predicting LTV. `cumulative_profit` represents data accumulated after the customer lifecycle, causing severe target leakage.

### Work Package 3: Upsell Probability (Binary Classification)
* **Task:** Binary classification targeting `upsell`.
* **Class Imbalance:** Check for imbalance and handle accordingly (e.g., `scale_pos_weight` or class weighting).
* **Metrics:** Train with Stratified 5-Fold CV and report: **Accuracy, Precision, Recall, F1-Score, ROC-AUC** against a majority-class baseline.
* **Business Heuristic Comparison:** Construct a rule-based baseline (e.g., *"If LTV > X and CAC < Y then Upsell = True"*) and compare heuristic accuracy against ML model performance.

### Work Package 4: Super-Customer Score
* **Task:** Classification model targeting customer referrals (`referred`).
* **Feature Engineering:** Create a categorical budget tier feature (Low, Medium, High) utilizing CatBoost's native categorical handling.
* **Hyperparameter Tuning:** Perform Grid/Random Search for `learning_rate`, `depth`, and `iterations`.
* **Scoring Pipeline:** Build a backend function returning a `0–100` probability score for new leads indicating their likelihood to become a "Super-Customer" (high retention, high upsell, high referral).

### Work Package 5: Follow-Up Funnel Analysis
* **Task:** Analyze transaction drop-off rates across follow-up stages (`followup_1` through `followup_5`).
* **Key Questions:**
  1. At which follow-up stage does anomalous drop-off behavior occur?
  2. What is the average number of follow-up cycles for successfully `closed` deals?
* **Deliverable:** Visual funnel diagram in the dashboard accompanied by actionable, data-backed policy recommendations.

### Work Package 6: Budget Optimization Simulator
* **Task:** Optimize monthly budget allocation for a ₪50,000 budget.
* **Simulator Logic:** Build a prediction tool for `cumulative_profit` based on budget allocation strategies (e.g., broad distribution of small budgets vs. concentrated high-budget campaigns).
* **Deliverable:** Interactive user interface allowing scenario testing to compare total profit outcomes under different distribution strategies.

---

## Part C: Final Deliverables Checklists

- [ ] **GitHub Repository:** Clean commit history, `README.md`, `schema.sql`, and active GitHub Actions CI/CD.
- [ ] **Deployed Application (Railway):** Functional API and Dashboard serving ML models and analytics.
- [ ] **Authentication:** Protected application layer requiring Supabase Auth login.
- [ ] **Analytical Report (`REPORT.md`):** Complete documentation of data insights, model performance comparisons, business rules, and recommendations.