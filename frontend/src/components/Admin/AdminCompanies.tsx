import { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Link } from 'react-router-dom';
import { Search, Building2 } from 'lucide-react';

export default function AdminCompanies() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    adminApi.companies().then((res) => setCompanies(res.data)).catch(console.error);
  }, []);

  const filtered = companies.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.ruc.includes(search)
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Empresas</h2>
      </div>

      <div className="card mb-6">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-9"
            placeholder="Buscar por nombre o RUC..."
          />
        </div>
      </div>

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-3 font-medium">Empresa</th>
                <th className="pb-3 font-medium">RUC</th>
                <th className="pb-3 font-medium">Plan</th>
                <th className="pb-3 font-medium">Licencia</th>
                <th className="pb-3 font-medium">Estado</th>
                <th className="pb-3 font-medium">Consumo</th>
                <th className="pb-3 font-medium"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((c) => (
                <tr key={c.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="py-3 font-medium">{c.name}</td>
                  <td className="py-3 font-mono text-xs">{c.ruc}</td>
                  <td className="py-3">{c.plan_envios_mes}/mes</td>
                  <td className="py-3 text-xs">
                    {c.licencia_fin || '-'}
                  </td>
                  <td className="py-3">
                    <span className={`badge ${
                      c.licencia_estado === 'activa' ? 'badge-success' :
                      c.licencia_estado === 'por_vencer' ? 'badge-warning' :
                      c.licencia_estado === 'grace_period' ? 'badge-info' :
                      'badge-danger'
                    }`}>
                      {c.licencia_estado}
                    </span>
                  </td>
                  <td className="py-3 text-xs">
                    {c.quota_utilizada}/{c.quota_limite}
                  </td>
                  <td className="py-3">
                    <Link to={`/admin/companies/${c.id}`} className="text-blue-600 hover:underline text-xs">
                      Gestionar
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
