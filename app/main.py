from fastapi import Depends, FastAPI
from pydantic import BaseModel

from app.auth import CurrentUser, get_current_user
from app.scoring import score_lead

app = FastAPI(title="FunnelIQ API")


class LeadFeatures(BaseModel):
    ad_budget: float
    num_leads: int
    leads_answered: int
    leads_not_answered: int
    followup_1: int
    followup_2: int
    followup_3: int
    followup_4: int
    followup_5: int
    not_closed: int
    closed: int
    calls_to_closed: int
    calls_to_not_closed: int
    customer_acquisition_cost: float
    ltv_months: float
    purchased: int
    upsell: int


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from FunnelIQ"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/me")
def read_current_user(current_user: CurrentUser = Depends(get_current_user)) -> dict:
    """Example protected route: requires a valid Supabase JWT."""
    return {"user_id": current_user.user_id, "email": current_user.email}


@app.post("/api/score-lead")
def score_lead_endpoint(
    lead: LeadFeatures, current_user: CurrentUser = Depends(get_current_user)
) -> dict:
    """Work Package 4: 0-100 'Super-Customer' likelihood score for a lead."""
    score = score_lead(lead.model_dump())
    return {"super_customer_score": score}
