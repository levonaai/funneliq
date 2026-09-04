from fastapi import FastAPI

app = FastAPI(title="FunnelIQ API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Hello from FunnelIQ"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
