import { useEffect, useState } from 'react';
import { adminApi } from '../../services/api';
import { Link } from 'react-router-dom';
import { Search, Building2, Plus, X, Loader } from 'lucide-react';

export default function AdminCompanies() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const todayStr = new Date().toISOString().split('T')[0];
  const nextMonth = new Date(Date.now() + 30*86400000).toISOString().split('T')[0];
  const [form, setForm] = useState({
    company_name: '',
    company_ruc: '',
    admin_full_name: '',
    admin_email: '',
    admin_password: '',
    plan_envios_mes: 50,
    licencia_inicio: todayStr,
    licencia_fin: nextMonth,
    dias_gracia: 60,
  });

  useEffect(() => {
    adminApi.companies().then((res) => setCompanies(res.data)).catch(console.error);
  }, []);

  const filtered = companies.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.ruc.includes(search)
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await adminApi.createCompany(form);
      setResult(res.data);
      setCompanies((prev) => [...prev, {
        id: res.data.company_id,
        name: res.data.company_name,
        ruc: '',
        plan_envios_mes: form.plan_envios_mes,
        licencia_fin: '',
        licencia_estado: 'activa',
        quota_utilizada: 0,
        quota_limite: form.plan_envios_mes,
      }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al crear empresa');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({ company_name: '', company_ruc: '', admin_full_name: '', admin_email: '', admin_password: '', plan_envios_mes: 50, licencia_inicio: todayStr, licencia_fin: nextMonth, dias_gracia: 60 });
    setResult(null);
    setError('');
    setShowModal(false);
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Empresas</h2>
        <button onClick={() => setShowModal(true)} className="btn btn-primary flex items-center gap-2">
          <Plus size={18} /> Crear Empresa
        </button>
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

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-bold text-gray-900">Nueva Empresa</h3>
              <button onClick={resetForm} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
            </div>

            {result ? (
              <div className="p-6 space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 text-sm text-green-800">
                  Empresa creada exitosamente.
                </div>
                <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 space-y-2 text-sm">
                  <p className="font-semibold text-yellow-800">Credenciales del administrador:</p>
                  <p><span className="font-medium">Email:</span> {result.admin_email}</p>
                  <p><span className="font-medium">Contraseña:</span> <code className="bg-yellow-100 px-2 py-0.5 rounded text-base">{result.admin_password}</code></p>
                  <p className="text-yellow-700 text-xs mt-2">Guarde estas credenciales. No se mostrarán nuevamente.</p>
                </div>
                <button onClick={resetForm} className="btn btn-primary w-full">Cerrar</button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="p-6 space-y-4">
                {error && <div className="bg-red-50 border border-red-200 rounded-xl p-3 text-sm text-red-700">{error}</div>}

                <div>
                  <label className="label">Nombre de la empresa</label>
                  <input name="company_name" value={form.company_name} onChange={handleChange} required className="input-field" placeholder="Ej: Otero & Asociados S.A.C." />
                </div>
                <div>
                  <label className="label">RUC</label>
                  <input name="company_ruc" value={form.company_ruc} onChange={handleChange} required className="input-field" placeholder="12345678901" />
                </div>
                <div>
                  <label className="label">Nombre del administrador</label>
                  <input name="admin_full_name" value={form.admin_full_name} onChange={handleChange} required className="input-field" placeholder="Nombre completo" />
                </div>
                <div>
                  <label className="label">Email del administrador</label>
                  <input name="admin_email" type="email" value={form.admin_email} onChange={handleChange} required className="input-field" placeholder="admin@correo.com" />
                </div>
                <div>
                  <label className="label">Contraseña <span className="text-gray-400 font-normal">(opcional — se genera automáticamente si se deja vacío)</span></label>
                  <input name="admin_password" type="text" value={form.admin_password} onChange={handleChange} className="input-field" placeholder="Dejar vacío para generar automáticamente" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Envíos por mes</label>
                    <input name="plan_envios_mes" type="number" value={form.plan_envios_mes} onChange={handleChange} required className="input-field" min={1} />
                  </div>
                  <div>
                    <label className="label">Días de gracia</label>
                    <input name="dias_gracia" type="number" value={form.dias_gracia} onChange={handleChange} required className="input-field" min={0} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="label">Inicio de licencia</label>
                    <input name="licencia_inicio" type="date" value={form.licencia_inicio} onChange={handleChange} required className="input-field" />
                  </div>
                  <div>
                    <label className="label">Fin de licencia</label>
                    <input name="licencia_fin" type="date" value={form.licencia_fin} onChange={handleChange} required className="input-field" />
                  </div>
                </div>
                <button type="submit" disabled={loading} className="btn btn-primary w-full flex items-center justify-center gap-2">
                  {loading && <Loader size={18} className="animate-spin" />}
                  {loading ? 'Creando...' : 'Crear Empresa'}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
