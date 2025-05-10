from ..db.connection import Database
from ..models.customer import Feedback
from ..models.enums import OperationType
from .audit import AuditLogService
from typing import Optional, Dict, Any


class FeedbackService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def create_feedback(self, customer_id: int, log_id: int, rating: int, comments: Optional[str] = None) -> Feedback:
        """
        Create a new feedback for a repair log.
        Args:
            customer_id (int): ID of the customer.
            log_id (int): ID of the repair log.
            rating (int): Rating given by the customer.
            comments (Optional[str]): Comments provided by the customer.
        Returns:
            Feedback: The created feedback.
        """
        # Create Feedback object with provided data
        feedback = Feedback(
            customer_id=customer_id,
            log_id=log_id,
            rating=rating,
            comments=comments
        )

        # SQL query to insert feedback
        insert_query = """
            INSERT INTO feedback (customer_id, log_id, rating, comments, feedback_time)
            VALUES (?, ?, ?, ?, GETDATE())
        """
        self.db.execute_non_query(
            insert_query,
            (feedback.customer_id, feedback.log_id,
             feedback.rating, feedback.comments)
        )

        # Fetch the inserted feedback ID (assuming database returns last inserted ID)
        select_id_query = "SELECT @@IDENTITY AS id"
        feedback_id_row = self.db.execute_query(select_id_query)
        feedback.feedback_id = int(
            feedback_id_row[0][0]) if feedback_id_row else None

        # Log audit event for the INSERT operation
        self.audit_log_service.log_audit_event(
            table_name="feedback",
            record_id=feedback.feedback_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(feedback)
        )

        return feedback

    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """
        Get a feedback by ID.
        Args:
            feedback_id (int): ID of the feedback.
        Returns:
            Optional[Feedback]: Feedback object if found, otherwise None.
        """
        select_query = """
            SELECT feedback_id, customer_id, log_id, rating, comments, feedback_time
            FROM feedback
            WHERE feedback_id = ?
        """
        rows = self.db.execute_query(select_query, (feedback_id,))
        if rows:
            # Map row to Feedback dataclass
            return Feedback(
                feedback_id=rows[0][0],
                customer_id=rows[0][1],
                log_id=rows[0][2],
                rating=rows[0][3],
                comments=rows[0][4] if rows[0][4] else None,
                feedback_time=rows[0][5] if rows[0][5] else None
            )
        return None

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert an object to a dictionary for audit logging.
        Args:
            obj: Object to convert.
        Returns:
            Dict[str, Any]: Dictionary representation of the object.
        """
        if not obj:
            return {}
        return {key: value for key, value in vars(obj).items() if not key.startswith("_")}
