import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { payrollApi } from '../../services/api';
import { Search, Eye, Download } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { PayrollUpload, Company } from '../../types';

export default function PayrollHistory() {
  const { selectedCompany, companies, isSuperAdmin } = useAuth();
  const [uploads, setUploads] = useState<(PayrollUpload & { company_name?: string; company_id?: string })[]>([]);
  const [search, setSearch] = useState('');
  const [tipoFilter, setTipoFilter] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');

  useEffect(() => {
    if (selectedCompany) loadUploads();
  }, [selectedCompany]);

  const loadUploads = async () => {
    if (!selectedCompany) return;
    const targetCompanies = isSuperAdmin ? companies : [selectedCompany];
    const results = await Promise.all(
      targetCompanies.map(async (c: Company) => {
        try {
          const params: any = {};
          if (search) params.ticket = search;
          if (tipoFilter) params.tipo_planilla = tipoFilter;
          const res = await payrollApi.list(c.id, params);
          return (res.data || []).map((u: PayrollUpload) => ({ ...u, company_name: c.name, company_id: c.id }));
        } catch {
          return [];
        }
      })
    );
    setUploads(results.flat());
  };

  const filteredUploads = companyFilter
    ? uploads.filter((u) => u.company_id === companyFilter)
    : uploads;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Historial de Cargas</h2>
      </div>

      <div className="card mb-6">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-end">
          <div className="flex-1 w-full">
            <label className="block text-sm font-medium text-gray-700 mb-1">Buscar por Ticket</label>
            <div className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="input-field pl-9"
                placeholder="BLP-2025-..."
              />
            </div>
          </div>
          <div className="w-full sm:w-auto">
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select value={tipoFilter} onChange={(e) => setTipoFilter(e.target.value)} className="input-field">
              <option value="">Todos</option>
              <option value="ordinaria">Ordinaria</option>
              <option value="gratificacion">Gratificación</option>
              <option value="excepcional">Excepcional</option>
              <option value="cts">CTS</option>
              <option value="vacaciones">Vacaciones</option>
            </select>
          </div>
          {isSuperAdmin && (
            <div className="w-full sm:w-auto">
              <label className="block text-sm font-medium text-gray-700 mb-1">Empresa</label>
              <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} className="input-field">
                <option value="">Todas</option>
                {companies.map((c: Company) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          )}
          <button onClick={loadUploads} className="btn-primary w-full sm:w-auto">Filtrar</button>
        </div>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                {isSuperAdmin && <th className="pb-3 font-medium">Empresa</th>}
                <th className="pb-3 font-medium">Ticket</th>
                <th className="pb-3 font-medium">Tipo</th>
                <th className="pb-3 font-medium">Período</th>
                <th className="pb-3 font-medium">Archivo</th>
                <th className="pb-3 font-medium">Reg.</th>
                <th className="pb-3 font-medium">Env.</th>
                <th className="pb-3 font-medium">Obs.</th>
                <th className="pb-3 font-medium">Estado</th>
                <th className="pb-3 font-medium">Fecha</th>
                <th className="pb-3 font-medium">Acción</th>
              </tr>
            </thead>
            <tbody>
              {filteredUploads.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50">
                  {isSuperAdmin && <td className="py-3 text-xs text-gray-500 max-w-[120px] truncate">{u.company_name}</td>}
                  <td className="py-3 font-mono text-xs">{u.ticket_number}</td>
                  <td className="py-3 capitalize">{u.tipo_planilla}</td>
                  <td className="py-3">{u.periodo}</td>
                  <td className="py-3 text-xs text-gray-500">{u.filename}</td>
                  <td className="py-3">{u.total_registros}</td>
                  <td className="py-3">{u.total_enviados}</td>
                  <td className="py-3">{u.total_observaciones}</td>
                  <td className="py-3">
                    <span className={`badge ${
                      u.estado === 'completed' ? 'badge-success' :
                      u.estado === 'processing' ? 'badge-warning' : 'badge-info'
                    }`}>
                      {u.estado}
                    </span>
                  </td>
                  <td className="py-3 text-xs text-gray-400">
                    {new Date(u.created_at).toLocaleDateString('es-PE')}
                  </td>
                  <td className="py-3">
                    <Link
                      to={`/payroll/report/${u.id}`}
                      className="flex items-center gap-1 text-blue-600 hover:underline text-xs"
                    >
                      <Eye size={14} />
                      Ver
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredUploads.length === 0 && (
                <tr><td colSpan={isSuperAdmin ? 11 : 10} className="py-8 text-center text-gray-400">No hay cargas registradas</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
