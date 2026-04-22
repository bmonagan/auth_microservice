"""
Test suite for application initialization and API structure.
"""


class TestAPIStructure:
    """Test the API app structure and endpoints."""

    def test_openapi_available(self, client):
        """OpenAPI specification is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui_available(self, client):
        """Swagger UI documentation is available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()

    def test_redoc_available(self, client):
        """ReDoc alternative documentation is available."""
        response = client.get("/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()
    
    def test_auth_endpoints_documented(self, client):
        """Auth endpoints are present in OpenAPI spec."""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})
        
        assert "/auth/register" in paths
        assert "/auth/login" in paths
    
    def test_user_endpoints_documented(self, client):
        """User endpoints are present in OpenAPI spec."""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data.get("paths", {})
        
        assert "/users/me" in paths
        assert "/users/me/sessions" in paths
    
    def test_app_info_in_openapi(self, client):
        """API info is properly set in OpenAPI spec."""
        response = client.get("/openapi.json")
        data = response.json()
        info = data.get("info", {})
        
        assert "title" in info
        assert "version" in info


class TestAPIHealth:
    """Test basic API health checks."""
    
    def test_root_endpoint_exists(self, client):
        """API root endpoint exists (even if just 404)."""
        response = client.get("/")
        # Either 404 or 200, just checking no 500 errors
        assert response.status_code in [200, 404]
    
    def test_invalid_endpoint_returns_404(self, client):
        """Invalid endpoints return 404, not 500."""
        response = client.get("/invalid/endpoint/that/does/not/exist")
        assert response.status_code == 404

    def test_live_health_endpoint(self, client):
        """Liveness endpoint should always return alive."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json().get("status") == "alive"

    def test_health_endpoint_includes_checks(self, client):
        """Health endpoint returns status and dependency checks."""
        response = client.get("/health")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]

    def test_ready_endpoint_includes_checks(self, client):
        """Readiness endpoint should report dependency checks."""
        response = client.get("/health/ready")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "database" in data["checks"]
        assert "redis" in data["checks"]
