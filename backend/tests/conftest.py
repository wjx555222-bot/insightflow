"""Shared test fixtures for InsightFlow backend tests."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.dependencies import get_current_user, get_db
from app.models.user import Role, User
from app.services.auth_service import hash_password, create_access_token


# In-memory SQLite for tests (shared cache so all connections see the same data)
TEST_DATABASE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    """Create tables, yield a session, then drop everything."""
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Create a test client with an overridden DB session and seeded roles."""
    # Seed roles
    for name in ("admin", "manager", "staff"):
        role = Role(name=name)
        db.add(role)
    db.commit()

    # Create test admin user
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    admin = User(
        email="admin@test.com",
        hashed_password=hash_password("password123"),
        full_name="Test Admin",
        role_id=admin_role.id,
        is_active=True,
    )
    db.add(admin)
    db.commit()

    # Build a minimal FastAPI app for testing
    from app.main import app

    app.dependency_overrides[get_db] = override_get_db

    # Override current user to always return admin
    def override_user():
        return admin

    app.dependency_overrides[get_current_user] = override_user

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(db):
    """Return a valid JWT for the test admin user."""
    admin = db.query(User).filter(User.email == "admin@test.com").first()
    return create_access_token(data={"sub": str(admin.id)})
