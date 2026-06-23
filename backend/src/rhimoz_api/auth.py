import os
from dataclasses import dataclass

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from supabase import AsyncClient, AuthError, create_async_client

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_PUBLISHABLE_KEY = os.environ["SUPABASE_PUBLISHABLE_KEY"]

_client: AsyncClient | None = None


async def get_supabase_client() -> AsyncClient:
    """Lazily creates a single shared AsyncClient for the life of the
    process - construction itself is async, so it can't happen at import
    time, and there's no need for a new client per request."""
    global _client
    if _client is None:
        _client = await create_async_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)
    return _client


@dataclass
class User:
    id: str
    email: str | None


async def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or malformed Authorization header")
    token = authorization.removeprefix("Bearer ")

    client = await get_supabase_client()
    # get_claims() verifies the JWT locally against Supabase's JWKS endpoint
    # (cached) for the new asymmetric signing keys, falling back to a
    # network round-trip (get_user()) only for legacy HS256 projects - no
    # need to hand-roll JWKS verification or pick an algorithm ourselves.
    try:
        response = await client.auth.get_claims(jwt=token)
    except AuthError as exc:
        raise HTTPException(401, f"Invalid token: {exc}") from exc

    if response is None:
        raise HTTPException(401, "Invalid token")

    # ClaimsResponse is a TypedDict, not a class instance - it's a plain
    # dict at runtime (confirmed via the installed supabase_auth.types
    # source after `.claims` attribute access raised AttributeError
    # against a real token in manual testing).
    claims = response["claims"]
    return User(id=claims["sub"], email=claims.get("email"))
