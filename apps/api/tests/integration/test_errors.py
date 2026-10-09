from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.middleware.request_id import RequestIDMiddleware


def create_test_app():
    test_app = FastAPI()

    test_app.add_middleware(
        RequestIDMiddleware
    )

    test_app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    test_app.add_exception_handler(
        404,
        http_exception_handler,
    )

    test_app.add_exception_handler(
        422,
        validation_exception_handler,
    )

    @test_app.get("/error")
    async def error():
        raise RuntimeError(
            "Something went wrong"
        )

    return test_app


def test_internal_error_does_not_expose_exception():
    app = create_test_app()

    client = TestClient(
        app,
        raise_server_exceptions=False,
    )

    response = client.get(
        "/error"
    )

    assert response.status_code == 500

    data = response.json()

    assert data["error"]["code"] == (
        "INTERNAL_SERVER_ERROR"
    )

    assert data["error"]["message"] == (
        "An unexpected error occurred"
    )

    assert "Something went wrong" not in (
        response.text
    )

    assert data["error"]["request_id"]