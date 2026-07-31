from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Generator

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import OperationalError
from fastapi.testclient import TestClient
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import create_session_factory
from app.dependencies.deps import get_app_settings, get_db
from app.dependencies.storage import get_optional_storage_service, get_storage_service
from app.main import app
from app.services.storage_service import UploadResult

ROOT_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_NAME = "kara_orders_test_stage3"


def _database_url(database_url: str, database_name: str) -> str:
    url = make_url(database_url)
    return str(url.set(database=database_name))


def _create_database(database_url: str, database_name: str) -> None:
    admin_url = _database_url(database_url, "postgres")
    engine = sa.create_engine(admin_url, isolation_level="AUTOCOMMIT", future=True)
    try:
        with engine.connect() as connection:
            connection.execute(sa.text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
            connection.execute(sa.text(f'CREATE DATABASE "{database_name}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def base_database_url() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://kara:kara_password@db:5432/kara_orders",
    )


@pytest.fixture(scope="session")
def test_database_url(base_database_url: str) -> str:
    database_url = _database_url(base_database_url, TEST_DATABASE_NAME)
    env = os.environ.copy()
    env["PYTHONPATH"] = "/app"
    try:
        _create_database(base_database_url, TEST_DATABASE_NAME)
    except OperationalError:
        env["DATABASE_URL"] = base_database_url
        subprocess.run(["alembic", "upgrade", "head"], cwd=str(ROOT_DIR), check=True, env=env)
        return base_database_url

    env["DATABASE_URL"] = database_url
    subprocess.run(["alembic", "upgrade", "head"], cwd=str(ROOT_DIR), check=True, env=env)
    return database_url


@pytest.fixture(scope="session")
def test_settings(test_database_url: str) -> Settings:
    return Settings(
        database_url=test_database_url,
        secret_key="test-secret-key",
        auth_refresh_cookie_secure=False,
        auth_refresh_cookie_samesite="lax",
        cors_origins=["http://testserver"],
    )


@pytest.fixture(scope="session")
def test_session_factory(test_database_url: str):
    return create_session_factory(test_database_url)


@pytest.fixture(autouse=True)
def clean_database(test_session_factory) -> Generator[None, None, None]:
    session: Session = test_session_factory()
    try:
        session.execute(
            sa.text(
                "TRUNCATE TABLE "
                "inventory_transactions, product_images, product_tag_links, product_tags, product_categories, "
                "ai_learning, ai_recognitions, company_invitations, order_items, orders, products, users, companies, "
                "audit_logs, notifications, company_usages, company_subscriptions "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
        yield
    finally:
        session.execute(
            sa.text(
                "TRUNCATE TABLE "
                "inventory_transactions, product_images, product_tag_links, product_tags, product_categories, "
                "ai_learning, ai_recognitions, company_invitations, order_items, orders, products, users, companies, "
                "audit_logs, notifications, company_usages, company_subscriptions "
                "RESTART IDENTITY CASCADE"
            )
        )
        session.commit()
        session.close()


@pytest.fixture()
def db_session(test_session_factory) -> Generator[Session, None, None]:
    session: Session = test_session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture()
def client(test_session_factory, test_settings: Settings) -> Generator[TestClient, None, None]:
    class FakeStorageService:
        def upload_public_file(self, *, bucket: str, object_path: str, content: bytes, content_type: str) -> UploadResult:
            return UploadResult(
                public_url=f"https://storage.local/{bucket}/{object_path}",
                object_path=object_path,
            )

    def override_get_db() -> Generator[Session, None, None]:
        session: Session = test_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_app_settings] = lambda: test_settings
    app.dependency_overrides[get_storage_service] = lambda: FakeStorageService()
    app.dependency_overrides[get_optional_storage_service] = lambda: FakeStorageService()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
