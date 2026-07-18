from __future__ import annotations

from dataclasses import dataclass

from app.core.auth import Role
from app.core.config import Settings
from app.core.security import hash_password
from app.db.models.company import Company
from app.db.models.user import User
from app.schemas.company import CompanyInviteRequest, CompanyInvitationAcceptRequest
from app.services.company_service import CompanyService
from app.services.storage_service import UploadResult, build_storage_object_name


@dataclass
class FakeStorage:
    last_args: dict[str, object] | None = None

    def upload_public_file(self, *, bucket: str, object_path: str, content: bytes, content_type: str) -> UploadResult:
        self.last_args = {
            "bucket": bucket,
            "object_path": object_path,
            "content": content,
            "content_type": content_type,
        }
        return UploadResult(public_url=f"https://storage.local/{bucket}/{object_path}", object_path=object_path)


def test_build_storage_object_name() -> None:
    object_name = build_storage_object_name("Companies", "Acme Supplies", "logo", "123", suffix="png")
    assert object_name == "companies/acme-supplies/logo/123.png"


def test_company_service_upload_logo(db_session) -> None:
    company = Company(name="Acme", currency="KZT", invoice_prefix="INV")
    db_session.add(company)
    db_session.flush()

    service = CompanyService(
        session=db_session,
        settings=Settings(database_url="postgresql+psycopg://example", supabase_storage_bucket="kara-orders"),
        storage_service=FakeStorage(),
    )

    result = service.upload_logo(
        company,
        content=b"image-bytes",
        content_type="image/png",
        kind="logo",
    )

    assert result.url.startswith("https://storage.local/kara-orders/")
    assert company.logo_url == result.url


def test_company_service_invite_and_accept(db_session) -> None:
    company = Company(name="Acme", currency="KZT", invoice_prefix="INV")
    db_session.add(company)
    db_session.flush()

    owner = User(
        company_id=company.id,
        email="owner@acme.local",
        password_hash=hash_password("Password123!"),
        full_name="Owner",
        role=Role.OWNER.value,
        is_active=True,
    )
    db_session.add(owner)
    db_session.commit()

    service = CompanyService(
        session=db_session,
        settings=Settings(database_url="postgresql+psycopg://example"),
    )

    invite = service.invite_user(
        company,
        owner,
        payload=CompanyInviteRequest(
            email="employee@acme.local",
            full_name="Employee",
            role=Role.EMPLOYEE,
        ),
    )
    assert invite.invitation.email == "employee@acme.local"
    assert invite.invite_token

    accepted_user = service.accept_invitation(
        payload=CompanyInvitationAcceptRequest(
            token=invite.invite_token,
            full_name="Employee",
            password="Password123!",
            confirm_password="Password123!",
        ),
    )
    assert accepted_user.email == "employee@acme.local"
