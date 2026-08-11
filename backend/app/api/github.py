"""
TraceIQ - GitHub API Router

HTTP endpoints for retrieving GitHub engineering context.

Responsibilities:
- Validate HTTP parameters.
- Call the GitHub integration.
- Translate integration errors into HTTP responses.
- Return normalized API responses.

This router intentionally contains NO:
- Root-cause analysis
- LLM calls
- Evidence scoring
- Investigation orchestration
- Direct httpx usage

Those responsibilities belong to the appropriate integration/service layer.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.config import settings
from app.integrations.github import (
    GitHubAPIError,
    GitHubAuthenticationError,
    GitHubClient,
    GitHubNotFoundError,
    GitHubRateLimitError,
)


router = APIRouter(
    prefix="/github",
    tags=["GitHub"],
)


# ============================================================================
# CLIENT DEPENDENCY
# ============================================================================


async def _get_github_client() -> GitHubClient:
    """
    Create a GitHub client for the current request.

    The integration itself owns the HTTP client and connection pooling.

    This dependency is intentionally small so it can later be replaced with
    an application-scoped client through FastAPI's dependency injection
    system without changing route signatures.
    """
    return GitHubClient(settings=settings)


# ============================================================================
# ERROR TRANSLATION
# ============================================================================


def _github_http_exception(
    exc: GitHubAPIError,
) -> HTTPException:
    """
    Translate GitHub integration exceptions into safe HTTP errors.

    Provider response bodies are deliberately not exposed directly to the
    client because they may contain implementation details.
    """

    if isinstance(exc, GitHubAuthenticationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub authentication failed.",
        )

    if isinstance(exc, GitHubRateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="GitHub API rate limit exceeded. Please try again later.",
        )

    if isinstance(exc, GitHubNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested GitHub resource was not found.",
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="GitHub API request failed.",
    )


# ============================================================================
# REPOSITORY
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}",
    summary="Get GitHub repository",
    description="Retrieve metadata for a GitHub repository.",
)
async def get_repository(
    owner: str,
    repo: str,
) -> dict[str, Any]:
    """
    Retrieve repository metadata.
    """

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_repository(
            owner=owner,
            repo=repo,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# COMMITS
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/commits",
    summary="Get repository commits",
    description="Retrieve recent commits from a GitHub repository.",
)
async def get_commits(
    owner: str,
    repo: str,
    sha: str | None = Query(
        default=None,
        description="Branch name, tag, or commit SHA.",
    ),
    path: str | None = Query(
        default=None,
        description="Only return commits affecting this file path.",
    ),
    since: str | None = Query(
        default=None,
        description="Only return commits after this ISO-8601 timestamp.",
    ),
    until: str | None = Query(
        default=None,
        description="Only return commits before this ISO-8601 timestamp.",
    ),
    per_page: int = Query(
        default=30,
        ge=1,
        le=100,
        description="Number of commits to return.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="1-based result page.",
    ),
) -> list[dict[str, Any]]:
    """
    Retrieve commits from a GitHub repository.
    """

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_commits(
            owner=owner,
            repo=repo,
            sha=sha,
            path=path,
            since=since,
            until=until,
            per_page=per_page,
            page=page,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# SINGLE COMMIT
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/commits/{sha}",
    summary="Get commit",
    description="Retrieve detailed information about a GitHub commit.",
)
async def get_commit(
    owner: str,
    repo: str,
    sha: str,
) -> dict[str, Any]:
    """Retrieve detailed information about one commit."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_commit(
            owner=owner,
            repo=repo,
            sha=sha,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# PULL REQUESTS
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/pulls",
    summary="Get pull requests",
    description="Retrieve pull requests from a GitHub repository.",
)
async def get_pull_requests(
    owner: str,
    repo: str,
    state: str = Query(
        default="all",
        pattern="^(open|closed|all)$",
    ),
    sort: str = Query(
        default="updated",
        pattern="^(created|updated|popularity|long-running)$",
    ),
    direction: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    per_page: int = Query(
        default=30,
        ge=1,
        le=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
) -> list[dict[str, Any]]:
    """Retrieve pull requests."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_pull_requests(
            owner=owner,
            repo=repo,
            state=state,
            sort=sort,
            direction=direction,
            per_page=per_page,
            page=page,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# PULL REQUEST DETAILS
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/pulls/{pull_number}",
    summary="Get pull request",
    description="Retrieve a specific GitHub pull request.",
)
async def get_pull_request(
    owner: str,
    repo: str,
    pull_number: int = Query(
        ...,
        ge=1,
    ),
) -> dict[str, Any]:
    """Retrieve one pull request."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_pull_request(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# PULL REQUEST FILES
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/pulls/{pull_number}/files",
    summary="Get pull request files",
    description="Retrieve files changed by a pull request.",
)
async def get_pull_request_files(
    owner: str,
    repo: str,
    pull_number: int = Query(
        ...,
        ge=1,
    ),
    per_page: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
) -> list[dict[str, Any]]:
    """Retrieve files changed by a pull request."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_pull_request_files(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            per_page=per_page,
            page=page,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# GITHUB ACTIONS
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/actions/runs",
    summary="Get workflow runs",
    description="Retrieve GitHub Actions workflow runs.",
)
async def get_workflow_runs(
    owner: str,
    repo: str,
    branch: str | None = Query(
        default=None,
    ),
    workflow_status: str | None = Query(
        default=None,
        alias="status",
        description="GitHub Actions workflow status filter.",
    ),
    per_page: int = Query(
        default=30,
        ge=1,
        le=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
) -> dict[str, Any]:
    """Retrieve GitHub Actions workflow runs."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_workflow_runs(
            owner=owner,
            repo=repo,
            branch=branch,
            status=workflow_status,
            per_page=per_page,
            page=page,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# SINGLE WORKFLOW RUN
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/actions/runs/{run_id}",
    summary="Get workflow run",
    description="Retrieve a specific GitHub Actions workflow run.",
)
async def get_workflow_run(
    owner: str,
    repo: str,
    run_id: int,
) -> dict[str, Any]:
    """Retrieve one GitHub Actions workflow run."""

    if run_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="run_id must be greater than zero.",
        )

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_workflow_run(
            owner=owner,
            repo=repo,
            run_id=run_id,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# WORKFLOW JOBS
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/actions/runs/{run_id}/jobs",
    summary="Get workflow jobs",
    description="Retrieve jobs associated with a GitHub Actions workflow run.",
)
async def get_workflow_jobs(
    owner: str,
    repo: str,
    run_id: int,
    per_page: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
    page: int = Query(
        default=1,
        ge=1,
    ),
) -> dict[str, Any]:
    """Retrieve jobs for a workflow run."""

    if run_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="run_id must be greater than zero.",
        )

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_workflow_run_jobs(
            owner=owner,
            repo=repo,
            run_id=run_id,
            per_page=per_page,
            page=page,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# REPOSITORY FILE
# ============================================================================


@router.get(
    "/repositories/{owner}/{repo}/contents/{file_path:path}",
    summary="Get repository file",
    description="Retrieve file content metadata from a GitHub repository.",
)
async def get_file_content(
    owner: str,
    repo: str,
    file_path: str,
    ref: str | None = Query(
        default=None,
        description="Branch, tag, or commit SHA.",
    ),
) -> dict[str, Any]:
    """Retrieve repository file content metadata."""

    if not file_path.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="file_path cannot be empty.",
        )

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_file_content(
            owner=owner,
            repo=repo,
            path=file_path,
            ref=ref,
        )

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


# ============================================================================
# AUTHENTICATED USER
# ============================================================================


@router.get(
    "/user",
    summary="Get authenticated GitHub user",
    description="Verify GitHub authentication and return the authenticated user.",
)
async def get_authenticated_user() -> dict[str, Any]:
    """Verify GitHub credentials."""

    if not settings.github_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub integration is not configured.",
        )

    client = await _get_github_client()

    try:
        return await client.get_authenticated_user()

    except GitHubAPIError as exc:
        raise _github_http_exception(exc) from exc

    finally:
        await client.aclose()


__all__ = [
    "router",
]