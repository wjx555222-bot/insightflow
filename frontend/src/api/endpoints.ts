import client from "./client";
import type {
  User,
  Customer,
  Product,
  Order,
  OrderListItem,
  DashboardSummary,
  SalesTrendPoint,
  TopProduct,
  TopCustomer,
  RegionPerformance,
  RecentOrder,
  DashboardAlert,
  RevenueAnalytics,
  GrowthAnalytics,
  CustomerRepeatRate,
  ProductPerformance,
  AnalyticsRegionPerformance,
  PaymentDelay,
  SalesTargetStatus,
  AIResponse,
  PaginatedResponse,
  ImportSummary,
  UploadHistory,
  AuditLog,
  Inventory,
} from "@/types";

// ====== Auth ======
export const auth = {
  login: (email: string, password: string) =>
    client.post<{ access_token: string; token_type: string }>("/auth/login", {
      email,
      password,
    }),

  register: (data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
  }) =>
    client.post<{ access_token: string; token_type: string }>(
      "/auth/register",
      data,
    ),

  getMe: () => client.get<User>("/auth/me"),
};

// ====== Users ======
export const usersApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    client.get<User[]>("/users", { params }),

  create: (data: {
    email: string;
    password: string;
    full_name?: string;
    role?: string;
  }) => client.post<User>("/users", data),

  update: (id: number, data: Partial<{ email: string; full_name: string; role_id: number; is_active: boolean }>) =>
    client.put<User>(`/users/${id}`, data),

  delete: (id: number) => client.delete(`/users/${id}`),
};

// ====== Dashboard ======
export const dashboardApi = {
  getSummary: () => client.get<DashboardSummary>("/dashboard/summary"),

  getSalesTrend: (params?: { months?: number }) =>
    client.get<SalesTrendPoint[]>("/dashboard/sales-trend", { params }),

  getTopProducts: (params?: { limit?: number }) =>
    client.get<TopProduct[]>("/dashboard/top-products", { params }),

  getTopCustomers: (params?: { limit?: number }) =>
    client.get<TopCustomer[]>("/dashboard/top-customers", { params }),

  getRegionPerformance: () =>
    client.get<RegionPerformance[]>("/dashboard/region-performance"),

  getRecentOrders: (params?: { limit?: number }) =>
    client.get<RecentOrder[]>("/dashboard/recent-orders", { params }),

  getAlerts: () => client.get<DashboardAlert[]>("/dashboard/alerts"),
};

