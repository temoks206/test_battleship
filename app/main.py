from fastapi import FastAPI

app = FastAPI(title="Battleship Service")


@app.get("/health")
def health_check():
    return {"status": "OK"}