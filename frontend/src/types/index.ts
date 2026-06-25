// ====== Core Entities ======

export interface RoleInfo {
  id: number;
  name: string;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: RoleInfo;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: number;
  name: string;
  company: string | null;
  email: string | null;
  phone: string | null;
  region: string | null;
  customer_type: string | null;
  total_spending: number;
  last_purchase_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  contact_person: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
}

export interface Product {
  id: number;
  name: string;
  category: string | null;
  supplier_id: number | null;
  unit_price: number;
  cost_price: number | null;
  current_stock: number;
  reorder_level: number;
  status: string;
  created_at: string;
  updated_at: string;
  supplier: Supplier | null;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string | null;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface Order {
  id: number;
  customer_id: number;
  customer_name: string | null;
  order_date: string;
  payment_status: string;
  shipment_status: string;
  region: string | null;
  salesperson: string | null;
  total_amount: number;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderListItem {
  id: number;
  customer_id: number;
  customer_name: string | null;
  order_date: string;
  payment_status: string;
  shipment_status: string;
  region: string | null;
  salesperson: string | null;
  total_amount: number;
}

export interface Inventory {
  id: number;
  product_id: number;
  product_name: string | null;
  warehouse: string;
  quantity: number;
  last_updated: string;
  reorder_level: number;
  current_stock: number;
}

export interface Payment {
  id: number;
  order_id: number;
  amount: number;
  method: string;
  status: string;
  due_date: string;
  paid_date: string | null;
  created_at: string;
}

export interface Shipment {
  id: number;
  order_id: number;
  carrier: string;
  tracking_number: string;
  status: string;
  shipped_date: string | null;
  delivered_date: string | null;
}

export interface SalesTarget {
  id: number;
  region: string;
  target_amount: number;
  period: string;
  year: number;
  month: number | null;
}

export interface UploadHistory {
  id: number;
  user_id: number;
  file_type: string;
  file_name: string;
  total_rows: number;
  success_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  action: string;
  entity_type: string;
  entity_id: number | null;
  details: string | null;
  ip_address: string | null;
  timestamp: string;
}

export interface AIReport {
  id: number;
  user_id: number;
  report_type: string;
  question: string;
  response: string;
  data_context: string | null;
  created_at: string;
}

// ====== Dashboard Types ======

export interface DashboardSummary {
  total_revenue: number;
  total_orders: number;
  total_customers: number;
  total_products: number;
  overdue_amount: number;
  low_stock_count: number;
}

export interface SalesTrendPoint {
  month: string;
  revenue: number;
  orders: number;
}

export interface TopProduct {
  product_id: number;
  product_name: string;
  total_revenue: number;
  total_quantity: number;
}

export interface TopCustomer {
  customer_id: number;
  customer_name: string;
  total_spending: number;
  order_count: number;
}

export interface RegionPerformance {
  region: string;
  total_revenue: number;
  order_count: number;
}

export interface RecentOrder {
  id: number;
  customer_name: string;
  order_date: string;
  total_amount: number;
  payment_status: string;
  shipment_status: string;
}

export interface DashboardAlert {
  alert_type: string;
  message: string;
  severity: string;
  entity_id: number | null;
}

// ====== Analytics Types ======

export interface MonthRevenue {
  month: string;
  revenue: number;
}

export interface RevenueAnalytics {
  monthly_data: MonthRevenue[];
  total_revenue: number;
  avg_order_value: number;
}

export interface GrowthAnalytics {
  current_period_revenue: number;
  previous_period_revenue: number;
  growth_rate: number;
  growth_amount: number;
}

export interface CustomerRepeatRate {
  repeat_customers: number;
  total_customers: number;
  repeat_rate: number;
}

export interface ProductPerformance {
  product_id: number;
  product_name: string;
  category: string;
  total_revenue: number;
  total_quantity: number;
  profit_margin: number;
}

export interface AnalyticsRegionPerformance {
  region: string;
  revenue: number;
  orders: number;
  avg_order_value: number;
}

export interface PaymentDelay {
  order_id: number;
  customer_name: string;
  amount: number;
  due_date: string;
  days_overdue: number;
}

export interface SalesTargetStatus {
  region: string;
  target: number;
  actual: number;
  completion_rate: number;
}

// ====== AI Types ======

export interface AIResponse {
  short_answer: string;
  data_evidence: string[];
  reasoning: string;
  suggested_actions: string[];
  confidence: string;
}

// ====== Generic Types ======

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface ImportSummary {
  total_rows: number;
  success_rows: number;
  failed_rows: number;
  duplicate_rows: number;
  errors: string[];
}
