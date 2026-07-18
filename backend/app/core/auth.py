from __future__ import annotations

import re
from enum import Enum


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    EMPLOYEE = "employee"

    @property
    def rank(self) -> int:
        return ROLE_RANKS[self.value]


ROLE_RANKS: dict[str, int] = {
    Role.EMPLOYEE.value: 1,
    Role.MANAGER.value: 2,
    Role.ADMIN.value: 3,
    Role.OWNER.value: 4,
}

PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 12 characters long and include upper, lower, digit, and symbol."
)

PASSWORD_POLICY_REGEXES = (
    re.compile(r"[A-Z]"),
    re.compile(r"[a-z]"),
    re.compile(r"\d"),
    re.compile(r"[^A-Za-z0-9]"),
)


def normalize_role(value: str | Role) -> Role:
    if isinstance(value, Role):
        return value
    return Role(value.lower())


def has_minimum_role(current_role: str | Role, required_roles: list[str | Role]) -> bool:
    current = normalize_role(current_role)
    required_ranks = [normalize_role(role).rank for role in required_roles]
    return current.rank >= min(required_ranks)


def validate_password_policy(password: str) -> None:
    if len(password) < 12:
        raise ValueError(PASSWORD_POLICY_MESSAGE)

    if not all(regex.search(password) for regex in PASSWORD_POLICY_REGEXES):
        raise ValueError(PASSWORD_POLICY_MESSAGE)
