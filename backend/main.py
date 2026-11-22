from fastapi import FastAPI

app = FastAPI(
    title="api test",
    version="0.1.0",
)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "fastapi"}