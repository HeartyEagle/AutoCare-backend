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
            where=f"username = '{username}'",
            limit=1
        )
        print(rows)
        return self._map_user_row_to_object(rows[0]) if rows else None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        print(type(user_id))
        rows = self.db.select_data(
            table_name="user",
            columns=["user_id", "name", "username", "password",
                     "phone", "email", "address", "discriminator"],
            where=f"user_id = {user_id}",
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

        print(customer.asdict(only_parent=True))

        self.db.insert_data(
            table_name="user",
            data=customer.asdict(only_parent=True)
        )
        row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        customer.user_id = int(row[0][0]) if row else None
        customer.customer_id = customer.user_id

        self.db.insert_data(table_name="customer", data={
            "customer_id": customer.customer_id
        })

        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=customer.user_id,
            operation=OperationType.INSERT,
            new_data=customer.asdict()

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
            data=admin.asdict(only_parent=True)
        )
        row = self.db.execute_query("SELECT LAST_INSERT_ID();")
        admin.user_id = int(row[0][0]) if row else None
        admin.admin_id = admin.user_id

        self.db.insert_data(table_name="admin", data={
            "admin_id": admin.admin_id
        })

        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=admin.user_id,
            operation=OperationType.INSERT,
            new_data=admin.asdict()
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
            data=staff.asdict(only_parent=True)
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
            new_data=staff.asdict()
        )
        return staff

    def update_user_info(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update any fields of user (name, email, address, phone, username, password...)
        Only non-None fields will be updated.
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        old = user.asdict()
        data = {}
        # Only update if not None
        if name is not None:
            user.name = name
            data["name"] = name
        if email is not None:
            user.email = email
            data["email"] = email
        if address is not None:
            user.address = address
            data["address"] = address
        if phone is not None:
            user.phone = phone
            data["phone"] = phone
        if username is not None:
            user.username = username
            data["username"] = username
        if password is not None:
            password = get_password_hash(password)
            user.password = password
            data["password"] = password

        if not data:
            # 没有任何字段需要更新
            return user

        self.db.update_data(table_name="user", data=data,
                            where=f"user_id = {user_id}")

        self.audit_log_service.log_audit_event(
            table_name="user",
            record_id=user_id,
            operation=OperationType.UPDATE,
            old_data=old,
            new_data=user.asdict()
        )
        return self.get_user_by_id(user_id)  # 刷新后的最新对象

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户，级联清理子表（admin/staff/customer），自动审计。
        :param user_id: 用户ID
        :return: 删除成功返回 True，否则 False
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        # 清理角色对应子表
        if user.discriminator == "admin":
            self.db.delete_data(table_name="admin",
                                where=f"admin_id = {user_id}")
        elif user.discriminator == "staff":
            self.db.delete_data(table_name="staff",
                                where=f"staff_id = {user_id}")
        elif user.discriminator == "customer":
            self.db.delete_data(table_name="customer",
                                where=f"customer_id = {user_id}")

        # 主user表
        deleted = self.db.delete_data(
            table_name="user", where=f"user_id = {user_id}")

        # 审计日志
        if deleted:
            self.audit_log_service.log_audit_event(
                table_name="user",
                record_id=user_id,
                operation=OperationType.DELETE,
                old_data=user.asdict(),
                new_data=None
            )
        return bool(deleted)

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
                where=f"staff_id = {row[0]}",
                limit=1
            )
            if details:
                base.update({"staff_id": row[0], "jobtype": StaffJobType(
                    details[0][0]), "hourly_rate": details[0][1] or 0})
            return Staff(**base)
        if disc == "customer":
            return Customer(**base)
        return User(**base)
