import { useEffect, useState, useCallback, useMemo } from "react";
import {
  Search,
  Loader2,
  Filter,
  Calendar,
  Clock,
  User,
  Shield,
  Activity,
  ChevronDown,
  ChevronUp,
  Download,
  RefreshCw,
} from "lucide-react";
import { auditLogsApi } from "@/api/endpoints";
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { AuditLog } from "@/types";

const ACTION_OPTIONS = [
  { value: "", label: "All Actions" },
  { value: "login", label: "Login" },
  { value: "create", label: "Create" },
  { value: "update", label: "Update" },
  { value: "delete", label: "Delete" },
  { value: "upload", label: "Upload" },
  { value: "export", label: "Export" },
];

const ENTITY_OPTIONS = [
  { value: "", label: "All Entities" },
  { value: "auth", label: "Auth" },
  { value: "user", label: "User" },
  { value: "order", label: "Order" },
  { value: "customer", label: "Customer" },
  { value: "product", label: "Product" },
  { value: "inventory", label: "Inventory" },
];

function actionBadgeVariant(
  action: string,
): "default" | "secondary" | "destructive" | "outline" {
  switch (action) {
    case "login":
      return "default";
    case "create":
      return "default";
    case "update":
      return "secondary";
    case "delete":
      return "destructive";
    case "upload":
      return "secondary";
    case "export":
      return "outline";
    default:
      return "outline";
  }
}

