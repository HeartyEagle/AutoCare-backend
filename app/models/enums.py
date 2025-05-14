from enum import Enum

class VehicleBrand(str, Enum):
    TOYOTA = "Toyota"
    HONDA = "Honda"
    FORD = "Ford"
    CHEVROLET = "Chevrolet"
    NISSAN = "Nissan"
    BMW = "BMW"
    MERCEDES = "Mercedes-Benz"
    AUDI = "Audi"
    VOLKSWAGEN = "Volkswagen"
    HYUNDAI = "Hyundai"
    KIA = "Kia"


class VehicleType(str, Enum):
    SEDAN = "Sedan"
    SUV = "SUV"
    TRUCK = "Truck"
    VAN = "Van"
    COUPE = "Coupe"
    HATCHBACK = "Hatchback"
    CONVERTIBLE = "Convertible"
    WAGON = "Wagon"
    MOTORCYCLE = "Motorcycle"
    BUS = "Bus"


class VehicleColor(str, Enum):
    RED = "Red"
    BLUE = "Blue"
    GREEN = "Green"
    BLACK = "Black"
    WHITE = "White"
    SILVER = "Silver"
    YELLOW = "Yellow"
    ORANGE = "Orange"
    PURPLE = "Purple"
    PINK = "Pink"
    GREY = "Grey"


class OperationType(str, Enum):
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class RepairStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


class StaffJobType(str, Enum):
    # 漆工 - 负责车辆喷漆和表面修复 (Responsible for painting and surface repair)
    PAINT_WORKER = "Paint Worker"
    # 焊工 - 负责车辆金属焊接和结构修复 (Responsible for metal welding and structural repair)
    WELDER = "Welder"
    # 汽修工 - 负责车辆机械维修 (Responsible for mechanical repairs)
    AUTO_REPAIR_WORKER = "Auto Repair Worker"
    # 电工 - 负责车辆电气系统维修 (Responsible for electrical system repairs)
    AUTO_ELECTRICIAN = "Auto Electrician"
    # 钣金工 - 负责车身钣金修复 (Responsible for body sheet metal repair)
    SHEET_METAL_WORKER = "Sheet Metal Worker"
    # 诊断技师 - 负责车辆故障诊断 (Responsible for vehicle fault diagnosis)
    DIAGNOSTIC_TECHNICIAN = "Diagnostic Technician"
    # 服务顾问 - 负责客户沟通和服务协调 (Responsible for customer communication and service coordination)
    SERVICE_ADVISOR = "Service Advisor"
    # 配件专员 - 负责配件管理和采购 (Responsible for parts management and procurement)
    PARTS_SPECIALIST = "Parts Specialist"

    def __str__(self):
        return self.value
