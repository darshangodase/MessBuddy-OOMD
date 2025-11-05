"""
Authentication tests.
Demonstrates OOP testing with pytest and async support.
"""
import pytest
from httpx import AsyncClient
from app.main import app
from app.models.user import User
from app.db import init_db, close_db


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Initialize database for testing."""
    await init_db()
    yield
    await close_db()


@pytest.fixture
async def client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_signup_success(client):
    """
    Test successful user signup.
    
    OOP Testing: Tests AuthService through router endpoint
    """
    response = await client.post(
        "/api/auth/signup",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "login_role": "User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == "testuser"
    assert "password" not in data["user"]
    
    # Cleanup
    user = await User.find_one({"username": "testuser"})
    if user:
        await user.delete()


@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    """Test signup with duplicate email."""
    # Create first user
    await client.post(
        "/api/auth/signup",
        json={
            "username": "user1",
            "email": "duplicate@example.com",
            "password": "password123",
            "login_role": "User"
        }
    )
    
    # Try to create second user with same email
    response = await client.post(
        "/api/auth/signup",
        json={
            "username": "user2",
            "email": "duplicate@example.com",
            "password": "password123",
            "login_role": "User"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()
    
    # Cleanup
    user = await User.find_one({"email": "duplicate@example.com"})
    if user:
        await user.delete()


@pytest.mark.asyncio
async def test_signin_success(client):
    """Test successful signin."""
    # Create user
    await client.post(
        "/api/auth/signup",
        json={
            "username": "signintest",
            "email": "signin@example.com",
            "password": "password123",
            "login_role": "User"
        }
    )
    
    # Signin
    response = await client.post(
        "/api/auth/signin",
        json={
            "username": "signintest",
            "password": "password123",
            "login_role": "User"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == "signintest"
    assert "token" in data
    
    # Cleanup
    user = await User.find_one({"username": "signintest"})
    if user:
        await user.delete()


@pytest.mark.asyncio
async def test_signin_invalid_credentials(client):
    """Test signin with invalid credentials."""
    response = await client.post(
        "/api/auth/signin",
        json={
            "username": "nonexistent",
            "password": "wrongpass",
            "login_role": "User"
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_mess_owner_signup_creates_mess(client):
    """
    Test that signing up as Mess Owner creates a mess.
    
    OOP Testing: Tests interaction between AuthService and MessService
    """
    response = await client.post(
        "/api/auth/signup",
        json={
            "username": "messowner",
            "email": "owner@example.com",
            "password": "password123",
            "login_role": "Mess Owner"
        }
    )
    
    assert response.status_code == 201
    assert response.json()["user"]["Login_Role"] == "Mess Owner"
    
    # Verify mess was created
    user = await User.find_one({"username": "messowner"})
    assert user is not None
    
    from app.models.mess import Mess
    mess = await Mess.find_one({"Owner_ID": user.id})
    assert mess is not None
    
    # Cleanup
    if mess:
        await mess.delete()
    if user:
        await user.delete()
