from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.repositories.analytics_repository import (
    AnalyticsRepository,
)
from app.schemas.analytics import DashboardResponse


class AnalyticsStorageError(Exception):
    pass


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.analytics = AnalyticsRepository(db)

    def get_dashboard(
        self,
        user_id: int,
    ) -> DashboardResponse:
        try:
            summary = self.analytics.get_dashboard_summary(
                user_id=user_id
            )
        except SQLAlchemyError as exc:
            raise AnalyticsStorageError(
                "Dashboard data could not be retrieved"
            ) from exc

        return DashboardResponse(**summary)