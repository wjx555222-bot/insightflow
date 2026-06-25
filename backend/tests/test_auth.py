"""Basic tests for auth endpoints."""


def test_root_endpoint(client):
    """Root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "InsightFlow API"
    assert data["version"] == "1.0.0"


def test_auth_me(client):
    """GET /auth/me returns the current user."""
    response = client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["full_name"] == "Test Admin"
    assert data["role"]["name"] == "admin"


def test_dashboard_summary(client):
    """GET /dashboard/summary returns KPI data."""
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_orders" in data
    assert "total_customers" in data


def test_orders_list_empty(client):
    """GET /orders returns empty list when no orders."""
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_customers_list_empty(client):
    """GET /customers returns empty list when no customers."""
    response = client.get("/customers")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_products_list_empty(client):
    """GET /products returns empty list when no products."""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


def test_create_customer(client):
    """POST /customers creates a new customer."""
    response = client.post("/customers", json={
        "name": "Test Corp",
        "company": "Test Company",
        "email": "test@corp.com",
        "region": "North",
        "customer_type": "enterprise",
    })
    assert response.status_code in (200, 201)
    data = response.json()
    assert data["name"] == "Test Corp"
    assert data["company"] == "Test Company"


def test_create_and_get_order(client):
    """Create a customer, then an order, then verify."""
    # Create customer first
    cust = client.post("/customers", json={"name": "Order Customer"})
    assert cust.status_code in (200, 201)
    cust_id = cust.json()["id"]

    # Create a product
    prod = client.post("/products", json={
        "name": "Test Widget",
        "unit_price": 29.99,
        "current_stock": 100,
    })
    assert prod.status_code in (200, 201)
    prod_id = prod.json()["id"]

    # Create order
    order = client.post("/orders", json={
        "customer_id": cust_id,
        "items": [{"product_id": prod_id, "quantity": 2, "unit_price": 29.99}],
        "region": "North",
        "salesperson": "Test Rep",
    })
    assert order.status_code in (200, 201)
    data = order.json()
    assert data["total_amount"] == 59.98
    assert len(data["items"]) == 1

    # Get the order
    get_resp = client.get(f"/orders/{data['id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == data["id"]
