from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


class Event:
    def __init__(self, event_type: str, payload: Dict[str, Any]):
        self.event_type = event_type
        self.payload = payload
        self.timestamp = datetime.now()


class EventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """
        Subscribe a callback to a specific event type.
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event_type: str, payload: Dict[str, Any]):
        """
        Publish an event to all subscribers of the event type.
        """
        event = Event(event_type, payload)
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error processing event {event_type}: {str(e)}")


# Singleton instance of the event bus
event_bus = EventBus()


# Event types as constants
REPAIR_ORDER_CREATED = "repair_order_created"
ASSIGNMENT_ACCEPTED = "assignment_accepted"
ASSIGNMENT_REJECTED = "assignment_rejected"
REASSIGNMENT_NEEDED = "reassignment_needed"

# Example event payload structures (can be formalized with dataclasses or Pydantic models if needed)


def create_repair_order_event_payload(order_id: int, vehicle_id: int, customer_id: int, request_id: int, required_staff_type: str):
    return {
        "order_id": order_id,
        "vehicle_id": vehicle_id,
        "customer_id": customer_id,
        "request_id": request_id,
        "required_staff_type": required_staff_type
    }


def create_assignment_response_payload(assignment_id: int, order_id: int, staff_id: int, accepted: bool):
    return {
        "assignment_id": assignment_id,
        "order_id": order_id,
        "staff_id": staff_id,
        "accepted": accepted
    }


def create_reassignment_needed_payload(order_id: int, required_staff_type: str, exclude_staff_id: int):
    return {
        "order_id": order_id,
        "required_staff_type": required_staff_type,
        "exclude_staff_id": exclude_staff_id
    }
