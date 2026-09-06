from fastapi import FastAPI

app = FastAPI(
    title="Greenhouse API",
    version="0.1.0",
)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Greenhouse API is running"}
