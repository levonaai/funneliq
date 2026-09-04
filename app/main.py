from fastapi import Depends, FastAPI

from app.auth import CurrentUser, get_current_user

app = FastAPI(title="FunnelIQ API")


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
