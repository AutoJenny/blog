from flask import jsonify, current_app, request
from app.api import bp
from app import db
from sqlalchemy import text
import datetime
import psutil
import os
import requests
import time
import openai
from app.services.llm_service import ServiceAuth


def check_ollama_performance():
    """Check Ollama's performance for different operations."""
    ollama_url = current_app.config.get("OLLAMA_API_URL", "http://localhost:11434")
    performance = {
        "status": "healthy",
        "api_url": ollama_url,
        "operations": {},
        "benchmarks": {},
    }

    try:
        # Test model listing
        start_time = time.time()
        response = requests.get(f"{ollama_url}/api/tags")
        list_time = time.time() - start_time

        if response.status_code == 200:
            models = response.json().get("models", [])
            performance["available_models"] = [model["name"] for model in models]
            performance["operations"]["list_models"] = {
                "latency": round(list_time * 1000, 2),  # Convert to ms
                "status": "success",
            }

            # Select test models for benchmarking
            test_models = {
                "embedding": "nomic-embed-text:latest",  # Fast embedding model
                "completion": "mistral:latest",  # Fast completion model
            }

            # Test embedding performance
            start_time = time.time()
            embed_response = requests.post(
                f"{ollama_url}/api/embeddings",
                json={
                    "model": test_models["embedding"],
                    "prompt": "Test embedding performance",
                },
            )
            embed_time = time.time() - start_time

            if embed_response.status_code == 200:
                performance["benchmarks"]["embedding"] = {
                    "model": test_models["embedding"],
                    "latency": round(embed_time * 1000, 2),
                    "status": "success",
                }

            # Test completion performance with different lengths
            for length in ["short", "medium"]:
                prompt = (
                    "Hi"
                    if length == "short"
                    else "Write a brief paragraph about performance testing."
                )
                start_time = time.time()
                gen_response = requests.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": test_models["completion"],
                        "prompt": prompt,
                        "stream": False,
                        "raw": True,  # Get raw performance metrics
                    },
                )
                gen_time = time.time() - start_time

                if gen_response.status_code == 200:
                    performance["benchmarks"][f"{length}_completion"] = {
                        "model": test_models["completion"],
                        "prompt_length": len(prompt),
                        "latency": round(gen_time * 1000, 2),
                        "status": "success",
                    }

            # Test model load times (non-blocking)
            for model_type, model in test_models.items():
                start_time = time.time()
                load_response = requests.post(
                    f"{ollama_url}/api/show", json={"name": model}, timeout=2
                )
                load_time = time.time() - start_time

                if load_response.status_code == 200:
                    model_info = load_response.json()
                    performance["benchmarks"][f"{model_type}_model_info"] = {
                        "model": model,
                        "load_latency": round(load_time * 1000, 2),
                        "parameters": model_info.get("parameters"),
                        "format": model_info.get("format"),
                        "families": model_info.get("families", []),
                        "status": "success",
                    }

    except Exception as e:
        performance["status"] = "degraded"
        performance["error"] = str(e)

    return performance


def _get_client():
    """Get an authenticated client"""
    auth = current_app.config.get("OPENAI_AUTH_TOKEN")
    if not auth:
        raise ValueError("Authentication token not configured")
    return openai.OpenAI(default_headers={"Authorization": f"Bearer {auth}"})


@bp.route("/health/openai")
def check_openai():
    """Check OpenAI's performance and availability."""
    try:
        auth = current_app.config.get("OPENAI_AUTH_TOKEN")
        if not auth:
            raise ValueError("Authentication token not configured")

        client = openai.OpenAI(auth=ServiceAuth(auth))
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=5,
        )
        latency = (time.time() - start_time) * 1000  # Convert to ms

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "model": "gpt-3.5-turbo",
        }
    except Exception as e:
        current_app.logger.error(f"OpenAI health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e), "model": "gpt-3.5-turbo"}


def check_dependencies():
    """Check for outdated or deprecated dependencies."""
    try:
        import pkg_resources
        from packaging import version

        critical_packages = {
            "langchain": "0.3.23",
            "langchain-community": "0.3.21",
            "langchain-core": "0.3.55",
            "openai": "1.12.0",
        }

        dependency_status = {
            "status": "healthy",
            "outdated_packages": [],
            "deprecated_packages": [],
        }

        for package, min_version in critical_packages.items():
            try:
                installed = pkg_resources.get_distribution(package)
                if version.parse(installed.version) < version.parse(min_version):
                    dependency_status["outdated_packages"].append(
                        {
                            "package": package,
                            "installed": installed.version,
                            "required": min_version,
                        }
                    )
            except pkg_resources.DistributionNotFound:
                dependency_status["outdated_packages"].append(
                    {
                        "package": package,
                        "installed": "not found",
                        "required": min_version,
                    }
                )

        if dependency_status["outdated_packages"]:
            dependency_status["status"] = "degraded"

        return dependency_status
    except Exception as e:
        current_app.logger.error(f"Dependency check failed: {str(e)}")
        return {"status": "error", "error": str(e)}


@bp.route("/health")
def health_check():
    """Check the health of the application and its dependencies."""
    # Support both /api/health and /v1/health paths
    is_v1 = request.path.startswith("/v1/")

    # Basic response for v1 health check (for legacy support)
    if is_v1:
        return jsonify(
            {
                "status": "healthy",
                "version": "1.0.0",
                "timestamp": datetime.datetime.utcnow().isoformat(),
            }
        )

    # Full health check
    health_status = {
        "status": "healthy",
        "database": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": current_app.config.get("ENV", "production"),
        "debug_mode": current_app.debug,
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
        },
        "dependencies": check_dependencies(),
        "llm_services": {},
    }

    # Check database connection
    try:
        db.session.execute(text("SELECT 1"))
        health_status["database_details"] = {
            "uri": current_app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1],
            "pool_size": db.engine.pool.size(),
        }
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"

    # Check Ollama (primary LLM)
    health_status["llm_services"]["ollama"] = check_ollama_performance()
    if health_status["llm_services"]["ollama"]["status"] == "degraded":
        health_status["status"] = "degraded"

    # Check OpenAI (secondary LLM)
    health_status["llm_services"]["openai"] = check_openai()
    if health_status["llm_services"]["openai"].get("status") == "unhealthy":
        health_status["status"] = "degraded"

    # Overall status determination
    if health_status["dependencies"]["status"] == "degraded":
        health_status["status"] = "degraded"

    response = jsonify(health_status)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response
