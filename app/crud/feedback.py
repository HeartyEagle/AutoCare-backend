from ..db.connection import Database
from ..models.customer import Feedback
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any, List
from datetime import datetime


class FeedbackService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_feedback(
        self,
        customer_id: int,
        order_id: int,
        log_id: int,
        rating: int,
        comments: Optional[str] = None
    ) -> Feedback:
        """
        Create a new feedback entry and audit the operation.
        """
        # Prepare feedback object
        feedback = Feedback(
            customer_id=customer_id,
            order_id=order_id,
            log_id=log_id,
            rating=rating,
            comments=comments,
            feedback_time=str(datetime.now())
        )
        # Insert data into 'feedback' table
        self.db.insert_data(
            table_name="feedback",
            data=feedback.asdict()
        )
        # Retrieve last inserted ID (MySQL)
        last_id_row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        feedback_id = int(last_id_row[0][0]) if last_id_row else None
        feedback.feedback_id = feedback_id
        # Log audit event
        self.audit_log_service.log_audit_event(
            table_name="feedback",
            record_id=feedback.feedback_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(feedback)
        )
        return feedback

    def get_feedback_by_id(
        self,
        feedback_id: int
    ) -> Optional[Feedback]:
        """
        Retrieve a feedback by its ID.
        """
        rows = self.db.select_data(
            table_name="feedback",
            columns=["feedback_id", "customer_id", "order_id",
                     "log_id", "rating", "comments", "feedback_time"],
            where=f"feedback_id = {feedback_id}",
            limit=1
        )
        if not rows:
            return None
        row = rows[0]
        return Feedback(
            feedback_id=row[0],
            customer_id=row[1],
            order_id=row[2],
            log_id=row[3],
            rating=row[4],
            comments=row[5] if row[5] else None,
            feedback_time=row[6] if row[6] else None
        )

    def get_feedbacks_by_order_id(self, order_id: int) -> List[Feedback]:
        """
        Retrieve all feedback associated with a specific repair order.

        Args:
            order_id (int): ID of the repair order to fetch feedback for.

        Returns:
            List[Feedback]: List of feedback objects associated with the repair order.
        """
        rows = self.db.select_data(
            table_name="feedback",
            columns=["feedback_id", "customer_id", "order_id",
                     "log_id", "rating", "comments", "feedback_time"],
            where=f"order_id = {order_id}"
        )
        if not rows:
            return []
        return [
            Feedback(
                feedback_id=row[0],
                customer_id=row[1],
                order_id=row[2],
                log_id=row[3] if row[3] != 0 else None,
                rating=row[4],
                comments=row[5] if row[5] else None,
                feedback_time=row[6] if row[6] else None
            )
            for row in rows
        ]

    def get_negative_feedbacks(self, max_rating: int) -> List[Feedback]:
        """
        Retrieve all feedback with a rating less than or equal to the specified maximum (negative feedback).

        Args:
            max_rating (int): Maximum rating to consider as negative feedback (e.g., 2 for ratings <= 2).

        Returns:
            List[Feedback]: List of feedback objects with rating <= max_rating.
        """
        rows = self.db.select_data(
            table_name="feedback",
            columns=["feedback_id", "customer_id", "order_id",
                     "log_id", "rating", "comments", "feedback_time"],
            where=f"rating <= {max_rating}",
            order_by="feedback_time DESC"
        )
        if not rows:
            return []
        return [
            Feedback(
                feedback_id=row[0],
                customer_id=row[1],
                order_id=row[2],
                log_id=row[3] if row[3] != 0 else None,
                rating=row[4],
                comments=row[5] if row[5] else None,
                feedback_time=row[6] if row[6] else None
            )
            for row in rows
        ]

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert an object to a dict for audit logging.
        """
        if not obj:
            return {}
        return {k: v for k, v in vars(obj).items() if not k.startswith("_")}
