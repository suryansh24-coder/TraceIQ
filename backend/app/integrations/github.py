"""
TraceIQ - GitHub Integration

Async GitHub API client used by TraceIQ.

Responsibilities:
- Authenticate with GitHub.
- Retrieve repository information.
- Retrieve commits and changed files.
- Retrieve pull requests.
- Retrieve GitHub Actions workflow runs.
- Retrieve repository file contents.
- Handle pagination.
- Normalize GitHub HTTP failures.
- Reuse HTTP connections efficiently.

This module must NOT contain:
- Root-cause analysis.
- LLM calls.
- Evidence scoring.
- Investigation orchestration.
- Recommendation generation.

Those responsibilities belong to the service layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator

import httpx

from app.config import Settings, get_settings


# ============================================================================
# EXCEPTIONS
# ============================================================================


class GitHubIntegrationError(Exception):
    """
    Base exception raised by the GitHub integration.

    Services can catch this exception without depending on httpx internals.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.status_code = status_code
        self.response = response


class GitHubAuthenticationError(GitHubIntegrationError):
    """Raised when GitHub authentication fails."""


class GitHubNotFoundError(GitHubIntegrationError):
    """Raised when a requested GitHub resource does not exist."""


class GitHubRateLimitError(GitHubIntegrationError):
    """Raised when GitHub API rate limits are exceeded."""


class GitHubAPIError(GitHubIntegrationError):
    """Raised for other GitHub API failures."""


# ============================================================================
# PAGINATION
# ============================================================================


@dataclass(slots=True, frozen=True)
class GitHubPage:
    """Metadata associated with a GitHub API page."""

    items: list[dict[str, Any]]
    page: int
    has_next: bool


# ============================================================================
# CLIENT
# ============================================================================