// ====== Orders ======
export const ordersApi = {
  list: (params?: {
    search?: string;
    date_from?: string;
    date_to?: string;
    payment_status?: string;
    shipment_status?: string;
    region?: string;
    sort_by?: string;
    sort_order?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<PaginatedResponse<OrderListItem>>("/orders", { params }),

  get: (id: number) => client.get<Order>(`/orders/${id}`),

  create: (data: {
    customer_id: number;
    items: Array<{ product_id: number; quantity: number; unit_price: number }>;
    region?: string;
    salesperson?: string;
    payment_status?: string;
    shipment_status?: string;
  }) => client.post<Order>("/orders", data),

  update: (
    id: number,
    data: Partial<{
      customer_id: number;
      region: string;
      salesperson: string;
      payment_status: string;
      shipment_status: string;
    }>,
  ) => client.put<Order>(`/orders/${id}`, data),

  delete: (id: number) => client.delete(`/orders/${id}`),
};

// ====== Customers ======
export const customersApi = {
  list: (params?: {
    search?: string;
    region?: string;
    customer_type?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<PaginatedResponse<Customer>>("/customers", { params }),

  get: (id: number) => client.get<Customer>(`/customers/${id}`),

  create: (data: Partial<Customer>) =>
    client.post<Customer>("/customers", data),

  update: (id: number, data: Partial<Customer>) =>
    client.put<Customer>(`/customers/${id}`, data),

  delete: (id: number) => client.delete(`/customers/${id}`),

  getOrders: (id: number) =>
    client.get<PaginatedResponse<OrderListItem>>(`/customers/${id}/orders`),
};

// ====== Products ======
export const productsApi = {
  list: (params?: {
    search?: string;
    category?: string;
    product_status?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<PaginatedResponse<Product>>("/products", { params }),

  get: (id: number) => client.get<Product>(`/products/${id}`),

  create: (data: Partial<Product>) => client.post<Product>("/products", data),

  update: (id: number, data: Partial<Product>) =>
    client.put<Product>(`/products/${id}`, data),

  delete: (id: number) => client.delete(`/products/${id}`),
};

// ====== Inventory ======
export const inventoryApi = {
  list: (params?: { skip?: number; limit?: number }) =>
    client.get<PaginatedResponse<Inventory>>("/products/inventory", {
      params,
    }),

  getLowStock: () =>
    client.get<Inventory[]>("/products/inventory/low-stock"),
};

// ====== Upload ======
export const uploadApi = {
  uploadOrders: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post<ImportSummary>("/upload/orders", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  uploadCustomers: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post<ImportSummary>("/upload/customers", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  uploadProducts: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post<ImportSummary>("/upload/products", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  uploadInventory: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return client.post<ImportSummary>("/upload/inventory", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  getHistory: (params?: { skip?: number; limit?: number }) =>
    client.get<PaginatedResponse<UploadHistory>>("/upload/history", {
      params,
    }),
};

// ====== Analytics ======
export const analyticsApi = {
  getRevenue: (params?: { year?: number }) =>
    client.get<RevenueAnalytics>("/analytics/revenue", { params }),

  getGrowth: (params?: { period?: string }) =>
    client.get<GrowthAnalytics>("/analytics/growth", { params }),

  getCustomerRepeatRate: () =>
    client.get<CustomerRepeatRate>("/analytics/customer-repeat-rate"),

  getProductPerformance: (params?: { category?: string }) =>
    client.get<ProductPerformance[]>("/analytics/product-performance", {
      params,
    }),

  getRegionPerformance: () =>
    client.get<AnalyticsRegionPerformance[]>(
      "/analytics/region-performance",
    ),

  getPaymentDelay: () =>
    client.get<PaymentDelay[]>("/analytics/payment-delay"),

  getSalesTargets: (params?: { year?: number }) =>
    client.get<SalesTargetStatus[]>("/analytics/sales-targets", { params }),
};

// ====== AI ======
export const aiApi = {
  ask: (question: string) =>
    client.post<AIResponse>("/ai/ask", { question }),

  generateReport: (report_type: string, additional_context?: string) =>
    client.post<AIResponse>("/ai/generate-report", {
      report_type,
      additional_context,
    }),

  explainTrend: (metric: string, period?: string) =>
    client.post<AIResponse>("/ai/explain-trend", { metric, period }),

  inventorySuggestion: (category?: string) =>
    client.post<AIResponse>("/ai/inventory-suggestion", { category }),
};

// ====== Export ======
export const exportApi = {
  salesCSV: () =>
    client.get("/export/sales.csv", { responseType: "blob" }),

  customersCSV: () =>
    client.get("/export/customers.csv", { responseType: "blob" }),

  inventoryCSV: () =>
    client.get("/export/inventory.csv", { responseType: "blob" }),

  businessReportPDF: () =>
    client.get("/export/business-report.pdf", { responseType: "blob" }),

  orderPDF: (id: number) =>
    client.get(`/export/orders/${id}.pdf`, { responseType: "blob" }),
};

// ====== Audit Logs ======
export const auditLogsApi = {
  list: (params?: {
    user_id?: number;
    action?: string;
    entity_type?: string;
    date_from?: string;
    date_to?: string;
    skip?: number;
    limit?: number;
  }) =>
    client.get<PaginatedResponse<AuditLog>>("/audit-logs", { params }),
};

// ====== Batch Operations ======
export const batchApi = {
  deleteOrders: (ids: number[]) =>
    client.post<{ deleted: number; failed: number; errors: string[] }>("/batch/orders/delete", { ids }),

  deleteCustomers: (ids: number[]) =>
    client.post<{ deleted: number; failed: number; errors: string[] }>("/batch/customers/delete", { ids }),

  deleteProducts: (ids: number[]) =>
    client.post<{ deleted: number; failed: number; errors: string[] }>("/batch/products/delete", { ids }),
};
