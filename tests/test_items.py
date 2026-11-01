"""
CRUD tests for the /items resource.

Checks:
  7.  create_item_returns_201
  8.  create_item_missing_name_returns_422
  9.  list_items_returns_list
  10. get_item_by_id
  11. get_nonexistent_item_returns_404
  12. update_item
  13. delete_item_returns_204
  14. delete_nonexistent_item_returns_404
"""


# ── Check 7 ───────────────────────────────────────────────────────────────────


def test_create_item_returns_201(client):
    """Creating a valid item must return HTTP 201 and the full item body."""
    payload = {"name": "Deploy pipeline", "description": "Set up CD", "status": "active"}
    response = client.post("/items/", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Deploy pipeline"
    assert body["id"] is not None
    assert "created_at" in body


# ── Check 8 ───────────────────────────────────────────────────────────────────


def test_create_item_missing_name_returns_422(client):
    """A request without a name field must be rejected with HTTP 422."""
    response = client.post("/items/", json={"description": "No name provided"})
    assert response.status_code == 422


# ── Check 9 ───────────────────────────────────────────────────────────────────


def test_list_items_returns_list(client):
    """GET /items/ must return a JSON object with an 'items' list and 'total'."""
    # Seed one item
    client.post("/items/", json={"name": "Seed item"})
    response = client.get("/items/")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)
    assert body["total"] >= 1


# ── Check 10 ──────────────────────────────────────────────────────────────────


def test_get_item_by_id(client):
    """GET /items/{id} must return the correct item."""
    created = client.post("/items/", json={"name": "Specific item"}).json()
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]
    assert response.json()["name"] == "Specific item"


# ── Check 11 ──────────────────────────────────────────────────────────────────


def test_get_nonexistent_item_returns_404(client):
    """Requesting an item that doesn't exist must return HTTP 404."""
    response = client.get("/items/999999")
    assert response.status_code == 404


# ── Check 12 ──────────────────────────────────────────────────────────────────


def test_update_item(client):
    """PUT /items/{id} must update the specified fields and return the item."""
    created = client.post("/items/", json={"name": "Old name"}).json()
    response = client.put(
        f"/items/{created['id']}", json={"name": "New name", "status": "inactive"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New name"
    assert body["status"] == "inactive"


# ── Check 13 ──────────────────────────────────────────────────────────────────


def test_delete_item_returns_204(client):
    """DELETE /items/{id} must return HTTP 204 and the item must no longer exist."""
    created = client.post("/items/", json={"name": "To be deleted"}).json()
    delete_response = client.delete(f"/items/{created['id']}")
    assert delete_response.status_code == 204
    get_response = client.get(f"/items/{created['id']}")
    assert get_response.status_code == 404


# ── Check 14 ──────────────────────────────────────────────────────────────────


def test_delete_nonexistent_item_returns_404(client):
    """Deleting an item that doesn't exist must return HTTP 404."""
    response = client.delete("/items/999999")
    assert response.status_code == 404
