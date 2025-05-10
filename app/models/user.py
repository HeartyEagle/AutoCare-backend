# models/user_models.py
from dataclasses import dataclass
from typing import Optional, List
from .enums import StaffJobType


@dataclass
class User:
    # Primary key, optional for new objects before DB insert
    user_id: Optional[int] = None
    name: str = ""
    username: str = ""
    password: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    # Field to distinguish user type (customer, staff, admin)
    discriminator: str = "customer"

    def __repr__(self) -> str:
        """Representation of the User."""
        return f"<User {self.username}>"


@dataclass
class Admin(User):
    # Foreign key to user.user_id, optional for new objects
    admin_id: Optional[int] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.discriminator = "admin"

    def __repr__(self) -> str:
        """Representation of the Admin."""
        return f"<Admin {self.username}>"


@dataclass
class Staff(User):
    # Foreign key to user.user_id, optional for new objects
    staff_id: Optional[int] = None
    jobtype: Optional[StaffJobType] = None
    hourly_rate: int = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.staff_id = kwargs.get("staff_id", self.user_id)
        self.discriminator = "staff"

    def __repr__(self) -> str:
        """Representation of the Staff."""
        return f"<Staff {self.username}>"

    @property
    def total_hours_worked(self) -> float:
        """Calculate the total hours worked by the staff."""
        if self.repair_assignments:
            return sum(assignment.time_worked for assignment in self.repair_assignments if assignment.time_worked is not None)
        return 0.0


@dataclass
class Customer(User):
    # Foreign key to user.user_id, optional for new objects
    customer_id: Optional[int] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.customer_id = kwargs.get("customer_id", self.user_id)
        self.discriminator = "customer"

    def __repr__(self) -> str:
        """Representation of the Customer."""
        return f"<Customer {self.username}>"
