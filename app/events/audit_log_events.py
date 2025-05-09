import json
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapper
from sqlalchemy import inspect

from ..models.audit import AuditLog, OperationType


def object_to_dict(obj: Optional[Any]) -> Optional[Dict[str, Any]]:
    """
    Convert a SQLAlchemy model object to a dictionary, excluding private attributes.

    Args:
        obj: The SQLAlchemy model instance to convert.

    Returns:
        A dictionary of the object's attributes or None if the input is None.
    """
    if obj is None:
        return None
    return {key: getattr(obj, key) for key in obj.__dict__ if not key.startswith('_')}


def get_record_id(target: Any) -> Optional[int]:
    """
    Dynamically retrieve the primary key value of a SQLAlchemy model instance.

    Args:
        target: The SQLAlchemy model instance.

    Returns:
        The primary key value (if found and single primary key) or None.
    """
    if target is None:
        return None

    mapper = inspect(target.__class__)

    primary_key_columns = mapper.primary_key

    if len(primary_key_columns) == 1:
        pk_column = primary_key_columns[0]
        return getattr(target, pk_column.key)
    return None


async def log_audit_event(
    db: AsyncSession,
    target: Any,
    operation: OperationType,
    old_data: Optional[Dict[str, Any]] = None,
    new_data: Optional[Dict[str, Any]] = None,
) -> None:
    try:
        audit_log = AuditLog(
            table_name=target.__tablename__,
            record_id=get_record_id(target),
            operation=operation,
            old_data=json.dumps(old_data) if old_data else None,
            new_data=json.dumps(new_data) if new_data else None,
        )
        db.add(audit_log)
        await db.commit()
    except Exception as e:
        print(f"Error logging audit event: {e}")
        raise