function actionBadgeClass(action: string): string {
  switch (action) {
    case "login":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "create":
      return "bg-green-100 text-green-800 border-green-200";
    case "update":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "delete":
      return "bg-red-100 text-red-800 border-red-200";
    case "upload":
      return "bg-purple-100 text-purple-800 border-purple-200";
    case "export":
      return "";
    default:
      return "";
  }
}

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + "...";
}

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");
  const [entityFilter, setEntityFilter] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // Sort
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");

  // Pagination
  const [page, setPage] = useState(0);
  const limit = 20;

  // Detail dialog
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  // Auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { limit: 1000 };
      if (actionFilter) params.action = actionFilter;
      if (entityFilter) params.entity_type = entityFilter;
      if (dateFrom) params.date_from = new Date(dateFrom).toISOString();
      if (dateTo) params.date_to = new Date(dateTo + "T23:59:59").toISOString();

      const res = await auditLogsApi.list(
        params as Parameters<typeof auditLogsApi.list>[0],
      );

      // Handle both plain array and paginated response
      const data = res.data;
      let items: AuditLog[];
      if (Array.isArray(data)) {
        items = data as unknown as AuditLog[];
      } else if (
        data &&
        typeof data === "object" &&
        "items" in data &&
        Array.isArray((data as { items: unknown }).items)
      ) {
        items = (data as { items: AuditLog[] }).items;
      } else {
        items = [];
      }

      setLogs(items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [actionFilter, entityFilter, dateFrom, dateTo]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Auto-refresh interval
  useEffect(() => {
    if (!autoRefresh) return;
    const id = setInterval(fetchLogs, 30000);
    return () => clearInterval(id);
  }, [autoRefresh, fetchLogs]);

  // Client-side filtering (search on details text) + sorting
  const filteredLogs = useMemo(() => {
    let result = logs;

    // Frontend text search on details
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (l) =>
          (l.details && l.details.toLowerCase().includes(q)) ||
          l.ip_address?.toLowerCase().includes(q) ||
          String(l.user_id).includes(q) ||
          String(l.entity_id ?? "").includes(q),
      );
    }

    // Sort by timestamp
    result = [...result].sort((a, b) => {
      const ta = new Date(a.timestamp).getTime();
      const tb = new Date(b.timestamp).getTime();
      return sortOrder === "desc" ? tb - ta : ta - tb;
    });

    return result;
  }, [logs, search, sortOrder]);

  // Client-side pagination
  const totalFiltered = filteredLogs.length;
  const totalPages = Math.max(1, Math.ceil(totalFiltered / limit));
  const paginatedLogs = filteredLogs.slice(page * limit, (page + 1) * limit);

  const clearFilters = () => {
    setSearch("");
    setActionFilter("");
    setEntityFilter("");
    setDateFrom("");
    setDateTo("");
    setSortOrder("desc");
    setPage(0);
  };

  const hasActiveFilters =
    search || actionFilter || entityFilter || dateFrom || dateTo;

  // CSV export (frontend-only, from currently visible/filtered data)
  const exportCSV = () => {
    const headers = [
      "ID",
      "Timestamp",
      "User ID",
      "Action",
      "Entity Type",
      "Entity ID",
      "Details",
      "IP Address",
    ];
    const rows = filteredLogs.map((l) => [
      String(l.id),
      formatTimestamp(l.timestamp),
      String(l.user_id),
      l.action,
      l.entity_type,
      l.entity_id != null ? String(l.entity_id) : "",
      `"${(l.details ?? "").replace(/"/g, '""')}"`,
      l.ip_address ?? "",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-2xl font-bold tracking-tight">Audit Logs</h2>
          <Badge variant="secondary" className="text-sm font-medium px-2.5 py-0.5">
            {filteredLogs.length} {filteredLogs.length === 1 ? "entry" : "entries"}
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {autoRefresh ? "Auto-refresh On" : "Auto-refresh"}
          </Button>
          <Button variant="outline" size="sm" onClick={exportCSV}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[180px] flex-1">
            <Label className="text-xs">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-8"
                placeholder="Search details, IP, user..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(0);
                }}
              />
            </div>
          </div>
          <div>
            <Label className="text-xs">Action</Label>
            <select
              className="h-9 rounded-md border bg-background px-3 text-sm"
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value);
                setPage(0);
              }}
            >
              {ACTION_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label className="text-xs">Entity Type</Label>
            <select
              className="h-9 rounded-md border bg-background px-3 text-sm"
              value={entityFilter}
              onChange={(e) => {
                setEntityFilter(e.target.value);
                setPage(0);
              }}
            >
              {ENTITY_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label className="text-xs">
              <Calendar className="mr-1 inline h-3 w-3" />
              From
            </Label>
            <Input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(0);
              }}
            />
          </div>
          <div>
            <Label className="text-xs">
              <Calendar className="mr-1 inline h-3 w-3" />
              To
            </Label>
            <Input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(0);
              }}
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setSortOrder(sortOrder === "asc" ? "desc" : "asc")
            }
            title={`Sort ${sortOrder === "desc" ? "oldest first" : "newest first"}`}
          >
            {sortOrder === "desc" ? (
              <ChevronDown className="mr-1 h-4 w-4" />
            ) : (
              <ChevronUp className="mr-1 h-4 w-4" />
            )}
            Timestamp
          </Button>
          {hasActiveFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear
            </Button>
          )}
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
                  <TableHead>Timestamp</TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Entity Type</TableHead>
                  <TableHead>Entity ID</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>IP Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedLogs.length === 0 ? (
                  <TableRow>
                    <TableCell
                      colSpan={7}
                      className="py-8 text-center text-muted-foreground"
                    >
                      <Activity className="mx-auto mb-2 h-8 w-8 text-muted-foreground/50" />
                      No audit logs found
                    </TableCell>
                  </TableRow>
                ) : (
                  paginatedLogs.map((log) => (
                    <TableRow
                      key={log.id}
                      className="cursor-pointer hover:bg-muted/50"
                      onClick={() => setSelectedLog(log)}
                    >
                      <TableCell className="whitespace-nowrap font-mono text-xs">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3 w-3 text-muted-foreground" />
                          {formatTimestamp(log.timestamp)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5">
                          <User className="h-3 w-3 text-muted-foreground" />
                          <span className="text-sm">
                            {(log as AuditLog & { user_email?: string })
                              .user_email || `User #${log.user_id}`}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={actionBadgeVariant(log.action)}
                          className={actionBadgeClass(log.action)}
                        >
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{log.entity_type}</Badge>
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.entity_id != null ? `#${log.entity_id}` : "\u2014"}
                      </TableCell>
                      <TableCell
                        className="max-w-[250px] truncate text-sm text-muted-foreground"
                        title={log.details ?? undefined}
                      >
                        {log.details ? truncate(log.details, 60) : "\u2014"}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.ip_address || "\u2014"}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {paginatedLogs.length > 0 ? page * limit + 1 : 0}&ndash;
          {Math.min((page + 1) * limit, totalFiltered)} of {totalFiltered} logs
        </p>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
          >
            Previous
          </Button>
          <span className="flex items-center text-sm">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page >= totalPages - 1}
            onClick={() => setPage(page + 1)}
          >
            Next
          </Button>
        </div>
      </div>

      {/* Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Audit Log #{selectedLog?.id}
            </DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Timestamp
                  </span>
                  <p className="font-mono">
                    {formatTimestamp(selectedLog.timestamp)}
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    User
                  </span>
                  <p className="flex items-center gap-1.5">
                    <User className="h-3.5 w-3.5 text-muted-foreground" />
                    {(selectedLog as AuditLog & { user_email?: string })
                      .user_email || `User #${selectedLog.user_id}`}
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Action
                  </span>
                  <div>
                    <Badge
                      variant={actionBadgeVariant(selectedLog.action)}
                      className={actionBadgeClass(selectedLog.action)}
                    >
                      {selectedLog.action}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Entity Type
                  </span>
                  <div>
                    <Badge variant="secondary">
                      {selectedLog.entity_type}
                    </Badge>
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    Entity ID
                  </span>
                  <p className="font-mono">
                    {selectedLog.entity_id != null
                      ? `#${selectedLog.entity_id}`
                      : "\u2014"}
                  </p>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-medium text-muted-foreground">
                    IP Address
                  </span>
                  <p className="font-mono">
                    {selectedLog.ip_address || "\u2014"}
                  </p>
                </div>
              </div>
              <div className="space-y-1">
                <span className="text-xs font-medium text-muted-foreground">
                  Details
                </span>
                <div className="rounded-md border bg-muted/30 p-3 text-sm whitespace-pre-wrap">
                  {selectedLog.details || "No details available."}
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
