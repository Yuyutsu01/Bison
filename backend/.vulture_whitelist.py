# Whitelist file for Vulture dead code analyzer
# Suppresses false positives for framework hooks, FastAPI endpoints, and Pytest fixtures

lifespan  # FastAPI lifespan context manager entrypoint attribute
app  # FastAPI application instance referenced by Uvicorn / TestClient
health_check  # FastAPI REST API endpoint handler
_.health_check  # FastAPI endpoint handler attribute
