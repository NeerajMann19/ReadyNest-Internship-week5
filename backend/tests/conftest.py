import pytest
import httpx
from uuid import uuid4
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.main import app
from app.db import session as db_session

# Re-bind the async_session maker to an engine with NullPool to prevent connection pool exhaustion during tests
test_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool
)

db_session.async_session = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="module")
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture(scope="module")
async def auth_headers(client):
    email = f"user_{uuid4().hex[:6]}@test.com"
    password = "secret_password_123"
    
    # Register
    reg = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    
    # Login
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
async def other_auth_headers(client):
    email = f"other_{uuid4().hex[:6]}@test.com"
    password = "other_secret_password_123"
    
    # Register
    reg = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200
    
    # Login
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_csv_content():
    return "id,name,score,age\n1,Alice,95,20\n2,Bob,88,21\n3,Charlie,92,22\n4,David,85,23"

@pytest.fixture
def large_csv_content():
    headers = "id,name,score,age\n"
    rows = []
    for i in range(10100):
        rows.append(f"{i},User{i},{80 + (i % 21)},{20 + (i % 29)}")
    return headers + "\n".join(rows)
