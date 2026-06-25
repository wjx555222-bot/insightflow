import { useEffect, useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  ShoppingCart,
  Users,
  Package,
  Warehouse,
  BarChart3,
  Bot,
  FileText,
  ScrollText,
  LogOut,
  Menu,
  X,
  ChevronLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/stores/authStore";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Separator } from "@/components/ui/separator";
import { Toaster } from "@/components/ui/toaster";

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  adminOnly?: boolean;
}

const navItems: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Orders", href: "/orders", icon: ShoppingCart },
  { label: "Customers", href: "/customers", icon: Users },
  { label: "Products", href: "/products", icon: Package },
  { label: "Inventory", href: "/inventory", icon: Warehouse },
  { label: "Analytics", href: "/analytics", icon: BarChart3 },
  { label: "AI Assistant", href: "/ai-assistant", icon: Bot },
  { label: "Reports", href: "/reports", icon: FileText },
  {
    label: "Audit Logs",
    href: "/audit-logs",
    icon: ScrollText,
    adminOnly: true,
  },
];

export default function DashboardLayout() {
  const { user, logout, fetchUser } = useAuthStore();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const isAdmin = user?.role?.name === "admin" || user?.role?.name === "manager";

  const filteredNavItems = navItems.filter(
    (item) => !item.adminOnly || isAdmin,
  );

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col bg-sidebar text-sidebar-foreground transition-all duration-300 lg:relative lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
          collapsed ? "w-16" : "w-64",
        )}
      >
        <div className="flex h-16 items-center justify-between px-4">
          {!collapsed && (
            <h1 className="text-lg font-bold tracking-tight text-white">
              InsightFlow
            </h1>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="hidden text-sidebar-foreground hover:bg-sidebar-accent hover:text-white lg:flex"
            onClick={() => setCollapsed(!collapsed)}
          >
            <ChevronLeft
              className={cn(
                "h-4 w-4 transition-transform",
                collapsed && "rotate-180",
              )}
            />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="text-sidebar-foreground hover:bg-sidebar-accent hover:text-white lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <Separator className="bg-sidebar-border" />

        <nav className="flex-1 space-y-1 overflow-y-auto px-2 py-4">
          {filteredNavItems.map((item) => (
            <NavLink
              key={item.href}
              to={item.href}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors",
                  "hover:bg-sidebar-accent hover:text-white",
                  isActive
                    ? "bg-sidebar-accent text-white"
                    : "text-sidebar-foreground/70",
                  collapsed && "justify-center px-2",
                )
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </NavLink>
          ))}
        </nav>

        <Separator className="bg-sidebar-border" />

        <div className="p-3">
          <div
            className={cn(
              "flex items-center gap-3",
              collapsed && "justify-center",
            )}
          >
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-sidebar-accent text-xs text-white">
                {user ? getInitials(user.full_name || user.email) : "U"}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex-1 overflow-hidden">
                <p className="truncate text-sm font-medium text-white">
                  {user?.full_name || user?.email || "User"}
                </p>
                <p className="truncate text-xs text-sidebar-foreground/60">
                  {user?.role?.name || "viewer"}
                </p>
              </div>
            )}
            {!collapsed && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 shrink-0 text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-white"
                onClick={handleLogout}
              >
                <LogOut className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center gap-4 border-b bg-white px-4 md:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex-1" />

          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground md:block">
              {user?.email}
            </span>
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary text-xs text-primary-foreground">
                {user ? getInitials(user.full_name || user.email) : "U"}
              </AvatarFallback>
            </Avatar>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>

      <Toaster />
    </div>
  );
}
