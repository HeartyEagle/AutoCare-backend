from ..db.connection import Database
from ..models.user import User, Admin, Staff, Customer
from ..models.enums import StaffJobType, OperationType
from .audit import AuditLogService
from ..core.security import get_password_hash
from ..schemas.auth import UserCreate, StaffCreate
from typing import Optional, Dict, Any, List


class UserService:
    def __init__(self, db: Database):
        self.db = db
        self.audit_log_service = AuditLogService(db)

    def get_user_by_username(self, username: str) -> Optional[User]:
        rows = self.db.select_data(
            table_name="user",
            columns=["user_id", "name", "username", "password",
                     "phone", "email", "address", "discriminator"],
            where="username = ?",
            where_params=(username,),
            limit=1
        )
        return self._map_user_row_to_object(rows[0]) if rows else None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        rows = self.db.select_data(
            table_name="user",
            columns=["user_id", "name", "username", "password",
                     "phone", "email", "address", "discriminator"],
            where="user_id = ?",
            where_params=(user_id,),
            limit=1
        )
        return self._map_user_row_to_object(rows[0]) if rows else None

    def get_all_users(self) -> List[User]:
        rows = self.db.select_data(
            table_name="user",
            columns=["user_id", "name", "username", "password",
                     "phone", "email", "address", "discriminator"]
        )
        return [self._map_user_row_to_object(row) for row in rows]

    def get_all_staff(self) -> List[Staff]:
        rows = self.db.select_data(
            table_name="user u",
            columns=["u.user_id", "u.name", "u.username", "u.password", "u.phone", "u.email", "u.address", "u.discriminator",
                     "s.jobtype", "s.hourly_rate"],
            joins=["INNER JOIN staff s ON u.user_id = s.staff_id"],
            where="u.discriminator = 'staff'"
        )
        staff_list: List[Staff] = []
        for row in rows:
            data = {
                "user_id": row[0],
                "name": row[1],
                "username": row[2],
                "password": row[3],
                "phone": row[4],
                "email": row[5],
                "address": row[6],
                "discriminator": row[7],
                "staff_id": row[0],
                "jobtype": StaffJobType(row[8]) if row[8] else None,
                "hourly_rate": row[9] or 0
            }
            staff_list.append(Staff(**data))
        return staff_list

    def create_customer(self, user: UserCreate) -> Customer:
        hashed = get_password_hash(user.password)
        customer = Customer(
            name=user.name,
            username=user.username,
            password=hashed,
            phone=user.phone,
            email=user.email,
            address=user.address
        )

        self.db.insert_data(
            table_name="user",
            data={key: customer.asdict()[key] for key in customer.asdict(
            ).keys() if key not in ["customer_id"]}
        )
        row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        customer.user_id = int(row[0][0]) if row else None
        customer.customer_id = customer.user_id

        self.db.insert_data(table_name='customer', data={
                            "customer_id": customer.user_id})
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=customer.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(customer)
        )
        return customer

    def create_admin(self, user: UserCreate) -> Admin:
        hashed = get_password_hash(user.password)
        admin = Admin(
            name=user.name,
            username=user.username,
            password=hashed,
            phone=user.phone,
            email=user.email,
            address=user.address
        )
        self.db.insert_data(
            table_name="user",
            data=admin.asdict()
        )
        row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        admin.user_id = int(row[0][0]) if row else None
        admin.admin_id = admin.user_id
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=admin.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(admin)
        )
        return admin

    def create_staff(self, user: StaffCreate) -> Staff:
        hashed = get_password_hash(user.password)
        staff = Staff(
            name=user.name,
            username=user.username,
            password=hashed,
            phone=user.phone,
            email=user.email,
            address=user.address,
            jobtype=user.jobtype,
            hourly_rate=user.hourly_rate
        )
        # Insert into user table
        self.db.insert_data(
            table_name="user",
            data=staff.asdict()
        )
        row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        staff.user_id = int(row[0][0]) if row else None
        staff.staff_id = staff.user_id
        # Insert into staff details
        self.db.insert_data(
            table_name="staff",
            data={"staff_id": staff.staff_id, "jobtype": staff.jobtype.value if staff.jobtype else None,
                  "hourly_rate": staff.hourly_rate}
        )
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=staff.user_id,
            operation=OperationType.INSERT,
            new_data=self._object_to_dict(staff)
        )
        return staff

    def update_user_info(self, user_id: int, name: str, email: str, address: str, phone: str) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        old = self._object_to_dict(user)
        user.name, user.email, user.address, user.phone = name, email, address, phone
        self.db.execute_non_query(
            "UPDATE user SET name = ?, email = ?, address = ?, phone = ? WHERE user_id = ?",
            (user.name, user.email, user.address, user.phone, user_id)
        )
        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=user_id,
            operation=OperationType.UPDATE,
            old_data=old,
            new_data=self._object_to_dict(user)
        )
        return user

    def _map_user_row_to_object(self, row: tuple) -> User:
        disc = row[7]
        base = {
            "user_id": row[0], "name": row[1], "username": row[2],
            "password": row[3], "phone": row[4], "email": row[5],
            "address": row[6], "discriminator": disc
        }
        if disc == "admin":
            return Admin(**base)
        if disc == "staff":
            details = self.db.select_data(
                table_name="staff",
                columns=["jobtype", "hourly_rate"],
                where="staff_id = ?",
                where_params=(row[0],),
                limit=1
            )
            if details:
                base.update({"staff_id": row[0], "jobtype": StaffJobType(
                    details[0][0]), "hourly_rate": details[0][1] or 0})
            return Staff(**base)
        if disc == "customer":
            return Customer(**base)
        return User(**base)

    def _object_to_dict(self, obj: Any) -> Dict[str, Any]:
        if not obj:
            return {}
        result: Dict[str, Any] = {}
        for k, v in vars(obj).items():
            if k.startswith("_"):
                continue
            if isinstance(v, StaffJobType):
                result[k] = v.value
            elif k == "password":
                result[k] = "[REDACTED]"
            else:
                result[k] = v
        return result
