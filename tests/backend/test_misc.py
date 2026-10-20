"""Tests for health checks and the request-size guard."""

from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "docs" in resp.json()


def test_oversized_request_rejected(client):
    # A body larger than the 1 MB limit is rejected before routing.
    big = b"x" * 1_100_000
    resp = client.post("/auth/login", content=big)
    assert resp.status_code == 413
