"""Rank players by how many questions they have answered correctly across all attempts."""

from dataclasses import dataclass
from datetime import datetime

from django.contrib.auth.models import User

LEADERBOARD_SIZE = 20


@dataclass(frozen=True)
class Standing:
    username: str
    favorite_club: str
    attempts: int
    total_correct: int
    best_score_pct: int
    first_attempt_at: datetime

    @property
    def sort_key(self) -> tuple[int, int, datetime]:
        return (-self.total_correct, -self.best_score_pct, self.first_attempt_at)


def standing_of(player: User) -> Standing:
    attempts = list(player.attempts.all())
    return Standing(
        username=player.username,
        favorite_club=player.profile.favorite_club,
        attempts=len(attempts),
        total_correct=sum(attempt.score for attempt in attempts),
        best_score_pct=max(attempt.percent for attempt in attempts),
        first_attempt_at=min(attempt.created_at for attempt in attempts),
    )


def leaderboard_rows() -> list[dict[str, str | int]]:
    """Top players: most correct answers, then best single attempt, then whoever played first."""
    players = (
        User.objects.filter(attempts__isnull=False)
        .distinct()
        .select_related("profile")
        .prefetch_related("attempts")
    )
    standings = sorted((standing_of(player) for player in players), key=lambda standing: standing.sort_key)
    return [
        {
            "rank": rank,
            "username": standing.username,
            "favorite_club": standing.favorite_club,
            "attempts": standing.attempts,
            "total_correct": standing.total_correct,
            "best_score_pct": standing.best_score_pct,
        }
        for rank, standing in enumerate(standings[:LEADERBOARD_SIZE], start=1)
    ]
