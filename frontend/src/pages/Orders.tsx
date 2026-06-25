import { useEffect, useState, useCallback } from "react";
import { Plus, Search, Loader2, Eye, Pencil, Trash2, X, CheckSquare, Square, Download } from "lucide-react";
import { ordersApi, batchApi, exportApi } from "@/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter,
} from "@/components/ui/dialog";
import type { Order, OrderListItem } from "@/types";

const fmt = (v: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);

const payBadge = (s: string) =>
  s === "paid" ? "default" : s === "overdue" ? "destructive" : "secondary";

const shipBadge = (s: string) =>
  s === "delivered" ? "default" : s === "shipped" ? "secondary" : "outline";

interface FormItem {
  product_id: string;
  quantity: string;
  unit_price: string;
}

export default function Orders() {
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [payFilter, setPayFilter] = useState("");
  const [shipFilter, setShipFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [sortBy, setSortBy] = useState("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(0);
  const limit = 20;

  // Dialogs
  const [viewOrder, setViewOrder] = useState<Order | null>(null);
  const [editDialog, setEditDialog] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);

  // Batch selection
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchDeleting, setBatchDeleting] = useState(false);

  const handleBatchDelete = async () => {
    if (!confirm(`Delete ${selected.size} selected orders?`)) return;
    setBatchDeleting(true);
    try {
      await batchApi.deleteOrders(Array.from(selected));
      setSelected(new Set());
      fetchOrders();
    } catch (e) { console.error(e); }
    setBatchDeleting(false);
  };

  const handleDownloadPDF = async (id: number) => {
    try {
      const res = await exportApi.orderPDF(id);
      const blob = new Blob([res.data as unknown as BlobPart], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `order-${id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) { console.error("PDF download failed:", e); }
  };

  // Create/Edit form state
  const [formCustomerId, setFormCustomerId] = useState("");
  const [formRegion, setFormRegion] = useState("");
  const [formSalesperson, setFormSalesperson] = useState("");
  const [formPayStatus, setFormPayStatus] = useState("pending");
  const [formShipStatus, setFormShipStatus] = useState("pending");
  const [formItems, setFormItems] = useState<FormItem[]>([{ product_id: "", quantity: "1", unit_price: "" }]);
  const [saving, setSaving] = useState(false);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { skip: page * limit, limit };
      if (search) params.search = search;
      if (payFilter) params.payment_status = payFilter;
      if (shipFilter) params.shipment_status = shipFilter;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (sortBy) params.sort_by = sortBy;
      params.sort_order = sortOrder;
      const res = await ordersApi.list(params as Parameters<typeof ordersApi.list>[0]);
      setOrders(res.data.items);
      setTotal(res.data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [search, payFilter, shipFilter, dateFrom, dateTo, sortBy, sortOrder, page]);

  useEffect(() => { fetchOrders(); }, [fetchOrders]);

  const totalPages = Math.max(1, Math.ceil(total / limit));

  const openCreate = () => {
    setEditingOrder(null);
    setFormCustomerId(""); setFormRegion(""); setFormSalesperson("");
    setFormPayStatus("pending"); setFormShipStatus("pending");
    setFormItems([{ product_id: "", quantity: "1", unit_price: "" }]);
    setEditDialog(true);
  };

  const openEdit = async (id: number) => {
    try {
      const res = await ordersApi.get(id);
      const o = res.data;
      setEditingOrder(o);
      setFormCustomerId(String(o.customer_id));
      setFormRegion(o.region || "");
      setFormSalesperson(o.salesperson || "");
      setFormPayStatus(o.payment_status);
      setFormShipStatus(o.shipment_status);
      setFormItems(o.items.map((it) => ({
        product_id: String(it.product_id),
        quantity: String(it.quantity),
        unit_price: String(it.unit_price),
      })));
      setEditDialog(true);
    } catch (e) { console.error(e); }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editingOrder) {
        await ordersApi.update(editingOrder.id, {
          customer_id: Number(formCustomerId) || undefined,
          region: formRegion || undefined,
          salesperson: formSalesperson || undefined,
          payment_status: formPayStatus,
          shipment_status: formShipStatus,
        });
      } else {
        await ordersApi.create({
          customer_id: Number(formCustomerId),
          region: formRegion || undefined,
          salesperson: formSalesperson || undefined,
          payment_status: formPayStatus,
          shipment_status: formShipStatus,
          items: formItems.filter((it) => it.product_id && it.quantity).map((it) => ({
            product_id: Number(it.product_id),
            quantity: Number(it.quantity),
            unit_price: Number(it.unit_price),
          })),
        });
      }
      setEditDialog(false);
      fetchOrders();
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await ordersApi.delete(deleteId);
      setDeleteId(null);
      fetchOrders();
    } catch (e) { console.error(e); }
  };

  const clearFilters = () => {
    setSearch(""); setPayFilter(""); setShipFilter("");
    setDateFrom(""); setDateTo(""); setSortBy("date"); setSortOrder("desc");
    setPage(0);
  };

  const addItem = () => setFormItems([...formItems, { product_id: "", quantity: "1", unit_price: "" }]);
  const removeItem = (i: number) => setFormItems(formItems.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: keyof FormItem, value: string) => {
    const next = [...formItems];
    next[i] = { ...next[i], [field]: value };
    setFormItems(next);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Orders</h2>
        <Button onClick={openCreate}><Plus className="mr-2 h-4 w-4" />New Order</Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[180px] flex-1">
            <Label className="text-xs">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-8" placeholder="Customer, product, ID..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} />
            </div>
          </div>
          <div>
            <Label className="text-xs">Payment</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={payFilter} onChange={(e) => { setPayFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="paid">Paid</option>
              <option value="overdue">Overdue</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div>
            <Label className="text-xs">Shipment</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={shipFilter} onChange={(e) => { setShipFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="shipped">Shipped</option>
              <option value="delivered">Delivered</option>
            </select>
          </div>
          <div>
            <Label className="text-xs">From</Label>
            <Input type="date" value={dateFrom} onChange={(e) => { setDateFrom(e.target.value); setPage(0); }} />
          </div>
          <div>
            <Label className="text-xs">To</Label>
            <Input type="date" value={dateTo} onChange={(e) => { setDateTo(e.target.value); setPage(0); }} />
          </div>
          <div>
            <Label className="text-xs">Sort</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
              <option value="date">Date</option>
              <option value="amount">Amount</option>
              <option value="status">Status</option>
            </select>
          </div>
          <Button variant="outline" size="sm" onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}>
            {sortOrder === "desc" ? "↓" : "↑"}
          </Button>
          <Button variant="ghost" size="sm" onClick={clearFilters}>Clear</Button>
        </CardContent>
      </Card>

      {/* Batch action bar */}
      {selected.size > 0 && (
        <div className="flex items-center gap-3 rounded-lg border bg-blue-50 p-3">
          <span className="text-sm font-medium">{selected.size} selected</span>
          <Button variant="destructive" size="sm" disabled={batchDeleting} onClick={handleBatchDelete}>
            {batchDeleting ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Trash2 className="mr-1 h-4 w-4" />}
            Delete Selected
          </Button>
          <Button variant="outline" size="sm" onClick={() => setSelected(new Set())}>Clear Selection</Button>
        </div>
      )}

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]">
                    <button onClick={() => {
                      if (selected.size === orders.length) setSelected(new Set());
                      else setSelected(new Set(orders.map(o => o.id)));
                    }}>
                      {selected.size === orders.length && orders.length > 0 ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                    </button>
                  </TableHead>
                  <TableHead>ID</TableHead><TableHead>Customer</TableHead><TableHead>Date</TableHead>
                  <TableHead>Region</TableHead><TableHead>Salesperson</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead>Payment</TableHead><TableHead>Shipment</TableHead><TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.length === 0 ? (
                  <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground py-8">No orders found</TableCell></TableRow>
                ) : orders.map((o) => (
                  <TableRow key={o.id}>
                    <TableCell>
                      <button onClick={() => {
                        const next = new Set(selected);
                        next.has(o.id) ? next.delete(o.id) : next.add(o.id);
                        setSelected(next);
                      }}>
                        {selected.has(o.id) ? <CheckSquare className="h-4 w-4 text-blue-600" /> : <Square className="h-4 w-4 text-muted-foreground" />}
                      </button>
                    </TableCell>
                    <TableCell className="font-medium">#{o.id}</TableCell>
                    <TableCell>{o.customer_name || "—"}</TableCell>
                    <TableCell>{new Date(o.order_date).toLocaleDateString()}</TableCell>
                    <TableCell>{o.region || "—"}</TableCell>
                    <TableCell>{o.salesperson || "—"}</TableCell>
                    <TableCell className="text-right">{fmt(o.total_amount)}</TableCell>
                    <TableCell><Badge variant={payBadge(o.payment_status) as "default" | "secondary" | "destructive"}>{o.payment_status}</Badge></TableCell>
                    <TableCell><Badge variant={shipBadge(o.shipment_status) as "default" | "secondary" | "outline"}>{o.shipment_status}</Badge></TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={async () => { const r = await ordersApi.get(o.id); setViewOrder(r.data); }}><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(o.id)}><Pencil className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => setDeleteId(o.id)}><Trash2 className="h-4 w-4" /></Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{total} total orders</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="flex items-center text-sm">Page {page + 1} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      </div>

      {/* View Dialog */}
      <Dialog open={!!viewOrder} onOpenChange={() => setViewOrder(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <DialogTitle>Order #{viewOrder?.id}</DialogTitle>
              <Button variant="outline" size="sm" onClick={() => viewOrder && handleDownloadPDF(viewOrder.id)}>
                <Download className="mr-1 h-4 w-4" /> PDF
              </Button>
            </div>
          </DialogHeader>
          {viewOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div><span className="text-muted-foreground">Customer:</span> {viewOrder.customer_name}</div>
                <div><span className="text-muted-foreground">Date:</span> {new Date(viewOrder.order_date).toLocaleDateString()}</div>
                <div><span className="text-muted-foreground">Region:</span> {viewOrder.region || "—"}</div>
                <div><span className="text-muted-foreground">Salesperson:</span> {viewOrder.salesperson || "—"}</div>
                <div><span className="text-muted-foreground">Payment:</span> <Badge variant={payBadge(viewOrder.payment_status) as "default" | "secondary" | "destructive"}>{viewOrder.payment_status}</Badge></div>
                <div><span className="text-muted-foreground">Shipment:</span> <Badge variant={shipBadge(viewOrder.shipment_status) as "default" | "secondary" | "outline"}>{viewOrder.shipment_status}</Badge></div>
              </div>
              <Table>
                <TableHeader><TableRow><TableHead>Product</TableHead><TableHead className="text-right">Qty</TableHead><TableHead className="text-right">Price</TableHead><TableHead className="text-right">Total</TableHead></TableRow></TableHeader>
                <TableBody>
                  {viewOrder.items.map((it) => (
                    <TableRow key={it.id}>
                      <TableCell>{it.product_name || `#${it.product_id}`}</TableCell>
                      <TableCell className="text-right">{it.quantity}</TableCell>
                      <TableCell className="text-right">{fmt(it.unit_price)}</TableCell>
                      <TableCell className="text-right">{fmt(it.total)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow>
                    <TableCell colSpan={3} className="text-right font-medium">Total</TableCell>
                    <TableCell className="text-right font-bold">{fmt(viewOrder.total_amount)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Create/Edit Dialog */}
      <Dialog open={editDialog} onOpenChange={setEditDialog}>
        <DialogContent className="max-w-xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingOrder ? `Edit Order #${editingOrder.id}` : "New Order"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><Label>Customer ID</Label><Input value={formCustomerId} onChange={(e) => setFormCustomerId(e.target.value)} /></div>
              <div><Label>Region</Label><Input value={formRegion} onChange={(e) => setFormRegion(e.target.value)} /></div>
              <div><Label>Salesperson</Label><Input value={formSalesperson} onChange={(e) => setFormSalesperson(e.target.value)} /></div>
              <div>
                <Label>Payment Status</Label>
                <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={formPayStatus} onChange={(e) => setFormPayStatus(e.target.value)}>
                  <option value="pending">Pending</option><option value="paid">Paid</option><option value="overdue">Overdue</option><option value="cancelled">Cancelled</option>
                </select>
              </div>
              <div>
                <Label>Shipment Status</Label>
                <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={formShipStatus} onChange={(e) => setFormShipStatus(e.target.value)}>
                  <option value="pending">Pending</option><option value="processing">Processing</option><option value="shipped">Shipped</option><option value="delivered">Delivered</option>
                </select>
              </div>
            </div>

            {!editingOrder && (
              <>
                <div className="flex items-center justify-between">
                  <Label>Line Items</Label>
                  <Button variant="outline" size="sm" onClick={addItem}><Plus className="mr-1 h-3 w-3" />Add Item</Button>
                </div>
                {formItems.map((item, i) => (
                  <div key={i} className="flex items-end gap-2">
                    <div className="flex-1"><Label className="text-xs">Product ID</Label><Input value={item.product_id} onChange={(e) => updateItem(i, "product_id", e.target.value)} /></div>
                    <div className="w-20"><Label className="text-xs">Qty</Label><Input type="number" value={item.quantity} onChange={(e) => updateItem(i, "quantity", e.target.value)} /></div>
                    <div className="w-28"><Label className="text-xs">Unit Price</Label><Input type="number" step="0.01" value={item.unit_price} onChange={(e) => updateItem(i, "unit_price", e.target.value)} /></div>
                    {formItems.length > 1 && (
                      <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0" onClick={() => removeItem(i)}><X className="h-4 w-4" /></Button>
                    )}
                  </div>
                ))}
              </>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialog(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Order</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete order #{deleteId}? This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
