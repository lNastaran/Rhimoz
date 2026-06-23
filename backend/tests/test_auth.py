import pytest
from fastapi import HTTPException

from rhimoz_api.auth import get_current_user


async def test_missing_authorization_header_is_401():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None)
    assert exc_info.value.status_code == 401


async def test_non_bearer_authorization_header_is_401():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Basic dXNlcjpwYXNz")
    assert exc_info.value.status_code == 401


async def test_malformed_jwt_is_401():
    # Three checks happen before any network call (structure, base64url
    # format), so a garbage token never needs live Supabase credentials.
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer not-a-real-jwt")
    assert exc_info.value.status_code == 401
