"""FastAPI application entry point (stub)."""
from fastapi import FastAPI


def create_app():
    app = FastAPI()
    @app.get("/")
    def root():
        return {"status": "ok"}

    return app


app = create_app()
