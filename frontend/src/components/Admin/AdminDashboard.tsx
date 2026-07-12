import { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import {
  Shield, Building2, AlertTriangle, Clock, XCircle,
  TrendingUp, BarChart3, Activity, Upload,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, Legend,
} from 'recharts';

const COLORS = ['#3b82f6', '#22c55e', '#eab308', '#f97316', '#ef4444'];
const PIE_COLORS = ['#22c55e', '#eab308', '#f97316', '#ef4444'];

export default function AdminDashboard() {
  const [data, setData] = useState<any>(null);
  const [expiring, setExpiring] = useState<any[]>([]);
  const [grace, setGrace] = useState<any[]>([]);

  useEffect(() => {
    adminApi.dashboard().then((res) => setData(res.data)).catch(console.error);
    adminApi.expiring(15).then((res) => setExpiring(res.data)).catch(console.error);
    adminApi.gracePeriod().then((res) => setGrace(res.data)).catch(console.error);
  }, []);

  const licensePie = data ? [
    { name: 'Activas', value: data.activas },
    { name: 'Por Vencer', value: data.por_vencer },
    { name: 'Grace Period', value: data.grace_period },
    { name: 'Bajas', value: data.bajas },
  ].filter((d) => d.value > 0) : [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Panel Super Admin</h2>
        {data && (
          <span className="text-sm text-gray-500">
            <Upload size={14} className="inline mr-1" />
            {data.uploads_del_mes} subidas este mes
          </span>
        )}
      </div>

      {data && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-4 mb-6">
            {[
              { label: 'Total Empresas', value: data.total_empresas, icon: Building2, color: 'text-blue-600 bg-blue-50' },
              { label: 'Activas', value: data.activas, icon: Shield, color: 'text-green-600 bg-green-50' },
              { label: 'Por Vencer', value: data.por_vencer, icon: AlertTriangle, color: 'text-yellow-600 bg-yellow-50' },
              { label: 'Grace Period', value: data.grace_period, icon: Clock, color: 'text-orange-600 bg-orange-50' },
              { label: 'Bajas', value: data.bajas, icon: XCircle, color: 'text-red-600 bg-red-50' },
            ].map((stat) => (
              <div key={stat.label} className="card flex items-center gap-3">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <stat.icon size={24} />
                </div>
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-xs text-gray-500">{stat.label}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <TrendingUp size={18} className="text-blue-500" />
                Envíos Mensuales (últimos 12 meses)
              </h3>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={data.monthly_sends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="mes" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="enviados" name="Enviados" fill="#22c55e" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="fallidos" name="Fallidos" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <BarChart3 size={18} className="text-purple-500" />
                Distribución de Licencias
              </h3>
              {licensePie.length > 0 && (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie data={licensePie} cx="50%" cy="50%" innerRadius={50} outerRadius={90} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                      {licensePie.map((_, idx) => (
                        <Cell key={idx} fill={PIE_COLORS[idx % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="lg:col-span-2 card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Activity size={18} className="text-indigo-500" />
                Subidas Diarias (últimos 30 días)
              </h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={data.daily_uploads}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="fecha" tick={{ fontSize: 10 }} tickFormatter={(v) => v.slice(5)} />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="subidas" name="Subidas" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Building2 size={18} className="text-emerald-500" />
                Top Empresas por Envíos
              </h3>
              <div className="space-y-2 max-h-[180px] overflow-y-auto">
                {data.top_companies.map((c: any, i: number) => (
                  <Link key={c.id} to={`/admin/companies/${c.id}`}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50 transition-colors">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-bold text-gray-400 w-5">{i + 1}</span>
                      <span className="text-sm truncate">{c.name}</span>
                    </div>
                    <span className="text-xs font-medium text-blue-600 whitespace-nowrap">{c.total_enviados} env.</span>
                  </Link>
                ))}
                {data.top_companies.length === 0 && (
                  <p className="text-sm text-gray-400">Sin datos aún</p>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle size={18} className="text-yellow-500" />
                Empresas Próximas a Vencer (15 días)
              </h3>
              {expiring.length === 0 ? (
                <p className="text-sm text-gray-400">No hay empresas próximas a vencer</p>
              ) : (
                <div className="space-y-2 max-h-[250px] overflow-y-auto">
                  {expiring.map((e) => (
                    <Link key={e.id} to={`/admin/companies/${e.id}`}
                      className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors">
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{e.name}</p>
                        <p className="text-xs text-gray-500">RUC: {e.ruc}</p>
                      </div>
                      <span className="text-xs font-medium text-yellow-700 whitespace-nowrap">Vence: {e.licencia_fin}</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Clock size={18} className="text-orange-500" />
                Empresas en Grace Period
              </h3>
              {grace.length === 0 ? (
                <p className="text-sm text-gray-400">No hay empresas en período de gracia</p>
              ) : (
                <div className="space-y-2 max-h-[250px] overflow-y-auto">
                  {grace.map((g) => (
                    <Link key={g.id} to={`/admin/companies/${g.id}`}
                      className="flex items-center justify-between p-3 bg-orange-50 rounded-lg hover:bg-orange-100 transition-colors">
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate">{g.name}</p>
                        <p className="text-xs text-gray-500">RUC: {g.ruc}</p>
                      </div>
                      <span className="text-xs font-medium text-orange-700 whitespace-nowrap">{g.dias_restantes} días</span>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
