import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Search,
  Loader2,
  Package,
  AlertTriangle,
  Warehouse,
  ArrowUpDown,
  Download,
} from "lucide-react";
import { inventoryApi } from "@/api/endpoints";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Inventory as InventoryType } from "@/types";

interface LowStockItem {
  product_id: number;
  product_name: string;
  category: string;
  current_stock: number;
  reorder_level: number;
  supplier_name: string;
}

export default function Inventory() {
  const [tab, setTab] = useState<"all" | "low">("all");

  // ── All Inventory ──
  const [items, setItems] = useState<InventoryType[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [warehouseFilter, setWarehouseFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [sortField, setSortField] = useState<"product_name" | "quantity" | "last_updated">("product_name");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(0);
  const limit = 20;

  // ── Low Stock ──
  const [lowStock, setLowStock] = useState<LowStockItem[]>([]);
  const [lowLoading, setLowLoading] = useState(false);
  const [lowSearch, setLowSearch] = useState("");

  const fetchInventory = useCallback(async () => {
    setLoading(true);
    try {
      const res = await inventoryApi.list({ skip: 0, limit: 500 });
      const data = res.data;
      let arr: InventoryType[];
      if (Array.isArray(data)) {
        arr = data as unknown as InventoryType[];
      } else if (data && typeof data === "object" && "items" in data) {
        arr = (data as { items: InventoryType[] }).items;
      } else {
        arr = [];
      }
      setItems(arr);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchLowStock = useCallback(async () => {
    setLowLoading(true);
    try {
      const res = await inventoryApi.getLowStock();
      const data = res.data;
      setLowStock(Array.isArray(data) ? (data as unknown as LowStockItem[]) : []);
    } catch (e) {
      console.error(e);
    } finally {
      setLowLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInventory();
    fetchLowStock();
  }, [fetchInventory, fetchLowStock]);

  // Derive unique warehouses and categories from data
  const warehouses = useMemo(
    () => [...new Set(items.map((i) => i.warehouse).filter(Boolean))].sort(),
    [items],
  );
  const categories = useMemo(
    () => [...new Set(items.map((i) => (i as InventoryType & { product_category?: string }).product_category).filter(Boolean))].sort() as string[],
    [items],
  );

  // Client-side filter + sort + paginate
  const filtered = useMemo(() => {
    let result = items;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (i) =>
          (i.product_name || "").toLowerCase().includes(q) ||
          String(i.product_id).includes(q) ||
          i.warehouse.toLowerCase().includes(q),
      );
    }
    if (warehouseFilter) {
      result = result.filter((i) => i.warehouse === warehouseFilter);
    }
    const catField = "product_category" as keyof InventoryType;
    if (categoryFilter) {
      result = result.filter((i) => (i[catField] as unknown as string) === categoryFilter);
    }
    // Sort
    result = [...result].sort((a, b) => {
      let cmp = 0;
      if (sortField === "product_name") {
        cmp = (a.product_name || "").localeCompare(b.product_name || "");
      } else if (sortField === "quantity") {
        cmp = a.quantity - b.quantity;
      } else if (sortField === "last_updated") {
        cmp = new Date(a.last_updated).getTime() - new Date(b.last_updated).getTime();
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return result;
  }, [items, search, warehouseFilter, categoryFilter, sortField, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / limit));
  const paginated = filtered.slice(page * limit, (page + 1) * limit);

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("asc");
    }
  };

  const clearFilters = () => {
    setSearch("");
    setWarehouseFilter("");
    setCategoryFilter("");
    setPage(0);
  };

  // Low stock client-side filter
  const filteredLow = useMemo(() => {
    if (!lowSearch) return lowStock;
    const q = lowSearch.toLowerCase();
    return lowStock.filter(
      (i) =>
        i.product_name.toLowerCase().includes(q) ||
        i.category.toLowerCase().includes(q) ||
        i.supplier_name.toLowerCase().includes(q),
    );
  }, [lowStock, lowSearch]);

  // CSV export
  const exportCSV = () => {
    const headers = ["Product", "Category", "Warehouse", "Quantity", "Reorder Level", "Status", "Last Updated"];
    const rows = filtered.map((i) => {
      const cat = (i as InventoryType & { product_category?: string }).product_category || "";
      const isLow = i.quantity <= i.reorder_level;
      return [
        `"${(i.product_name || "").replace(/"/g, '""')}"`,
        `"${cat.replace(/"/g, '""')}"`,
        i.warehouse,
        String(i.quantity),
        String(i.reorder_level),
        isLow ? "Low Stock" : "In Stock",
        new Date(i.last_updated).toLocaleDateString(),
      ].join(",");
    });
    const csv = [headers.join(","), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inventory-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const SortIcon = ({ field }: { field: typeof sortField }) => (
    <ArrowUpDown className={`ml-1 inline h-3 w-3 ${sortField === field ? "text-primary" : "text-muted-foreground"}`} />
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight">Inventory</h2>
          {lowStock.length > 0 && (
            <Badge variant="destructive" className="flex items-center gap-1">
              <AlertTriangle className="h-3 w-3" />
              {lowStock.length} Low Stock
            </Badge>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={exportCSV}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg bg-muted p-1 w-fit">
        <button
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            tab === "all" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setTab("all")}
        >
          All Inventory
        </button>
        <button
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            tab === "low" ? "bg-background shadow-sm" : "text-muted-foreground hover:text-foreground"
          }`}
          onClick={() => setTab("low")}
        >
          Low Stock Alerts
          {lowStock.length > 0 && (
            <span className="ml-2 inline-flex h-5 min-w-[20px] items-center justify-center rounded-full bg-red-100 px-1.5 text-xs font-bold text-red-700">
              {lowStock.length}
            </span>
          )}
        </button>
      </div>

      {tab === "all" ? (
        <>
          {/* Filters */}
          <Card>
            <CardContent className="flex flex-wrap items-end gap-3 p-4">
              <div className="min-w-[200px] flex-1">
                <Label className="text-xs">Search</Label>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-8"
                    placeholder="Product name or ID..."
                    value={search}
                    onChange={(e) => { setSearch(e.target.value); setPage(0); }}
                  />
                </div>
              </div>
              <div>
                <Label className="text-xs">
                  <Warehouse className="mr-1 inline h-3 w-3" />Warehouse
                </Label>
                <select
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  value={warehouseFilter}
                  onChange={(e) => { setWarehouseFilter(e.target.value); setPage(0); }}
                >
                  <option value="">All Warehouses</option>
                  {warehouses.map((w) => (
                    <option key={w} value={w}>{w}</option>
                  ))}
                </select>
              </div>
              {categories.length > 0 && (
                <div>
                  <Label className="text-xs">Category</Label>
                  <select
                    className="h-9 rounded-md border bg-background px-3 text-sm"
                    value={categoryFilter}
                    onChange={(e) => { setCategoryFilter(e.target.value); setPage(0); }}
                  >
                    <option value="">All Categories</option>
                    {categories.map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
              )}
              <Button variant="ghost" size="sm" onClick={clearFilters}>Clear</Button>
            </CardContent>
          </Card>

          {/* Table */}
          <Card>
            <CardContent className="p-0">
              {loading ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product ID</TableHead>
                      <TableHead
                        className="cursor-pointer select-none"
                        onClick={() => toggleSort("product_name")}
                      >
                        Product Name <SortIcon field="product_name" />
                      </TableHead>
                      <TableHead>Warehouse</TableHead>
                      <TableHead
                        className="cursor-pointer select-none text-right"
                        onClick={() => toggleSort("quantity")}
                      >
                        Quantity <SortIcon field="quantity" />
                      </TableHead>
                      <TableHead className="text-right">Reorder Level</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead
                        className="cursor-pointer select-none"
                        onClick={() => toggleSort("last_updated")}
                      >
                        Last Updated <SortIcon field="last_updated" />
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {paginated.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                          <Package className="mx-auto mb-2 h-8 w-8 text-muted-foreground/50" />
                          No inventory records found
                        </TableCell>
                      </TableRow>
                    ) : (
                      paginated.map((item) => {
                        const isLow = item.quantity <= item.reorder_level;
                        return (
                          <TableRow key={item.id}>
                            <TableCell className="font-mono text-xs">#{item.product_id}</TableCell>
                            <TableCell className="font-medium">{item.product_name || "—"}</TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1.5">
                                <Warehouse className="h-3 w-3 text-muted-foreground" />
                                {item.warehouse}
                              </div>
                            </TableCell>
                            <TableCell className={`text-right font-semibold ${isLow ? "text-red-600" : ""}`}>
                              {item.quantity.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">{item.reorder_level}</TableCell>
                            <TableCell>
                              {isLow ? (
                                <Badge variant="destructive" className="flex w-fit items-center gap-1">
                                  <AlertTriangle className="h-3 w-3" />
                                  Low Stock
                                </Badge>
                              ) : (
                                <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                                  In Stock
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {new Date(item.last_updated).toLocaleDateString()}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          {/* Pagination */}
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {paginated.length > 0 ? page * limit + 1 : 0}–
              {Math.min((page + 1) * limit, filtered.length)} of {filtered.length} records
            </p>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" disabled={page === 0} onClick={() => setPage(page - 1)}>
                Previous
              </Button>
              <span className="flex items-center text-sm">
                Page {page + 1} of {totalPages}
              </span>
              <Button variant="outline" size="sm" disabled={page >= totalPages - 1} onClick={() => setPage(page + 1)}>
                Next
              </Button>
            </div>
          </div>
        </>
      ) : (
        /* Low Stock Tab */
        <>
          <Card>
            <CardContent className="flex flex-wrap items-end gap-3 p-4">
              <div className="min-w-[250px] flex-1">
                <Label className="text-xs">Search</Label>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    className="pl-8"
                    placeholder="Product, category, or supplier..."
                    value={lowSearch}
                    onChange={(e) => setLowSearch(e.target.value)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-0">
              {lowLoading ? (
                <div className="flex h-32 items-center justify-center">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product ID</TableHead>
                      <TableHead>Product Name</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead className="text-right">Current Stock</TableHead>
                      <TableHead className="text-right">Reorder Level</TableHead>
                      <TableHead className="text-right">Deficit</TableHead>
                      <TableHead>Supplier</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredLow.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={7} className="py-8 text-center text-muted-foreground">
                          <div className="flex flex-col items-center gap-2">
                            <Package className="h-8 w-8 text-green-400" />
                            <span className="text-green-600 font-medium">All products are well-stocked!</span>
                          </div>
                        </TableCell>
                      </TableRow>
                    ) : (
                      filteredLow.map((item) => {
                        const deficit = item.reorder_level - item.current_stock;
                        return (
                          <TableRow key={item.product_id}>
                            <TableCell className="font-mono text-xs">#{item.product_id}</TableCell>
                            <TableCell className="font-medium">
                              <div className="flex items-center gap-2">
                                <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0" />
                                {item.product_name}
                              </div>
                            </TableCell>
                            <TableCell>{item.category}</TableCell>
                            <TableCell className="text-right font-semibold text-red-600">
                              {item.current_stock.toLocaleString()}
                            </TableCell>
                            <TableCell className="text-right">{item.reorder_level}</TableCell>
                            <TableCell className="text-right">
                              <Badge variant="destructive">-{deficit}</Badge>
                            </TableCell>
                            <TableCell className="text-sm text-muted-foreground">
                              {item.supplier_name || "—"}
                            </TableCell>
                          </TableRow>
                        );
                      })
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            {filteredLow.length} {filteredLow.length === 1 ? "product" : "products"} below reorder level
          </p>
        </>
      )}
    </div>
  );
}
