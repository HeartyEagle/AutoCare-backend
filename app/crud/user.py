from ..db.connection import Database
from ..models.user import User, Admin, Staff, Customer
from ..models.enums import StaffJobType, OperationType
from .audit import AuditLogService
from ..core.security import get_password_hash
from ..schemas.auth import UserCreate, StaffCreate
from typing import Optional, Dict, Any


class UserService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        Args:
            username (str): Username of the user.
        Returns:
            Optional[User]: User object if found, otherwise None.
        """
        select_query = """
            SELECT user_id, name, username, password, phone, email, address, discriminator
            FROM user
            WHERE username = ?
        """
        rows = self.db.execute_query(select_query, (username,))
        if rows:
            return self._map_user_row_to_object(rows[0])
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        Args:
            user_id (int): ID of the user.
        Returns:
            Optional[User]: User object if found, otherwise None.
        """
        select_query = """
            SELECT user_id, name, username, password, phone, email, address, discriminator
            FROM user
            WHERE user_id = ?
        """
        rows = self.db.execute_query(select_query, (user_id,))
        if rows:
            return self._map_user_row_to_object(rows[0])
        return None

    def create_customer(self, user: UserCreate) -> Customer:
        """
        Create a customer with a hashed password.
        Args:
            user (UserCreate): User creation schema with user details.
        Returns:
            Customer: Created customer object.
        """
        hashed_password = get_password_hash(user.password)
        customer = Customer(
            name=user.name,
            username=user.username,
            password=hashed_password,
            phone=user.phone,
            email=user.email,
            address=user.address
        )
        insert_query = """
            INSERT INTO user (name, username, password, phone, email, address, discriminator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_non_query(
            insert_query,
            (customer.name, customer.username, customer.password, customer.phone,
             customer.email, customer.address, customer.discriminator)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        user_id_row = self.db.execute_query(select_id_query)
        user_id = int(user_id_row[0][0]) if user_id_row else None
        customer.user_id = user_id
        customer.customer_id = user_id  # Assuming customer_id is the same as user_id
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=customer.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(customer)
        )
        return customer

    def create_admin(self, user: UserCreate) -> Admin:
        """
        Create an admin with a hashed password.
        Args:
            user (UserCreate): User creation schema with user details.
        Returns:
            Admin: Created admin object.
        """
        hashed_password = get_password_hash(user.password)
        admin = Admin(
            name=user.name,
            username=user.username,
            password=hashed_password,
            phone=user.phone,
            email=user.email,
            address=user.address
        )  # discriminator is set to "admin" in Admin's __init__
        insert_query = """
            INSERT INTO user (name, username, password, phone, email, address, discriminator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_non_query(
            insert_query,
            (admin.name, admin.username, admin.password, admin.phone,
             admin.email, admin.address, admin.discriminator)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        user_id_row = self.db.execute_query(select_id_query)
        user_id = int(user_id_row[0][0]) if user_id_row else None
        admin.user_id = user_id
        admin.admin_id = user_id  # Assuming admin_id is the same as user_id
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=admin.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(admin)
        )
        return admin

    def create_staff(self, user: StaffCreate) -> Staff:
        """
        Create a staff member with a hashed password.
        Args:
            user (StaffCreate): User creation schema with user details.
        Returns:
            Staff: Created staff object.
        """
        hashed_password = get_password_hash(user.password)
        staff = Staff(
            name=user.name,
            username=user.username,
            password=hashed_password,
            phone=user.phone,
            email=user.email,
            address=user.address,
            jobtype=user.jobtype,
            hourly_rate=user.hourly_rate
        )  # discriminator is set to "staff" in Staff's __init__
        # Insert into user table
        insert_user_query = """
            INSERT INTO user (name, username, password, phone, email, address, discriminator)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.db.execute_non_query(
            insert_user_query,
            (staff.name, staff.username, staff.password, staff.phone,
             staff.email, staff.address, staff.discriminator)
        )
        select_id_query = "SELECT @@IDENTITY AS id"
        user_id_row = self.db.execute_query(select_id_query)
        user_id = int(user_id_row[0][0]) if user_id_row else None
        staff.user_id = user_id
        staff.staff_id = user_id  # Assuming staff_id is the same as user_id
        # Insert into staff table for additional fields
        insert_staff_query = """
            INSERT INTO staff (staff_id, jobtype, hourly_rate)
            VALUES (?, ?, ?)
        """
        self.db.execute_non_query(
            insert_staff_query,
            (staff.staff_id, staff.jobtype.value if staff.jobtype else None,
             staff.hourly_rate)
        )
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=staff.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(staff)
        )
        return staff

    def update_user_info(self, user_id: int, name: str, email: str, address: str, phone: str) -> Optional[User]:
        """
        Update user information.
        Args:
            user_id (int): ID of the user to update.
            name (str): New name of the user.
            email (str): New email of the user.
            address (str): New address of the user.
            phone (str): New phone number of the user.
        Returns:
            Optional[User]: Updated user object if found, otherwise None.
        """
        user = self.get_user_by_id(user_id)
        if user:
            old_data = self._object_to_dict(user)
            user.name = name
            user.email = email
            user.address = address
            user.phone = phone
            update_query = """
                UPDATE user
                SET name = ?, email = ?, address = ?, phone = ?
                WHERE user_id = ?
            """
            self.db.execute_non_query(
                update_query,
                (user.name, user.email, user.address, user.phone, user_id)
            )
            self.audit_log_service.log_audit_event(
                table_name="user",
                record_id=user_id,
                operation=OperationType.UPDATE,
                old_data=old_data,
                new_data=self._object_to_dict(user)
            )
        return user

    def _map_user_row_to_object(self, row: tuple) -> User:
        """
        Map a database row to the appropriate User subclass based on discriminator.
        Args:
            row: Tuple representing a database row.
        Returns:
            User: Instantiated User object or subclass (Admin, Staff, Customer).
        """
        # Assuming order: user_id, name, username, password, phone, email, address, discriminator
        discriminator = row[7]
        user_data = {
            "user_id": row[0],
            "name": row[1],
            "username": row[2],
            "password": row[3],
            "phone": row[4],
            "email": row[5],
            "address": row[6],
            "discriminator": discriminator
        }
        if discriminator == "admin":
            return Admin(**user_data)
        elif discriminator == "staff":
            # Fetch staff-specific fields
            staff_query = "SELECT jobtype, hourly_rate FROM staff WHERE staff_id = ?"
            staff_rows = self.db.execute_query(staff_query, (row[0],))
            if staff_rows:
                user_data.update({
                    "staff_id": row[0],
                    "jobtype": StaffJobType(staff_rows[0][0]) if staff_rows[0][0] else None,
                    "hourly_rate": staff_rows[0][1] if staff_rows[0][1] else 0
                })
            return Staff(**user_data)
        elif discriminator == "customer":
            return Customer(**user_data)
        return User(**user_data)

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        result = {}
        for key, value in vars(obj).items():
            if not key.startswith("_"):
                if isinstance(value, StaffJobType):
                    result[key] = value.value if value else None
                elif key == "password":
                    # Avoid logging plain text passwords
                    result[key] = "[REDACTED]"
                else:
                    result[key] = value
        return result
