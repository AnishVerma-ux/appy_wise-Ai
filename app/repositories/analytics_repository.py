from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.application import Application, ApplicationStatus


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard_summary(
        self,
        user_id: int,
    ) -> dict[str, int | float]:
        statement = select(
            func.count(Application.id).label(
                "total_applications"
            ),
            func.sum(
                case(
                    (
                        Application.status
                        == ApplicationStatus.INTERVIEW.value,
                        1,
                    ),
                    else_=0,
                )
            ).label("interviews"),
            func.sum(
                case(
                    (
                        Application.status
                        == ApplicationStatus.OFFERED.value,
                        1,
                    ),
                    else_=0,
                )
            ).label("offers"),
            func.sum(
                case(
                    (
                        Application.status
                        == ApplicationStatus.REJECTED.value,
                        1,
                    ),
                    else_=0,
                )
            ).label("rejections"),
            func.avg(Application.match_score).label(
                "average_match_score"
            ),
        ).where(Application.user_id == user_id)

        result = self.db.execute(statement).one()

        return {
            "total_applications": int(
                result.total_applications or 0
            ),
            "interviews": int(result.interviews or 0),
            "offers": int(result.offers or 0),
            "rejections": int(result.rejections or 0),
            "average_match_score": round(
                float(result.average_match_score or 0),
                2,
            ),
        }