class GitHubClient:
    """
    High-performance asynchronous GitHub API client.

    The client maintains one reusable httpx.AsyncClient so connections can be
    pooled across multiple GitHub requests.

    Usage:

        async with GitHubClient() as github:
            repository = await github.get_repository(
                "owner",
                "repository",
            )

    Or use a shared application-scoped instance and call `aclose()` during
    application shutdown.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()

        self._external_client = client is not None
        self._client = client

        if self._client is None:
            timeout = httpx.Timeout(
                timeout=self.settings.github_request_timeout_seconds,
                connect=self.settings.http_connect_timeout_seconds,
            )

            limits = httpx.Limits(
                max_connections=self.settings.http_max_connections,
                max_keepalive_connections=(
                    self.settings.http_max_keepalive_connections
                ),
            )

            self._client = httpx.AsyncClient(
                base_url=self.settings.github_api_url.rstrip("/"),
                timeout=timeout,
                limits=limits,
                headers=self._build_headers(),
                follow_redirects=True,
            )

    # ========================================================================
    # CONTEXT MANAGEMENT
    # ========================================================================

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """
        Close the underlying HTTP client.

        External clients supplied by dependency injection are not closed here.
        """
        if self._client is not None and not self._external_client:
            await self._client.aclose()

    # ========================================================================
    # HEADERS
    # ========================================================================

    def _build_headers(self) -> dict[str, str]:
        """Build standard GitHub API request headers."""

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.settings.github_api_version,
            "User-Agent": "TraceIQ/1.0",
        }

        if self.settings.github_token:
            token = self.settings.github_token.get_secret_value()

            if token:
                headers["Authorization"] = f"Bearer {token}"

        return headers

    # ========================================================================
    # LOW-LEVEL REQUEST
    # ========================================================================

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any | None = None,
    ) -> Any:
        """
        Execute a GitHub API request and normalize failures.

        This is the only method that directly deals with HTTP-level GitHub
        error semantics.
        """

        if self._client is None:
            raise GitHubIntegrationError(
                "GitHub HTTP client is not initialized."
            )

        try:
            response = await self._client.request(
                method,
                endpoint,
                params=params,
                json=json,
            )

        except httpx.TimeoutException as exc:
            raise GitHubAPIError(
                "GitHub API request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise GitHubAPIError(
                f"GitHub API request failed: {exc}"
            ) from exc

        if response.status_code == 401:
            raise GitHubAuthenticationError(
                "GitHub authentication failed.",
                status_code=response.status_code,
                response=self._safe_response_json(response),
            )

        if response.status_code == 403:
            response_data = self._safe_response_json(response)

            if self._is_rate_limited(response):
                raise GitHubRateLimitError(
                    "GitHub API rate limit exceeded.",
                    status_code=response.status_code,
                    response=response_data,
                )

            raise GitHubAPIError(
                "GitHub API access was forbidden.",
                status_code=response.status_code,
                response=response_data,
            )

        if response.status_code == 404:
            raise GitHubNotFoundError(
                "GitHub resource was not found.",
                status_code=response.status_code,
                response=self._safe_response_json(response),
            )

        if response.status_code >= 400:
            raise GitHubAPIError(
                f"GitHub API returned HTTP {response.status_code}.",
                status_code=response.status_code,
                response=self._safe_response_json(response),
            )

        if response.status_code == 204:
            return None

        try:
            return response.json()

        except ValueError as exc:
            raise GitHubAPIError(
                "GitHub returned an invalid JSON response.",
                status_code=response.status_code,
            ) from exc

    @staticmethod
    def _safe_response_json(
        response: httpx.Response,
    ) -> dict[str, Any] | None:
        """Safely extract a JSON error response."""

        try:
            data = response.json()

            if isinstance(data, dict):
                return data

        except ValueError:
            pass

        return None

    @staticmethod
    def _is_rate_limited(response: httpx.Response) -> bool:
        """Detect GitHub rate-limit responses."""

        remaining = response.headers.get("X-RateLimit-Remaining")

        if remaining == "0":
            return True

        return response.status_code == 403 and (
            "rate limit" in response.text.lower()
        )

    # ========================================================================
    # REPOSITORY
    # ========================================================================

    async def get_repository(
        self,
        owner: str,
        repo: str,
    ) -> dict[str, Any]:
        """
        Retrieve repository metadata.
        """

        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}",
        )

    # ========================================================================
    # COMMITS
    # ========================================================================

    async def get_commits(
        self,
        owner: str,
        repo: str,
        *,
        sha: str | None = None,
        path: str | None = None,
        since: str | None = None,
        until: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Retrieve repository commits.

        Parameters such as `since` and `until` should be ISO-8601 timestamps.
        """

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        params: dict[str, Any] = {
            "per_page": per_page,
            "page": page,
        }

        if sha:
            params["sha"] = sha

        if path:
            params["path"] = path

        if since:
            params["since"] = since

        if until:
            params["until"] = until

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits",
            params=params,
        )

        if not isinstance(data, list):
            raise GitHubAPIError(
                "Unexpected GitHub commits response format."
            )

        return data

    async def iter_commits(
        self,
        owner: str,
        repo: str,
        *,
        sha: str | None = None,
        path: str | None = None,
        since: str | None = None,
        until: str | None = None,
        per_page: int = 100,
        max_pages: int = 10,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Lazily iterate through commits.

        Lazy pagination prevents TraceIQ from loading large repositories
        entirely into memory.
        """

        per_page = min(max(per_page, 1), 100)
        max_pages = max(max_pages, 1)

        for page in range(1, max_pages + 1):
            commits = await self.get_commits(
                owner,
                repo,
                sha=sha,
                path=path,
                since=since,
                until=until,
                per_page=per_page,
                page=page,
            )

            if not commits:
                break

            for commit in commits:
                yield commit

            if len(commits) < per_page:
                break

    # ========================================================================
    # SINGLE COMMIT
    # ========================================================================

    async def get_commit(
        self,
        owner: str,
        repo: str,
        sha: str,
    ) -> dict[str, Any]:
        """Retrieve detailed information about one commit."""

        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/commits/{sha}",
        )

    # ========================================================================
    # PULL REQUESTS
    # ========================================================================

    async def get_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        state: str = "all",
        sort: str = "updated",
        direction: str = "desc",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Retrieve repository pull requests."""

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={
                "state": state,
                "sort": sort,
                "direction": direction,
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, list):
            raise GitHubAPIError(
                "Unexpected GitHub pull request response format."
            )

        return data

    async def get_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> dict[str, Any]:
        """Retrieve a single pull request."""

        if pull_number < 1:
            raise ValueError("pull_number must be greater than zero.")

        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}",
        )

    async def get_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        *,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Retrieve files changed by a pull request."""

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls/{pull_number}/files",
            params={
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, list):
            raise GitHubAPIError(
                "Unexpected GitHub pull request files response format."
            )

        return data

    # ========================================================================
    # GITHUB ACTIONS
    # ========================================================================

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        *,
        branch: str | None = None,
        status: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Retrieve GitHub Actions workflow runs.

        The response includes:
            total_count
            workflow_runs
        """

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        params: dict[str, Any] = {
            "per_page": per_page,
            "page": page,
        }

        if branch:
            params["branch"] = branch

        if status:
            params["status"] = status

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs",
            params=params,
        )

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "Unexpected GitHub Actions response format."
            )

        return data

    async def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> dict[str, Any]:
        """Retrieve a specific GitHub Actions workflow run."""

        if run_id <= 0:
            raise ValueError("run_id must be greater than zero.")

        return await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}",
        )

    async def get_workflow_run_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        *,
        per_page: int = 100,
        page: int = 1,
    ) -> dict[str, Any]:
        """Retrieve jobs associated with a GitHub Actions workflow run."""

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/jobs",
            params={
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "Unexpected GitHub Actions jobs response format."
            )

        return data

    # ========================================================================
    # REPOSITORY CONTENT
    # ========================================================================

    async def get_file_content(
        self,
        owner: str,
        repo: str,
        path: str,
        *,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve repository file metadata/content.

        GitHub normally returns Base64 encoded file content for files.
        Decoding is intentionally handled by a higher-level utility/service
        so this integration remains a faithful API adapter.
        """

        params: dict[str, Any] | None = None

        if ref:
            params = {"ref": ref}

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/contents/{path.lstrip('/')}",
            params=params,
        )

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "Unexpected GitHub file-content response format."
            )

        return data

    # ========================================================================
    # BRANCHES
    # ========================================================================

    async def get_branches(
        self,
        owner: str,
        repo: str,
        *,
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Retrieve repository branches."""

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/branches",
            params={
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, list):
            raise GitHubAPIError(
                "Unexpected GitHub branches response format."
            )

        return data

    # ========================================================================
    # ISSUES
    # ========================================================================

    async def get_issues(
        self,
        owner: str,
        repo: str,
        *,
        state: str = "open",
        per_page: int = 30,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Retrieve repository issues.

        Pull requests may also appear in GitHub's Issues API. Consumers
        should inspect the `pull_request` field when they need to distinguish
        them.
        """

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={
                "state": state,
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, list):
            raise GitHubAPIError(
                "Unexpected GitHub issues response format."
            )

        return data

    # ========================================================================
    # SEARCH
    # ========================================================================

    async def search_code(
        self,
        query: str,
        *,
        per_page: int = 30,
        page: int = 1,
    ) -> dict[str, Any]:
        """
        Search GitHub code.

        The caller is responsible for constructing a valid GitHub search
        query, for example:

            "database timeout repo:owner/repository"
        """

        if not query.strip():
            raise ValueError("GitHub code search query cannot be empty.")

        per_page = min(max(per_page, 1), 100)
        page = max(page, 1)

        data = await self._request(
            "GET",
            "/search/code",
            params={
                "q": query,
                "per_page": per_page,
                "page": page,
            },
        )

        if not isinstance(data, dict):
            raise GitHubAPIError(
                "Unexpected GitHub code-search response format."
            )

        return data

    # ========================================================================
    # HEALTH / AUTHENTICATION
    # ========================================================================

    async def get_authenticated_user(self) -> dict[str, Any]:
        """
        Verify GitHub authentication and retrieve the authenticated user.

        This is useful for the TraceIQ health/readiness checks.
        """

        return await self._request(
            "GET",
            "/user",
        )


# ============================================================================
# FACTORY
# ============================================================================


def create_github_client(
    settings: Settings | None = None,
) -> GitHubClient:
    """
    Create a GitHub client.

    A factory keeps construction centralized and makes dependency injection
    straightforward in FastAPI tests and application startup.
    """

    return GitHubClient(
        settings=settings or get_settings(),
    )


__all__ = [
    "GitHubClient",
    "GitHubIntegrationError",
    "GitHubAuthenticationError",
    "GitHubNotFoundError",
    "GitHubRateLimitError",
    "GitHubAPIError",
    "GitHubPage",
    "create_github_client",
]