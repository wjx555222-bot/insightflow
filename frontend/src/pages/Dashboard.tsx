import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ReactECharts from "echarts-for-react";
import {
  DollarSign,
  ShoppingCart,
  Users,
  Package,
  AlertTriangle,
  TrendingDown,
  Loader2,
} from "lucide-react";
import { dashboardApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type {
  DashboardSummary,
  SalesTrendPoint,
  TopProduct,
  TopCustomer,
  RegionPerformance,
  RecentOrder,
  DashboardAlert,
} from "@/types";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(v);

const fmtN = (v: number) => new Intl.NumberFormat("en-US").format(v);

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [salesTrend, setSalesTrend] = useState<SalesTrendPoint[]>([]);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [topCustomers, setTopCustomers] = useState<TopCustomer[]>([]);
  const [regionPerf, setRegionPerf] = useState<RegionPerformance[]>([]);
  const [recentOrders, setRecentOrders] = useState<RecentOrder[]>([]);
  const [alerts, setAlerts] = useState<DashboardAlert[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      try {
        const [s, st, tp, tc, rp, ro, al] = await Promise.all([
          dashboardApi.getSummary(),
          dashboardApi.getSalesTrend(),
          dashboardApi.getTopProducts(),
          dashboardApi.getTopCustomers(),
          dashboardApi.getRegionPerformance(),
          dashboardApi.getRecentOrders(),
          dashboardApi.getAlerts(),
        ]);
        setSummary(s.data);
        setSalesTrend(st.data);
        setTopProducts(tp.data);
        setTopCustomers(tc.data);
        setRegionPerf(rp.data);
        setRecentOrders(ro.data);
        setAlerts(al.data);
      } catch (e) {
        console.error("Dashboard load failed:", e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const kpis = [
    { title: "Total Revenue", value: summary ? fmt(summary.total_revenue) : "$0", icon: DollarSign, color: "text-green-600", bg: "bg-green-50", path: "/analytics" },
    { title: "Total Orders", value: summary ? fmtN(summary.total_orders) : "0", icon: ShoppingCart, color: "text-blue-600", bg: "bg-blue-50", path: "/orders" },
    { title: "Total Customers", value: summary ? fmtN(summary.total_customers) : "0", icon: Users, color: "text-purple-600", bg: "bg-purple-50", path: "/customers" },
    { title: "Total Products", value: summary ? fmtN(summary.total_products) : "0", icon: Package, color: "text-orange-600", bg: "bg-orange-50", path: "/products" },
    { title: "Overdue Amount", value: summary ? fmt(summary.overdue_amount) : "$0", icon: AlertTriangle, color: summary && summary.overdue_amount > 0 ? "text-red-600" : "text-gray-400", bg: summary && summary.overdue_amount > 0 ? "bg-red-50" : "bg-gray-50", path: "/orders?payment=overdue" },
    { title: "Low Stock", value: summary ? fmtN(summary.low_stock_count) : "0", icon: TrendingDown, color: summary && summary.low_stock_count > 0 ? "text-red-600" : "text-gray-400", bg: summary && summary.low_stock_count > 0 ? "bg-red-50" : "bg-gray-50", path: "/inventory" },
  ];

  const trendOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: salesTrend.map((p) => p.month), axisLabel: { rotate: 30 } },
    yAxis: { type: "value" as const, axisLabel: { formatter: (v: number) => (v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`) } },
    series: [{ name: "Revenue", type: "line", smooth: true, data: salesTrend.map((p) => p.revenue), areaStyle: { opacity: 0.12 }, itemStyle: { color: "#3b82f6" } }],
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
  };

  const statusCounts: Record<string, number> = {};
  recentOrders.forEach((o) => { statusCounts[o.payment_status] = (statusCounts[o.payment_status] || 0) + 1; });
  const pieOpt = {
    tooltip: { trigger: "item" as const },
    legend: { bottom: 0 },
    series: [{ type: "pie", radius: ["40%", "70%"], label: { show: true, formatter: "{b}: {c}" }, data: Object.entries(statusCounts).map(([name, value]) => ({ name, value })), color: ["#3b82f6", "#f59e0b", "#ef4444", "#6b7280", "#10b981"] }],
  };

  const prodOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "value" as const },
    yAxis: { type: "category" as const, data: topProducts.map((p) => p.product_name), axisLabel: { width: 120, overflow: "truncate" as const } },
    series: [{ name: "Revenue", type: "bar", data: topProducts.map((p) => p.total_revenue), itemStyle: { color: "#8b5cf6" } }],
    grid: { left: "3%", right: "8%", bottom: "3%", top: "3%", containLabel: true },
  };

  const regOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: regionPerf.map((r) => r.region) },
    yAxis: { type: "value" as const },
    series: [
      { name: "Revenue", type: "bar", data: regionPerf.map((r) => r.total_revenue), itemStyle: { color: "#10b981" } },
      { name: "Orders", type: "bar", data: regionPerf.map((r) => r.order_count), itemStyle: { color: "#f59e0b" } },
    ],
    legend: { bottom: 0 },
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold tracking-tight">Dashboard</h2>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {kpis.map((k) => (
          <Card key={k.title} className="cursor-pointer transition-shadow hover:shadow-md" onClick={() => navigate(k.path || "/")}>
            <CardContent className="flex items-center gap-3 p-4">
              <div className={`rounded-lg p-2 ${k.bg}`}>
                <k.icon className={`h-5 w-5 ${k.color}`} />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-muted-foreground">{k.title}</p>
                <p className="text-lg font-bold">{k.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Revenue Trend</CardTitle></CardHeader>
          <CardContent><ReactECharts option={trendOpt} style={{ height: 300 }} onEvents={{ click: () => navigate("/orders") }} /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Payment Status</CardTitle></CardHeader>
          <CardContent><ReactECharts option={pieOpt} style={{ height: 300 }} onEvents={{ click: (p: Record<string, string>) => navigate(`/orders?payment=${encodeURIComponent(p.name || "")}`) }} /></CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Top Products by Revenue</CardTitle></CardHeader>
          <CardContent><ReactECharts option={prodOpt} style={{ height: 300 }} onEvents={{ click: () => navigate("/products") }} /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Regional Performance</CardTitle></CardHeader>
          <CardContent><ReactECharts option={regOpt} style={{ height: 300 }} onEvents={{ click: (p: Record<string, string>) => navigate(`/customers?region=${encodeURIComponent(p.name || "")}`) }} /></CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2"><CardTitle className="text-base">Recent Orders</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead><TableHead>Customer</TableHead><TableHead>Date</TableHead>
                  <TableHead className="text-right">Amount</TableHead><TableHead>Payment</TableHead><TableHead>Shipment</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {recentOrders.length === 0 ? (
                  <TableRow><TableCell colSpan={6} className="text-center text-muted-foreground">No recent orders</TableCell></TableRow>
                ) : recentOrders.map((o) => (
                  <TableRow key={o.id} className="cursor-pointer hover:bg-muted/50" onClick={() => navigate("/orders")}>
                    <TableCell className="font-medium">#{o.id}</TableCell>
                    <TableCell>{o.customer_name}</TableCell>
                    <TableCell>{new Date(o.order_date).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">{fmt(o.total_amount)}</TableCell>
                    <TableCell><Badge variant={o.payment_status === "paid" ? "default" : o.payment_status === "overdue" ? "destructive" : "secondary"}>{o.payment_status}</Badge></TableCell>
                    <TableCell><Badge variant="outline">{o.shipment_status}</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Alerts</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.length === 0 ? (
                <p className="text-sm text-muted-foreground">No active alerts</p>
              ) : alerts.map((a, i) => (
                <div key={i} className={`rounded-lg border p-3 ${a.severity === "critical" ? "border-red-200 bg-red-50" : a.severity === "warning" ? "border-yellow-200 bg-yellow-50" : "border-blue-200 bg-blue-50"}`}>
                  <Badge variant={a.severity === "critical" ? "destructive" : "secondary"}>{a.alert_type}</Badge>
                  <p className="mt-1 text-sm">{a.message}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Top Customers</CardTitle></CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow><TableHead>Customer</TableHead><TableHead className="text-right">Spending</TableHead><TableHead className="text-right">Orders</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {topCustomers.length === 0 ? (
                <TableRow><TableCell colSpan={3} className="text-center text-muted-foreground">No data</TableCell></TableRow>
              ) : topCustomers.map((c) => (
                <TableRow key={c.customer_id} className="cursor-pointer hover:bg-muted/50" onClick={() => navigate("/customers")}>
                  <TableCell className="font-medium">{c.customer_name}</TableCell>
                  <TableCell className="text-right">{fmt(c.total_spending)}</TableCell>
                  <TableCell className="text-right">{c.order_count}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
