import { useEffect, useState, useCallback } from "react";
import { Plus, Search, Loader2, Pencil, Trash2, UserCheck, UserX } from "lucide-react";
import axios from "axios";
import { usersApi } from "@/api/endpoints";
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
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import type { User } from "@/types";

const ROLE_OPTIONS = [
  { id: 1, name: "admin" },
  { id: 2, name: "manager" },
  { id: 3, name: "staff" },
] as const;

const roleBadge = (name: string): "default" | "secondary" | "outline" =>
  name === "admin" ? "default" : name === "manager" ? "secondary" : "outline";

const avatarBg = (name: string) =>
  name === "admin"
    ? "bg-blue-600 text-white"
    : name === "manager"
      ? "bg-purple-600 text-white"
      : "bg-gray-500 text-white";

function getInitials(user: User): string {
  if (user.full_name) {
    const parts = user.full_name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].slice(0, 2).toUpperCase();
  }
  return user.email.slice(0, 2).toUpperCase();
}

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  // Dialogs
  const [createDialog, setCreateDialog] = useState(false);
  const [editUser, setEditUser] = useState<User | null>(null);
  const [deleteUser, setDeleteUser] = useState<User | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);

  // Create form state
  const [formFullName, setFormFullName] = useState("");
  const [formEmail, setFormEmail] = useState("");
  const [formPassword, setFormPassword] = useState("");
  const [formRole, setFormRole] = useState("staff");
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");

  // Edit form state
  const [editFullName, setEditFullName] = useState("");
  const [editEmail, setEditEmail] = useState("");
  const [editRoleId, setEditRoleId] = useState(3);
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  const fetchUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await usersApi.list({ skip: 0, limit: 50 });
      setUsers(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchUsers(); }, [fetchUsers]);

  // Client-side filtering
  const filtered = users.filter((u) => {
    if (search) {
      const q = search.toLowerCase();
      const name = (u.full_name || "").toLowerCase();
      const email = u.email.toLowerCase();
      if (!name.includes(q) && !email.includes(q)) return false;
    }
    if (roleFilter && u.role.name !== roleFilter) return false;
    if (statusFilter === "active" && !u.is_active) return false;
    if (statusFilter === "inactive" && u.is_active) return false;
    return true;
  });

  const clearFilters = () => {
    setSearch("");
    setRoleFilter("");
    setStatusFilter("");
  };

  // ── Create ──
  const openCreate = () => {
    setFormFullName("");
    setFormEmail("");
    setFormPassword("");
    setFormRole("staff");
    setFormError("");
    setCreateDialog(true);
  };

  const handleCreate = async () => {
    if (!formEmail || !formPassword) return;
    setSaving(true);
    setFormError("");
    try {
      await usersApi.create({
        email: formEmail,
        password: formPassword,
        full_name: formFullName || undefined,
        role: formRole,
      });
      setCreateDialog(false);
      fetchUsers();
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 409) {
        setFormError("A user with this email already exists.");
      } else {
        setFormError("Failed to create user. Please try again.");
      }
    } finally {
      setSaving(false);
    }
  };

  // ── Edit ──
  const openEdit = (user: User) => {
    setEditUser(user);
    setEditFullName(user.full_name || "");
    setEditEmail(user.email);
    setEditRoleId(user.role.id);
    setEditError("");
  };

  const handleEdit = async () => {
    if (!editUser) return;
    setEditSaving(true);
    setEditError("");
    try {
      await usersApi.update(editUser.id, {
        email: editEmail || undefined,
        full_name: editFullName || undefined,
        role_id: editRoleId,
      });
      setEditUser(null);
      fetchUsers();
    } catch (e) {
      if (axios.isAxiosError(e) && e.response?.status === 409) {
        setEditError("A user with this email already exists.");
      } else if (axios.isAxiosError(e) && e.response?.status === 404) {
        setEditError("User not found.");
      } else {
        setEditError("Failed to update user. Please try again.");
      }
    } finally {
      setEditSaving(false);
    }
  };

  // ── Toggle Active ──
  const handleToggleActive = async (user: User) => {
    setTogglingId(user.id);
    try {
      await usersApi.update(user.id, { is_active: !user.is_active });
      fetchUsers();
    } catch (e) {
      console.error(e);
    } finally {
      setTogglingId(null);
    }
  };

  // ── Delete ──
  const handleDelete = async () => {
    if (!deleteUser) return;
    try {
      await usersApi.delete(deleteUser.id);
      setDeleteUser(null);
      fetchUsers();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold tracking-tight">User Management</h2>
        <Button onClick={openCreate}><Plus className="mr-2 h-4 w-4" />Add User</Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="flex flex-wrap items-end gap-3 p-4">
          <div className="min-w-[220px] flex-1">
            <Label className="text-xs">Search</Label>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-8" placeholder="Search by name or email..." value={search} onChange={(e) => setSearch(e.target.value)} />
            </div>
          </div>
          <div>
            <Label className="text-xs">Role</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="manager">Manager</option>
              <option value="staff">Staff</option>
            </select>
          </div>
          <div>
            <Label className="text-xs">Status</Label>
            <select className="h-9 rounded-md border bg-background px-3 text-sm" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <Button variant="ghost" size="sm" onClick={clearFilters}>Clear</Button>
        </CardContent>
      </Card>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[60px]"></TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.length === 0 ? (
                  <TableRow><TableCell colSpan={7} className="text-center text-muted-foreground py-8">No users found</TableCell></TableRow>
                ) : filtered.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell>
                      <Avatar className={`h-8 w-8 ${avatarBg(u.role.name)}`}>
                        <AvatarFallback className={avatarBg(u.role.name)}>{getInitials(u)}</AvatarFallback>
                      </Avatar>
                    </TableCell>
                    <TableCell className="font-medium">{u.full_name || "\u2014"}</TableCell>
                    <TableCell>{u.email}</TableCell>
                    <TableCell><Badge variant={roleBadge(u.role.name)}>{u.role.name}</Badge></TableCell>
                    <TableCell>
                      <Badge variant={u.is_active ? "default" : "destructive"}>
                        {u.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell>{new Date(u.created_at).toLocaleDateString()}</TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(u)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => handleToggleActive(u)}
                          disabled={togglingId === u.id}
                          title={u.is_active ? "Deactivate user" : "Activate user"}
                        >
                          {togglingId === u.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : u.is_active ? (
                            <UserX className="h-4 w-4 text-amber-500" />
                          ) : (
                            <UserCheck className="h-4 w-4 text-green-500" />
                          )}
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500" onClick={() => setDeleteUser(u)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Summary */}
      <p className="text-sm text-muted-foreground">
        {filtered.length} of {users.length} users shown
      </p>

      {/* Create Dialog */}
      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Add User</DialogTitle></DialogHeader>
          {formError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{formError}</div>
          )}
          <div className="space-y-4">
            <div>
              <Label>Full Name</Label>
              <Input value={formFullName} onChange={(e) => setFormFullName(e.target.value)} placeholder="John Doe" />
            </div>
            <div>
              <Label>Email <span className="text-destructive">*</span></Label>
              <Input type="email" value={formEmail} onChange={(e) => setFormEmail(e.target.value)} placeholder="user@example.com" />
            </div>
            <div>
              <Label>Password <span className="text-destructive">*</span></Label>
              <Input type="password" value={formPassword} onChange={(e) => setFormPassword(e.target.value)} placeholder="Minimum 8 characters" />
            </div>
            <div>
              <Label>Role</Label>
              <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={formRole} onChange={(e) => setFormRole(e.target.value)}>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="staff">Staff</option>
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialog(false)}>Cancel</Button>
            <Button onClick={handleCreate} disabled={saving || !formEmail || !formPassword}>
              {saving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Creating...</> : "Create User"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editUser} onOpenChange={() => setEditUser(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Edit User</DialogTitle></DialogHeader>
          {editError && (
            <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">{editError}</div>
          )}
          <div className="space-y-4">
            <div>
              <Label>Full Name</Label>
              <Input value={editFullName} onChange={(e) => setEditFullName(e.target.value)} />
            </div>
            <div>
              <Label>Email</Label>
              <Input type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} />
            </div>
            <div>
              <Label>Role</Label>
              <select className="h-9 w-full rounded-md border bg-background px-3 text-sm" value={editRoleId} onChange={(e) => setEditRoleId(Number(e.target.value))}>
                {ROLE_OPTIONS.map((r) => (
                  <option key={r.id} value={r.id}>{r.name.charAt(0).toUpperCase() + r.name.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditUser(null)}>Cancel</Button>
            <Button onClick={handleEdit} disabled={editSaving}>
              {editSaving ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</> : "Save Changes"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteUser} onOpenChange={() => setDeleteUser(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Delete User</DialogTitle></DialogHeader>
          <p className="text-sm text-muted-foreground">
            Are you sure you want to delete <strong>{deleteUser?.full_name || deleteUser?.email}</strong>?
            This will deactivate their account.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteUser(null)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
