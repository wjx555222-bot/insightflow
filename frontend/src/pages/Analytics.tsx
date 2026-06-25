import { useEffect, useState } from "react";
import ReactECharts from "echarts-for-react";
import { TrendingUp, Users, DollarSign, Loader2 } from "lucide-react";
import { analyticsApi } from "@/api/endpoints";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type {
  RevenueAnalytics, GrowthAnalytics, CustomerRepeatRate,
  ProductPerformance, AnalyticsRegionPerformance, PaymentDelay, SalesTargetStatus,
} from "@/types";

const fmt = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);
const pct = (v: number) => `${v.toFixed(1)}%`;

export default function Analytics() {
  const [loading, setLoading] = useState(true);
  const [revenue, setRevenue] = useState<RevenueAnalytics | null>(null);
  const [growth, setGrowth] = useState<GrowthAnalytics | null>(null);
  const [repeatRate, setRepeatRate] = useState<CustomerRepeatRate | null>(null);
  const [products, setProducts] = useState<ProductPerformance[]>([]);
  const [regions, setRegions] = useState<AnalyticsRegionPerformance[]>([]);
  const [delays, setDelays] = useState<PaymentDelay[]>([]);
  const [targets, setTargets] = useState<SalesTargetStatus[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [r, g, rr, pp, rg, pd, st] = await Promise.all([
          analyticsApi.getRevenue(), analyticsApi.getGrowth(), analyticsApi.getCustomerRepeatRate(),
          analyticsApi.getProductPerformance(), analyticsApi.getRegionPerformance(),
          analyticsApi.getPaymentDelay(), analyticsApi.getSalesTargets(),
        ]);
        setRevenue(r.data); setGrowth(g.data); setRepeatRate(rr.data);
        setProducts(pp.data); setRegions(rg.data); setDelays(pd.data); setTargets(st.data);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    };
    load();
  }, []);

  if (loading) return <div className="flex h-64 items-center justify-center"><Loader2 className="h-8 w-8 animate-spin" /></div>;

  const revOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: revenue?.monthly_data.map((m) => m.month) || [], axisLabel: { rotate: 30 } },
    yAxis: { type: "value" as const, axisLabel: { formatter: (v: number) => v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}` } },
    series: [{ name: "Revenue", type: "line", smooth: true, data: revenue?.monthly_data.map((m) => m.revenue) || [], areaStyle: { opacity: 0.1 }, itemStyle: { color: "#3b82f6" } }],
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
  };

  const prodOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: products.map((p) => p.product_name), axisLabel: { rotate: 45, fontSize: 10 } },
    yAxis: { type: "value" as const },
    series: [
      { name: "Revenue", type: "bar", data: products.map((p) => p.total_revenue), itemStyle: { color: "#8b5cf6" } },
      { name: "Quantity", type: "bar", data: products.map((p) => p.total_quantity), itemStyle: { color: "#f59e0b" } },
    ],
    legend: { bottom: 0 },
    grid: { left: "3%", right: "4%", bottom: "20%", containLabel: true },
  };

  const regOpt = {
    tooltip: { trigger: "axis" as const },
    xAxis: { type: "category" as const, data: regions.map((r) => r.region) },
    yAxis: [
      { type: "value" as const, name: "Revenue" },
      { type: "value" as const, name: "Orders" },
    ],
    series: [
      { name: "Revenue", type: "bar", data: regions.map((r) => r.revenue), itemStyle: { color: "#10b981" } },
      { name: "Avg Order", type: "line", yAxisIndex: 1, data: regions.map((r) => r.avg_order_value), itemStyle: { color: "#ef4444" } },
    ],
    legend: { bottom: 0 },
    grid: { left: "3%", right: "4%", bottom: "15%", containLabel: true },
  };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold tracking-tight">Analytics</h2>

      {/* KPI Row */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="rounded-lg bg-blue-50 p-3"><TrendingUp className="h-6 w-6 text-blue-600" /></div>
            <div>
              <p className="text-xs text-muted-foreground">Growth Rate</p>
              <p className="text-2xl font-bold">{growth ? pct(growth.growth_rate) : "—"}</p>
              <p className="text-xs text-muted-foreground">
                {growth ? `vs previous period (${fmt(growth.growth_amount)})` : ""}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="rounded-lg bg-purple-50 p-3"><Users className="h-6 w-6 text-purple-600" /></div>
            <div>
              <p className="text-xs text-muted-foreground">Customer Repeat Rate</p>
              <p className="text-2xl font-bold">{repeatRate ? pct(repeatRate.repeat_rate) : "—"}</p>
              <p className="text-xs text-muted-foreground">
                {repeatRate ? `${repeatRate.repeat_customers} of ${repeatRate.total_customers} customers` : ""}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-4 p-4">
            <div className="rounded-lg bg-green-50 p-3"><DollarSign className="h-6 w-6 text-green-600" /></div>
            <div>
              <p className="text-xs text-muted-foreground">Avg Order Value</p>
              <p className="text-2xl font-bold">{revenue ? fmt(revenue.avg_order_value) : "—"}</p>
              <p className="text-xs text-muted-foreground">
                {revenue ? `Total: ${fmt(revenue.total_revenue)}` : ""}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Monthly Revenue Trend</CardTitle></CardHeader>
          <CardContent><ReactECharts option={revOpt} style={{ height: 320 }} /></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Product Performance</CardTitle></CardHeader>
          <CardContent><ReactECharts option={prodOpt} style={{ height: 320 }} /></CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-base">Regional Performance</CardTitle></CardHeader>
        <CardContent><ReactECharts option={regOpt} style={{ height: 320 }} /></CardContent>
      </Card>

      {/* Tables */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Payment Delays</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Order</TableHead><TableHead>Customer</TableHead><TableHead className="text-right">Amount</TableHead><TableHead>Due Date</TableHead><TableHead className="text-right">Days Overdue</TableHead></TableRow></TableHeader>
              <TableBody>
                {delays.length === 0 ? <TableRow><TableCell colSpan={5} className="text-center text-muted-foreground">No overdue payments</TableCell></TableRow>
                : delays.map((d) => (
                  <TableRow key={d.order_id}>
                    <TableCell>#{d.order_id}</TableCell><TableCell>{d.customer_name}</TableCell>
                    <TableCell className="text-right">{fmt(d.amount)}</TableCell>
                    <TableCell>{d.due_date}</TableCell>
                    <TableCell className="text-right"><Badge variant={d.days_overdue > 30 ? "destructive" : "secondary"}>{d.days_overdue} days</Badge></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-base">Sales Targets</CardTitle></CardHeader>
          <CardContent>
            <Table>
              <TableHeader><TableRow><TableHead>Region</TableHead><TableHead className="text-right">Target</TableHead><TableHead className="text-right">Actual</TableHead><TableHead>Progress</TableHead></TableRow></TableHeader>
              <TableBody>
                {targets.length === 0 ? <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No targets set</TableCell></TableRow>
                : targets.map((t) => (
                  <TableRow key={t.region}>
                    <TableCell>{t.region}</TableCell>
                    <TableCell className="text-right">{fmt(t.target)}</TableCell>
                    <TableCell className="text-right">{fmt(t.actual)}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-24 rounded-full bg-gray-200">
                          <div className="h-2 rounded-full bg-blue-500" style={{ width: `${Math.min(100, t.completion_rate * 100)}%` }} />
                        </div>
                        <span className="text-xs">{pct(t.completion_rate)}</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
