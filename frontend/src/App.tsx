import { Routes, Route, Navigate } from "react-router-dom";
import DashboardLayout from "@/layouts/DashboardLayout";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import Orders from "@/pages/Orders";
import Customers from "@/pages/Customers";
import Products from "@/pages/Products";
import Inventory from "@/pages/Inventory";
import Analytics from "@/pages/Analytics";
import AIAssistant from "@/pages/AIAssistant";
import Reports from "@/pages/Reports";
import AdminUsers from "@/pages/AdminUsers";
import AuditLogs from "@/pages/AuditLogs";
import { useAuthStore } from "@/stores/authStore";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/orders" element={<Orders />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/products" element={<Products />} />
        <Route path="/inventory" element={<Inventory />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/ai-assistant" element={<AIAssistant />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/admin/users" element={<AdminUsers />} />
        <Route path="/audit-logs" element={<AuditLogs />} />
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

export default App;
