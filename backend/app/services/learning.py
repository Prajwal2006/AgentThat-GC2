"""Learning Platform Service - courses, assessments, certifications, and team progress."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, UTC
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class PrerequisiteIncompleteError(Exception):
    """Raised when a user attempts to enroll without completing prerequisites."""
    pass


class AssessmentCooldownError(Exception):
    """Raised when a user attempts an assessment within the 24hr cooldown period."""
    pass


class LearningPlatformService:
    """Manages courses, enrollment, assessments, certifications, and team progress."""

    PASSING_SCORE: float = 70.0
    COOLDOWN_HOURS: int = 24

    def __init__(self, db: AsyncSession, tenant_id: uuid.UUID, user_id: uuid.UUID):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id

    async def list_courses(self) -> list[dict[str, Any]]:
        """List all available courses for the tenant.

        Returns:
            List of course dicts with metadata.
        """
        # Placeholder: real implementation queries courses table
        return []

    async def enroll(self, course_id: uuid.UUID) -> dict[str, Any]:
        """Enroll the current user in a course, enforcing prerequisites.

        Args:
            course_id: The course to enroll in.

        Returns:
            Enrollment record.

        Raises:
            PrerequisiteIncompleteError: If prerequisites are not met.
        """
        prerequisites = await self._get_prerequisites(course_id)
        completed = await self._get_completed_courses(self.user_id)

        missing = [p for p in prerequisites if p not in completed]
        if missing:
            raise PrerequisiteIncompleteError(
                f"Missing prerequisites: {', '.join(str(m) for m in missing)}"
            )

        enrollment_id = uuid.uuid4()
        now = datetime.now(UTC)

        return {
            "enrollment_id": str(enrollment_id),
            "course_id": str(course_id),
            "user_id": str(self.user_id),
            "tenant_id": str(self.tenant_id),
            "status": "enrolled",
            "enrolled_at": now.isoformat(),
        }

    async def submit_assessment(
        self, course_id: uuid.UUID, answers: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Submit a course assessment with 70% passing threshold and 24hr cooldown.

        Args:
            course_id: The course being assessed.
            answers: List of answer dicts (question_id, answer).

        Returns:
            Assessment result dict with score, passed status, and certification if earned.

        Raises:
            AssessmentCooldownError: If attempted within 24hr of last attempt.
        """
        # Check cooldown
        last_attempt = await self._get_last_attempt_time(self.user_id, course_id)
        if last_attempt:
            cooldown_end = last_attempt + timedelta(hours=self.COOLDOWN_HOURS)
            now = datetime.now(UTC)
            if now < cooldown_end:
                remaining = cooldown_end - now
                hours_remaining = remaining.total_seconds() / 3600
                raise AssessmentCooldownError(
                    f"Assessment cooldown active. Retry in {hours_remaining:.1f} hours"
                )

        # Score assessment
        score = await self._calculate_score(course_id, answers)
        passed = score >= self.PASSING_SCORE
        now = datetime.now(UTC)

        result: dict[str, Any] = {
            "assessment_id": str(uuid.uuid4()),
            "course_id": str(course_id),
            "user_id": str(self.user_id),
            "score": round(score, 2),
            "passing_score": self.PASSING_SCORE,
            "passed": passed,
            "submitted_at": now.isoformat(),
        }

        if passed:
            cert_id = uuid.uuid4()
            result["certification"] = {
                "certification_id": str(cert_id),
                "course_id": str(course_id),
                "user_id": str(self.user_id),
                "issued_at": now.isoformat(),
                "expires_at": (now + timedelta(days=365)).isoformat(),
            }

        return result

    async def get_certifications(
        self, user_id: uuid.UUID | None = None
    ) -> list[dict[str, Any]]:
        """Get certifications for a user (defaults to current user).

        Args:
            user_id: Optional user ID. Defaults to current user.

        Returns:
            List of certification records.
        """
        target_user = user_id or self.user_id
        # Placeholder: real implementation queries certifications table
        return []

    async def get_team_progress(self, team_id: uuid.UUID) -> dict[str, Any]:
        """Get aggregate learning progress for a team.

        Args:
            team_id: The team identifier.

        Returns:
            Team progress summary with per-member breakdown.
        """
        # Placeholder: real implementation aggregates team member progress
        return {
            "team_id": str(team_id),
            "tenant_id": str(self.tenant_id),
            "total_members": 0,
            "courses_completed": 0,
            "certifications_earned": 0,
            "average_score": 0.0,
            "members": [],
        }

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_prerequisites(self, course_id: uuid.UUID) -> list[uuid.UUID]:
        """Fetch prerequisite course IDs for a given course.

        Placeholder: real implementation queries course prerequisites table.
        """
        return []

    async def _get_completed_courses(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Fetch list of completed course IDs for a user.

        Placeholder: real implementation queries enrollment/completion table.
        """
        return []

    async def _get_last_attempt_time(
        self, user_id: uuid.UUID, course_id: uuid.UUID
    ) -> datetime | None:
        """Fetch the timestamp of the user's last assessment attempt.

        Placeholder: real implementation queries assessment attempts table.
        """
        return None

    async def _calculate_score(
        self, course_id: uuid.UUID, answers: list[dict[str, Any]]
    ) -> float:
        """Calculate assessment score as a percentage.

        Placeholder: real implementation checks answers against answer key.
        """
        if not answers:
            return 0.0
        # Simulated scoring
        return 75.0
