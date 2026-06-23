"""Song search across the user's saved transcriptions and the bundled
public-domain set.

Matches on title and composer with a case-insensitive substring (ILIKE).
Plain ILIKE is sufficient at this scale; Postgres full-text search is a
later optimization if the library grows large. The two sources are queried
separately - personal via the user-scoped client (so RLS limits it to the
caller's own rows) and public via the world-readable table - and returned
in separate lists so the UI can render them as distinct sections.

Each field is queried with its own standalone `.ilike()` and the rows are
merged in Python, rather than combining them into a single PostgREST
`or=(...)` filter. An or=() filter string would need the query value to be
escaped against that grammar's reserved characters (comma, parentheses,
colon) - e.g. searching the bundled composer "Traditional (Irish)" would
otherwise silently match nothing. A standalone filter value has no such
reserved characters, so only the LIKE wildcards need escaping.
"""
from fastapi import APIRouter, Depends

from rhimoz_api.auth import User, get_current_user, get_user_scoped_client
from rhimoz_api.routes.public import LIST_COLUMNS as PUBLIC_COLUMNS
from rhimoz_api.routes.saved import LIST_COLUMNS as SAVED_COLUMNS
from rhimoz_api.schemas import (
    PublicTranscriptionOut,
    SavedTranscriptionOut,
    SearchResultsOut,
)

router = APIRouter()


def _escape_like(term: str) -> str:
    """Neutralize SQL LIKE wildcards so a search for a literal % or _ (or
    the \\ escape char itself) doesn't match everything."""
    return term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def _search_table(db, table: str, columns: str, fields: tuple[str, ...], pattern: str):
    """ILIKE `pattern` against each of `fields`, returning rows deduped by
    id (a row matching on both title and composer appears once)."""
    merged: dict[str, dict] = {}
    for field in fields:
        result = await db.table(table).select(columns).ilike(field, pattern).execute()
        for row in result.data:
            merged[row["id"]] = row
    return list(merged.values())


@router.get("/search", response_model=SearchResultsOut)
async def search_transcriptions(
    q: str,
    user: User = Depends(get_current_user),
) -> SearchResultsOut:
    term = q.strip()
    if not term:
        # An empty query would become "%%" and match the entire library;
        # return nothing instead (the UI also guards this).
        return SearchResultsOut(personal=[], public=[])

    pattern = f"%{_escape_like(term)}%"
    db = await get_user_scoped_client(user.token)

    # RLS on saved_transcriptions scopes this to the caller's own rows.
    personal_rows = await _search_table(
        db, "saved_transcriptions", SAVED_COLUMNS, ("display_name", "composer"), pattern
    )
    personal_rows.sort(key=lambda r: r["created_at"], reverse=True)

    public_rows = await _search_table(
        db, "public_transcriptions", PUBLIC_COLUMNS, ("title", "composer"), pattern
    )
    public_rows.sort(key=lambda r: r["title"].lower())

    return SearchResultsOut(
        personal=[SavedTranscriptionOut(**row) for row in personal_rows],
        public=[PublicTranscriptionOut(**row) for row in public_rows],
    )
