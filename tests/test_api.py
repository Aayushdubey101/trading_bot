import pytest
from fastapi.testclient import TestClient
from bot.api.server import app

client = TestClient(app)

def test_account_endpoint_mocked(mocker):
    # Mock the client dependency
    mock_client = mocker.AsyncMock()
    mock_client.get_account.return_value = {"assets": []}
    
    # Patch the state
    from bot.api import server
    server.state.client = mock_client
    from bot.api import routes
    routes.client_instance = mock_client
    
    response = client.get("/account")
    assert response.status_code == 200
    assert response.json() == {"assets": []}
