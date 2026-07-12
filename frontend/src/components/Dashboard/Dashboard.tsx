import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { payrollApi } from '../../services/api';
import { Upload, Send, AlertCircle, CheckCircle, Clock, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { PayrollUpload, QuotaStatus } from '../../types';

export default function Dashboard() {
  const { selectedCompany } = useAuth();
  const [uploads, setUploads] = useState<PayrollUpload[]>([]);
  const [quota, setQuota] = useState<QuotaStatus | null>(null);

  useEffect(() => {
    if (!selectedCompany) return;
    payrollApi.list(selectedCompany.id, { limit: 5 })
      .then((res) => setUploads(res.data))
      .catch(console.error);

    payrollApi.quotaStatus(selectedCompany.id)
      .then((res) => setQuota(res.data))
      .catch(console.error);
  }, [selectedCompany]);

  if (!selectedCompany) {
    return (
      <div className="text-center py-20 text-gray-500">
        <Building2 size={48} className="mx-auto mb-4 text-gray-300" />
        <p className="text-lg">Seleccione una empresa para comenzar</p>
      </div>
    );
  }

  const totalRegistros = uploads.reduce((a, b) => a + b.total_registros, 0);
  const totalEnviados = uploads.reduce((a, b) => a + b.total_enviados, 0);
  const totalObservaciones = uploads.reduce((a, b) => a + b.total_observaciones, 0);
  const totalFallidos = uploads.reduce((a, b) => a + b.total_fallidos, 0);

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-gray-900">Dashboard</h2>
          <p className="text-sm text-gray-500">{selectedCompany.name} - RUC: {selectedCompany.ruc}</p>
        </div>
        <Link to="/payroll/upload" className="btn-primary flex items-center justify-center gap-2 sm:w-auto">
          <Upload size={16} />
          Subir Planilla
        </Link>
      </div>

      {/* Quota */}
      {quota && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">Plan Mensual de Envíos</span>
            <span className="text-sm text-gray-500">
              {quota.utilizados} / {quota.limite} utilizados
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full ${
                quota.disponibles < 10 ? 'bg-red-500' : quota.disponibles < 30 ? 'bg-yellow-500' : 'bg-blue-600'
              }`}
              style={{ width: `${(quota.utilizados / quota.limite) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {quota.disponibles} envíos disponibles este mes
          </p>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4 mb-6">
        {[
          { label: 'Registros', value: totalRegistros, icon: Upload, color: 'text-blue-600 bg-blue-50' },
          { label: 'Enviados', value: totalEnviados, icon: Send, color: 'text-green-600 bg-green-50' },
          { label: 'Observaciones', value: totalObservaciones, icon: AlertCircle, color: 'text-yellow-600 bg-yellow-50' },
          { label: 'Fallidos', value: totalFallidos, icon: AlertCircle, color: 'text-red-600 bg-red-50' },
        ].map((stat) => (
          <div key={stat.label} className="card flex items-center gap-4">
            <div className={`p-3 rounded-lg ${stat.color}`}>
              <stat.icon size={24} />
            </div>
            <div>
              <p className="text-2xl font-bold">{stat.value}</p>
              <p className="text-sm text-gray-500">{stat.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Uploads */}
      <div className="card">
        <h3 className="font-semibold text-gray-900 mb-4">Últimas Cargas</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-3 font-medium">Ticket</th>
                <th className="pb-3 font-medium">Tipo</th>
                <th className="pb-3 font-medium">Período</th>
                <th className="pb-3 font-medium">Registros</th>
                <th className="pb-3 font-medium">Enviados</th>
                <th className="pb-3 font-medium">Estado</th>
                <th className="pb-3 font-medium">Fecha</th>
              </tr>
            </thead>
            <tbody>
              {uploads.length === 0 && (
                <tr><td colSpan={7} className="py-8 text-center text-gray-400">No hay cargas aún</td></tr>
              )}
              {uploads.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 font-mono text-xs">{u.ticket_number}</td>
                  <td className="py-3 capitalize">{u.tipo_planilla}</td>
                  <td className="py-3">{u.periodo}</td>
                  <td className="py-3">{u.total_registros}</td>
                  <td className="py-3">{u.total_enviados}</td>
                  <td className="py-3">
                    <span className={`badge ${
                      u.estado === 'completed' ? 'badge-success' :
                      u.estado === 'processing' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {u.estado === 'completed' ? 'Completado' : u.estado}
                    </span>
                  </td>
                  <td className="py-3 text-gray-400 text-xs">
                    {new Date(u.created_at).toLocaleDateString('es-PE')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {uploads.length > 0 && (
          <Link to="/payroll/history" className="text-sm text-blue-600 hover:underline mt-4 inline-block">
            Ver todas las cargas →
          </Link>
        )}
      </div>
    </div>
  );
}

function Building2({ size, className }: { size: number; className?: string }) {
  return (
    <svg width={size} height={size} className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );
}
