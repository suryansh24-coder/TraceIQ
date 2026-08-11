"""
TraceIQ - GitHub Actions Integration

Provides an asynchronous adapter for GitHub Actions CI/CD data.

Responsibilities:
- Retrieve workflow runs.
- Retrieve workflow jobs.
- Retrieve failed job information.
- Retrieve workflow metadata.
- Normalize common CI/CD information.
- Reuse the application's GitHub HTTP client.

This module is intentionally focused on data acquisition.

It does NOT:
- Determine root cause.
- Calculate investigation confidence.
- Call an LLM.
- Generate recommendations.
- Execute deployments or workflow mutations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.config import Settings, get_settings
from app.integrations.github import (
    GitHubAPIError,
    GitHubClient,
    GitHubNotFoundError,
)


# ============================================================================
# EXCEPTIONS
# ============================================================================


class GitHubActionsError(Exception):
    """Base exception for GitHub Actions integration failures."""


class WorkflowRunNotFoundError(GitHubActionsError):
    """Raised when a requested workflow run does not exist."""


class WorkflowDataError(GitHubActionsError):
    """Raised when GitHub returns unexpected workflow data."""


# ============================================================================
# NORMALIZED DATA MODELS
# ============================================================================


@dataclass(slots=True, frozen=True)
class WorkflowRunSummary:
    """
    Normalized representation of a GitHub Actions workflow run.

    This keeps the service layer independent from GitHub's complete response
    structure.
    """

    run_id: int
    name: str | None
    workflow_id: int | None
    status: str | None
    conclusion: str | None
    branch: str | None
    commit_sha: str | None
    event: str | None
    actor: str | None
    created_at: datetime | None
    updated_at: datetime | None
    url: str | None


@dataclass(slots=True, frozen=True)
class WorkflowJobSummary:
    """Normalized representation of a GitHub Actions job."""

    job_id: int
    name: str | None
    status: str | None
    conclusion: str | None
    started_at: datetime | None
    completed_at: datetime | None
    runner_name: str | None
    url: str | None


@dataclass(slots=True, frozen=True)
class FailedJob:
    """A failed GitHub Actions job with useful investigation context."""

    job: WorkflowJobSummary
    failed_steps: tuple[str, ...]


# ============================================================================
# CLIENT
# ============================================================================


class GitHubActionsClient:
    """
    Async GitHub Actions adapter.

    This class reuses GitHubClient rather than creating a second HTTP client.
    That gives TraceIQ connection pooling and centralized GitHub error
    handling.
    """

    def __init__(
        self,
        github_client: GitHubClient | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.github = github_client or GitHubClient(self.settings)
        self._owns_github_client = github_client is None

    async def aclose(self) -> None:
        """Close the underlying GitHub client when owned by this instance."""

        if self._owns_github_client:
            await self.github.aclose()

    async def __aenter__(self) -> "GitHubActionsClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any,
    ) -> None:
        await self.aclose()

    # ========================================================================
    # WORKFLOW RUNS
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
    ) -> list[WorkflowRunSummary]:
        """
        Retrieve normalized workflow runs.

        The GitHub API returns a dictionary containing `workflow_runs`.
        """

        try:
            response = await self.github.get_workflow_runs(
                owner,
                repo,
                branch=branch,
                status=status,
                per_page=per_page,
                page=page,
            )

        except GitHubNotFoundError as exc:
            raise WorkflowRunNotFoundError(
                f"GitHub Actions data not found for {owner}/{repo}."
            ) from exc

        except GitHubAPIError as exc:
            raise GitHubActionsError(
                f"Unable to retrieve workflow runs for {owner}/{repo}: {exc}"
            ) from exc

        runs = response.get("workflow_runs", [])

        if not isinstance(runs, list):
            raise WorkflowDataError(
                "GitHub returned an invalid workflow_runs structure."
            )

        return [
            self._normalize_workflow_run(run)
            for run in runs
            if isinstance(run, dict)
        ]

    async def get_latest_workflow_run(
        self,
        owner: str,
        repo: str,
        *,
        branch: str | None = None,
    ) -> WorkflowRunSummary | None:
        """
        Retrieve the newest workflow run.

        Returns None when the repository has no workflow runs.
        """

        runs = await self.get_workflow_runs(
            owner,
            repo,
            branch=branch,
            per_page=1,
            page=1,
        )

        return runs[0] if runs else None

    async def get_failed_workflow_runs(
        self,
        owner: str,
        repo: str,
        *,
        branch: str | None = None,
        per_page: int = 30,
        page: int = 1,
    ) -> list[WorkflowRunSummary]:
        """Retrieve workflow runs that ended unsuccessfully."""

        runs = await self.get_workflow_runs(
            owner,
            repo,
            branch=branch,
            per_page=per_page,
            page=page,
        )

        return [
            run
            for run in runs
            if run.conclusion in {
                "failure",
                "timed_out",
                "cancelled",
                "startup_failure",
                "action_required",
            }
        ]

    # ========================================================================
    # SINGLE RUN
    # ========================================================================

    async def get_workflow_run(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> WorkflowRunSummary:
        """Retrieve and normalize one workflow run."""

        try:
            response = await self.github.get_workflow_run(
                owner,
                repo,
                run_id,
            )

        except GitHubNotFoundError as exc:
            raise WorkflowRunNotFoundError(
                f"Workflow run {run_id} was not found."
            ) from exc

        except GitHubAPIError as exc:
            raise GitHubActionsError(
                f"Unable to retrieve workflow run {run_id}: {exc}"
            ) from exc

        if not isinstance(response, dict):
            raise WorkflowDataError(
                "GitHub returned an invalid workflow run response."
            )

        return self._normalize_workflow_run(response)

    # ========================================================================
    # JOBS
    # ========================================================================

    async def get_workflow_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
        *,
        per_page: int = 100,
        page: int = 1,
    ) -> list[WorkflowJobSummary]:
        """Retrieve jobs associated with a workflow run."""

        try:
            response = await self.github.get_workflow_run_jobs(
                owner,
                repo,
                run_id,
                per_page=per_page,
                page=page,
            )

        except GitHubNotFoundError as exc:
            raise WorkflowRunNotFoundError(
                f"Jobs for workflow run {run_id} were not found."
            ) from exc

        except GitHubAPIError as exc:
            raise GitHubActionsError(
                f"Unable to retrieve jobs for workflow run {run_id}: {exc}"
            ) from exc

        jobs = response.get("jobs", [])

        if not isinstance(jobs, list):
            raise WorkflowDataError(
                "GitHub returned an invalid jobs structure."
            )

        return [
            self._normalize_job(job)
            for job in jobs
            if isinstance(job, dict)
        ]

    async def get_failed_jobs(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> list[FailedJob]:
        """
        Retrieve failed jobs and identify failed steps.

        This is particularly useful for TraceIQ because CI failures can
        provide strong evidence about a recently introduced regression.
        """

        try:
            response = await self.github.get_workflow_run_jobs(
                owner,
                repo,
                run_id,
                per_page=100,
                page=1,
            )

        except GitHubNotFoundError as exc:
            raise WorkflowRunNotFoundError(
                f"Jobs for workflow run {run_id} were not found."
            ) from exc

        except GitHubAPIError as exc:
            raise GitHubActionsError(
                f"Unable to inspect jobs for workflow run {run_id}: {exc}"
            ) from exc

        jobs = response.get("jobs", [])

        if not isinstance(jobs, list):
            raise WorkflowDataError(
                "GitHub returned an invalid jobs structure."
            )

        failed_jobs: list[FailedJob] = []

        for raw_job in jobs:
            if not isinstance(raw_job, dict):
                continue

            job = self._normalize_job(raw_job)

            if job.conclusion != "failure":
                continue

            failed_steps = self._extract_failed_steps(raw_job)

            failed_jobs.append(
                FailedJob(
                    job=job,
                    failed_steps=tuple(failed_steps),
                )
            )

        return failed_jobs

    # ========================================================================
    # CI INVESTIGATION CONTEXT
    # ========================================================================

    async def collect_run_context(
        self,
        owner: str,
        repo: str,
        run_id: int,
    ) -> dict[str, Any]:
        """
        Collect compact investigation context for a workflow run.

        The result is intentionally normalized and bounded so that the
        orchestrator does not unnecessarily send huge GitHub responses to
        the LLM.
        """

        run = await self.get_workflow_run(
            owner,
            repo,
            run_id,
        )

        failed_jobs = await self.get_failed_jobs(
            owner,
            repo,
            run_id,
        )

        return {
            "run": self._run_to_dict(run),
            "failed_jobs": [
                {
                    "job": self._job_to_dict(item.job),
                    "failed_steps": list(item.failed_steps),
                }
                for item in failed_jobs
            ],
            "failure_count": len(failed_jobs),
        }

    # ========================================================================
    # NORMALIZATION
    # ========================================================================

    @staticmethod
    def _normalize_workflow_run(
        data: dict[str, Any],
    ) -> WorkflowRunSummary:
        """Normalize GitHub workflow-run JSON."""

        return WorkflowRunSummary(
            run_id=int(data.get("id", 0)),
            name=data.get("name"),
            workflow_id=_safe_int(data.get("workflow_id")),
            status=data.get("status"),
            conclusion=data.get("conclusion"),
            branch=data.get("head_branch"),
            commit_sha=data.get("head_sha"),
            event=data.get("event"),
            actor=_extract_actor(data),
            created_at=_parse_datetime(data.get("created_at")),
            updated_at=_parse_datetime(data.get("updated_at")),
            url=data.get("html_url"),
        )

    @staticmethod
    def _normalize_job(
        data: dict[str, Any],
    ) -> WorkflowJobSummary:
        """Normalize GitHub Actions job JSON."""

        return WorkflowJobSummary(
            job_id=int(data.get("id", 0)),
            name=data.get("name"),
            status=data.get("status"),
            conclusion=data.get("conclusion"),
            started_at=_parse_datetime(data.get("started_at")),
            completed_at=_parse_datetime(data.get("completed_at")),
            runner_name=data.get("runner_name"),
            url=data.get("html_url"),
        )

    @staticmethod
    def _extract_failed_steps(
        job: dict[str, Any],
    ) -> list[str]:
        """
        Extract names of failed steps from a GitHub Actions job.

        Only failed steps are retained to keep investigation context compact.
        """

        steps = job.get("steps", [])

        if not isinstance(steps, list):
            return []

        failed_steps: list[str] = []

        for step in steps:
            if not isinstance(step, dict):
                continue

            if step.get("conclusion") != "failure":
                continue

            name = step.get("name")

            if isinstance(name, str) and name.strip():
                failed_steps.append(name.strip())

        return failed_steps

    # ========================================================================
    # SERIALIZATION
    # ========================================================================

    @staticmethod
    def _run_to_dict(
        run: WorkflowRunSummary,
    ) -> dict[str, Any]:
        """Convert normalized workflow data to JSON-compatible data."""

        return {
            "run_id": run.run_id,
            "name": run.name,
            "workflow_id": run.workflow_id,
            "status": run.status,
            "conclusion": run.conclusion,
            "branch": run.branch,
            "commit_sha": run.commit_sha,
            "event": run.event,
            "actor": run.actor,
            "created_at": (
                run.created_at.isoformat()
                if run.created_at
                else None
            ),
            "updated_at": (
                run.updated_at.isoformat()
                if run.updated_at
                else None
            ),
            "url": run.url,
        }

    @staticmethod
    def _job_to_dict(
        job: WorkflowJobSummary,
    ) -> dict[str, Any]:
        """Convert normalized job data to JSON-compatible data."""

        return {
            "job_id": job.job_id,
            "name": job.name,
            "status": job.status,
            "conclusion": job.conclusion,
            "started_at": (
                job.started_at.isoformat()
                if job.started_at
                else None
            ),
            "completed_at": (
                job.completed_at.isoformat()
                if job.completed_at
                else None
            ),
            "runner_name": job.runner_name,
            "url": job.url,
        }


# ============================================================================
# HELPERS
# ============================================================================


def _parse_datetime(value: Any) -> datetime | None:
    """Safely parse an ISO-8601 timestamp."""

    if not isinstance(value, str) or not value.strip():
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        return None


def _safe_int(value: Any) -> int | None:
    """Safely convert a value to an integer."""

    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _extract_actor(data: dict[str, Any]) -> str | None:
    """Extract the actor login from a GitHub response."""

    actor = data.get("actor")

    if isinstance(actor, dict):
        login = actor.get("login")

        if isinstance(login, str):
            return login

    return None


# ============================================================================
# FACTORY
# ============================================================================


def create_github_actions_client(
    settings: Settings | None = None,
    github_client: GitHubClient | None = None,
) -> GitHubActionsClient:
    """
    Construct a GitHub Actions integration.

    Dependency injection is supported so tests can provide a mocked
    GitHubClient.
    """

    return GitHubActionsClient(
        github_client=github_client,
        settings=settings or get_settings(),
    )


__all__ = [
    "GitHubActionsClient",
    "GitHubActionsError",
    "WorkflowRunNotFoundError",
    "WorkflowDataError",
    "WorkflowRunSummary",
    "WorkflowJobSummary",
    "FailedJob",
    "create_github_actions_client",
]