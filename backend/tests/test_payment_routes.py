from app.main import create_app


def test_unprotected_payment_stub_route_is_not_registered():
    app = create_app()
    routes = {route.path for route in app.routes}

    assert "/api/v1/payments/webhook" not in routes
    assert "/api/v1/payments/webhook/mp" in routes
