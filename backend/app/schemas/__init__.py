from app.schemas.ai import (
    AIAskRequest,
    AIInventoryRequest,
    AIReportRequest,
    AIResponse,
    AITrendRequest,
)
from app.schemas.analytics import (
    CustomerRepeatRate,
    GrowthAnalytics,
    MonthRevenue,
    PaymentDelay,
    ProductPerformance,
    RegionPerformance,
    RevenueAnalytics,
    SalesTargetStatus,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.customer import CustomerCreate, CustomerResponse, CustomerUpdate
from app.schemas.dashboard import (
    DashboardAlert,
    DashboardSummary,
    RecentOrder,
    RegionPerformance as DashboardRegionPerformance,
    SalesTrendPoint,
    TopCustomer,
    TopProduct,
)
from app.schemas.order import (
    OrderCreate,
    OrderItemCreate,
    OrderItemResponse,
    OrderListResponse,
    OrderResponse,
    OrderUpdate,
)
from app.schemas.product import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
    SupplierResponse,
)
from app.schemas.upload import ImportSummary, UploadHistoryResponse
from app.schemas.user import RoleResponse, UserCreate, UserResponse, UserUpdate

__all__ = [
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "TokenResponse",
    # User
    "RoleResponse",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    # Customer
    "CustomerCreate",
    "CustomerResponse",
    "CustomerUpdate",
    # Product
    "ProductCreate",
    "ProductResponse",
    "ProductUpdate",
    "SupplierResponse",
    # Order
    "OrderCreate",
    "OrderItemCreate",
    "OrderItemResponse",
    "OrderListResponse",
    "OrderResponse",
    "OrderUpdate",
    # Dashboard
    "DashboardAlert",
    "DashboardSummary",
    "DashboardRegionPerformance",
    "RecentOrder",
    "SalesTrendPoint",
    "TopCustomer",
    "TopProduct",
    # Analytics
    "CustomerRepeatRate",
    "GrowthAnalytics",
    "MonthRevenue",
    "PaymentDelay",
    "ProductPerformance",
    "RegionPerformance",
    "RevenueAnalytics",
    "SalesTargetStatus",
    # Upload
    "ImportSummary",
    "UploadHistoryResponse",
    # AI
    "AIAskRequest",
    "AIInventoryRequest",
    "AIReportRequest",
    "AIResponse",
    "AITrendRequest",
]
