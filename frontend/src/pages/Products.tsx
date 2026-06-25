import { useEffect, useState, useCallback } from "react";
import { Plus, Search, Loader2, Pencil, Trash2, CheckSquare, Square } from "lucide-react";
import { productsApi, batchApi } from "@/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import type { Product } from "@/types";

const fmt = (v: number) => new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(v);

interface FormData { name: string; category: string; supplier_id: string; unit_price: string; cost_price: string; current_stock: string; reorder_level: string; }
const emptyForm: FormData = { name: "", category: "", supplier_id: "", unit_price: "", cost_price: "", current_stock: "0", reorder_level: "10" };

export default function Products() {
  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [catFilter, setCatFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const [dialog, setDialog] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [batchDeleting, setBatchDeleting] = useState(false);

  const handleBatchDelete = async () => {
    if (!confirm(`Delete ${selected.size} selected products?`)) return;
    setBatchDeleting(true);
    try {
      await batchApi.deleteProducts(Array.from(selected));
      setSelected(new Set());
      fetch();
    } catch (e) { console.error(e); }
    setBatchDeleting(false);
  };

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { skip: page * limit, limit };
      if (search) params.search = search;
      if (catFilter) params.category = catFilter;
      if (statusFilter) params.product_status = statusFilter;
      const res = await productsApi.list(params as Parameters<typeof productsApi.list>[0]);
      setItems(res.data.items);
      setTotal(res.data.total);
    } catch (e) { console.error(e); }
    finally { setLoading(false); }
  }, [search, catFilter, statusFilter, page]);

  useEffect(() => { fetch(); }, [fetch]);
  const totalPages = Math.max(1, Math.ceil(total / limit));

  const openCreate = () => { setEditing(null); setForm(emptyForm); setDialog(true); };
  const openEdit = (p: Product) => {
    setEditing(p);
    setForm({
      name: p.name, category: p.category || "", supplier_id: p.supplier_id ? String(p.supplier_id) : "",
      unit_price: String(p.unit_price), cost_price: p.cost_price ? String(p.cost_price) : "",
      current_stock: String(p.current_stock), reorder_level: String(p.reorder_level),
    });
    setDialog(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const data = {
        name: form.name,
        category: form.category || undefined,
        supplier_id: form.supplier_id ? Number(form.supplier_id) : undefined,
        unit_price: Number(form.unit_price),
        cost_price: form.cost_price ? Number(form.cost_price) : undefined,
        current_stock: Number(form.current_stock),
        reorder_level: Number(form.reorder_level),
      };
      if (editing) await productsApi.update(editing.id, data);
      else await productsApi.create(data);
      setDialog(false);
      fetch();
    } catch (e) { console.error(e); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try { await productsApi.delete(deleteId); setDeleteId(null); fetch(); } catch (e) { console.error(e); }
  };

  const upd = (field: keyof FormData, value: string) => setForm({ ...form, [field]: value });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">Products</h2>
        <Button onClick={openCreate}><Plus className="mr-2 h-4 w-4" />Add Product</Button>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[200px] flex-1">
            <Label className="text-xs">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-8" placeholder="Product name..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} />
            </div>
          </div>
          <div>
            <Label className="text-xs">Category</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={catFilter} onChange={(e) => { setCatFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              {["Electronics", "Office Supplies", "Furniture", "Food & Beverage", "Clothing"].map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <Label className="text-xs">Status</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(0); }}>
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="discontinued">Discontinued</option>
            </select>
          </div>
          <Button variant="ghost" size="sm" onClick={() => { setSearch(""); setCatFilter(""); setStatusFilter(""); setPage(0); }}>Clear</Button>
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

      <Card>
        <CardContent className="p-0">
          {loading ? <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div> : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[40px]">
                    <button onClick={() => {
                      if (selected.size === items.length) setSelected(new Set());
                      else setSelected(new Set(items.map(p => p.id)));
                    }}>
                      {selected.size === items.length && items.length > 0 ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                    </button>
                  </TableHead>
                  <TableHead>Name</TableHead><TableHead>Category</TableHead><TableHead>Supplier</TableHead>
                  <TableHead className="text-right">Unit Price</TableHead><TableHead className="text-right">Cost</TableHead>
                  <TableHead className="text-right">Stock</TableHead><TableHead className="text-right">Reorder</TableHead>
                  <TableHead>Status</TableHead><TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.length === 0 ? (
                  <TableRow><TableCell colSpan={10} className="text-center text-muted-foreground py-8">No products found</TableCell></TableRow>
                ) : items.map((p) => {
                  const lowStock = p.current_stock <= p.reorder_level;
                  return (
                    <TableRow key={p.id}>
                      <TableCell>
                        <button onClick={() => {
                          const next = new Set(selected);
                          next.has(p.id) ? next.delete(p.id) : next.add(p.id);
                          setSelected(next);
                        }}>
                          {selected.has(p.id) ? <CheckSquare className="h-4 w-4 text-blue-600" /> : <Square className="h-4 w-4 text-muted-foreground" />}
                        </button>
                      </TableCell>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell>{p.category || "—"}</TableCell>
                      <TableCell>{p.supplier?.name || "—"}</TableCell>
                      <TableCell className="text-right">{fmt(p.unit_price)}</TableCell>
                      <TableCell className="text-right">{p.cost_price ? fmt(p.cost_price) : "—"}</TableCell>
                      <TableCell className="text-right">
                        <span className={lowStock ? "font-medium text-red-600" : ""}>{p.current_stock}</span>
                      </TableCell>
                      <TableCell className="text-right">{p.reorder_level}</TableCell>
                      <TableCell>
                        {lowStock && <Badge variant="destructive" className="mr-1">Low</Badge>}
                        <Badge variant={p.status === "active" ? "default" : "secondary"}>{p.status}</Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(p)}><Pencil className="h-4 w-4" /></Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => setDeleteId(p.id)}><Trash2 className="h-4 w-4" /></Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{total} total products</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>Previous</Button>
          <span className="flex items-center text-sm">Page {page + 1} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>Next</Button>
        </div>
      </div>

      {/* Create/Edit Dialog */}
      <Dialog open={dialog} onOpenChange={setDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editing ? "Edit Product" : "Add Product"}</DialogTitle></DialogHeader>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2"><Label>Name *</Label><Input value={form.name} onChange={(e) => upd("name", e.target.value)} /></div>
            <div><Label>Category</Label><Input value={form.category} onChange={(e) => upd("category", e.target.value)} /></div>
            <div><Label>Supplier ID</Label><Input type="number" value={form.supplier_id} onChange={(e) => upd("supplier_id", e.target.value)} /></div>
            <div><Label>Unit Price *</Label><Input type="number" step="0.01" value={form.unit_price} onChange={(e) => upd("unit_price", e.target.value)} /></div>
            <div><Label>Cost Price</Label><Input type="number" step="0.01" value={form.cost_price} onChange={(e) => upd("cost_price", e.target.value)} /></div>
            <div><Label>Current Stock</Label><Input type="number" value={form.current_stock} onChange={(e) => upd("current_stock", e.target.value)} /></div>
            <div><Label>Reorder Level</Label><Input type="number" value={form.reorder_level} onChange={(e) => upd("reorder_level", e.target.value)} /></div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialog(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving || !form.name || !form.unit_price}>
              {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete */}
      <Dialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete Product</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">Are you sure you want to delete this product?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
