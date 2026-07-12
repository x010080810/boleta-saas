import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './hooks/useAuth';
import Layout from './components/Layout/Layout';
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';
import Dashboard from './components/Dashboard/Dashboard';
import Employees from './components/Employees/Employees';
import PayrollUpload from './components/Payroll/PayrollUpload';
import PayrollHistory from './components/Payroll/PayrollHistory';
import PayrollReport from './components/Payroll/PayrollReport';
import Configuration from './components/Configuration/Configuration';
import AdminCompanies from './components/Admin/AdminCompanies';
import AdminCompanyDetail from './components/Admin/AdminCompanyDetail';
import AdminDashboard from './components/Admin/AdminDashboard';
import AdminSystemSettings from './components/Admin/AdminSystemSettings';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen">Cargando...</div>;
  if (!user) return <Navigate to="/login" />;
  return <>{children}</>;
}

function AppRoutes() {
  const { isSuperAdmin } = useAuth();

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route index element={isSuperAdmin ? <Dashboard /> : <Navigate to="/payroll/history" />} />
        <Route path="employees" element={<Employees />} />
        <Route path="payroll/upload" element={<PayrollUpload />} />
        <Route path="payroll/history" element={<PayrollHistory />} />
        <Route path="payroll/report/:uploadId" element={<PayrollReport />} />
        <Route path="settings" element={<Configuration />} />
        {isSuperAdmin && (
          <>
            <Route path="admin" element={<AdminDashboard />} />
            <Route path="admin/companies" element={<AdminCompanies />} />
            <Route path="admin/companies/:id" element={<AdminCompanyDetail />} />
            <Route path="admin/settings" element={<AdminSystemSettings />} />
          </>
        )}
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}
