import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import {
  LayoutDashboard, Users, Upload, Clock, Settings,
  Shield, LogOut, Building2, ChevronDown, Menu, X,
} from 'lucide-react';
import { useState } from 'react';

const navItems = [
  { to: '/employees', icon: Users, label: 'Empleados' },
  { to: '/payroll/upload', icon: Upload, label: 'Subir Planilla' },
  { to: '/payroll/history', icon: Clock, label: 'Historial' },
  { to: '/settings', icon: Settings, label: 'Configuración' },
];

const adminItems = [
  { to: '/admin', icon: Shield, label: 'Panel Admin' },
  { to: '/admin/companies', icon: Building2, label: 'Empresas' },
  { to: '/admin/settings', icon: Settings, label: 'Config. Sistema' },
];

export default function Layout() {
  const { user, companies, selectedCompany, selectCompany, isSuperAdmin, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showCompanies, setShowCompanies] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path: string) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  const sidebarContent = (
    <>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-blue-600">Boleta SaaS</h1>
            <p className="text-xs text-gray-500 mt-1">Sistema de Boletas de Pago</p>
          </div>
          <button onClick={() => setSidebarOpen(false)} className="p-1 text-gray-400 hover:text-gray-600 md:hidden">
            <X size={20} />
          </button>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.filter((item) => !isSuperAdmin || item.to !== '/settings').map((item) => (
          <Link
            key={item.to}
            to={item.to}
            onClick={() => setSidebarOpen(false)}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              isActive(item.to)
                ? 'bg-blue-50 text-blue-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <item.icon size={18} />
            {item.label}
          </Link>
        ))}

        {isSuperAdmin && (
          <>
            <div className="pt-4 pb-2">
              <p className="px-3 text-xs font-semibold text-gray-400 uppercase">Super Admin</p>
            </div>
            {adminItems.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive(item.to)
                    ? 'bg-purple-50 text-purple-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <item.icon size={18} />
                {item.label}
              </Link>
            ))}
          </>
        )}
      </nav>

      <div className="p-3 border-t border-gray-200 space-y-2">
        {selectedCompany && !isSuperAdmin && (
          <div className="relative">
            <button
              onClick={() => setShowCompanies(!showCompanies)}
              className="flex items-center justify-between w-full px-3 py-2 text-sm bg-gray-50 rounded-lg hover:bg-gray-100"
            >
              <div className="flex items-center gap-2 truncate">
                <Building2 size={16} className="text-gray-400" />
                <span className="truncate">{selectedCompany.name}</span>
              </div>
              <ChevronDown size={14} />
            </button>
            {showCompanies && (
              <div className="absolute bottom-full mb-1 w-full bg-white border rounded-lg shadow-lg z-10">
                {companies.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => { selectCompany(c); setShowCompanies(false); }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                      c.id === selectedCompany.id ? 'bg-blue-50 text-blue-700' : ''
                    }`}
                  >
                    {c.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between px-3 py-2">
          <div className="text-sm min-w-0">
            <p className="font-medium text-gray-700 truncate max-w-[140px]">{user?.full_name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
          <button onClick={handleLogout} className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-gray-100 shrink-0">
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </>
  );

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 bg-white border-r border-gray-200 flex flex-col transform transition-transform duration-200 ease-in-out md:relative md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Main */}
      <main className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center gap-3 p-4 border-b border-gray-200 bg-white md:hidden">
          <button onClick={() => setSidebarOpen(true)} className="p-1 text-gray-500 hover:text-gray-700">
            <Menu size={22} />
          </button>
          <h1 className="text-lg font-bold text-blue-600">Boleta SaaS</h1>
        </div>
        <div className="flex-1 overflow-y-auto p-4 md:p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
