import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { adminApi } from '../../services/api';
import { ArrowLeft, Save, Clock, History, UserPlus, UserX, Shield, ToggleLeft, ToggleRight, Trash2 } from 'lucide-react';

export default function AdminCompanyDetail() {
  const { id } = useParams();
  const [company, setCompany] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [form, setForm] = useState({
    plan_envios_mes: 100,
    licencia_inicio: '',
    licencia_fin: '',
    dias_gracia: 60,
  });

  const [showUserModal, setShowUserModal] = useState(false);
  const [userForm, setUserForm] = useState({ email: '', password: '', full_name: '', role: 'admin' });
  const [userSaving, setUserSaving] = useState(false);
  const [userMessage, setUserMessage] = useState('');

  useEffect(() => {
    if (!id) return;
    loadCompany();
    adminApi.licenseHistory(id).then((res) => setHistory(res.data)).catch(console.error);
  }, [id]);

  const loadCompany = () => {
    if (!id) return;
    adminApi.getCompany(id).then((res) => {
      setCompany(res.data);
      setForm({
        plan_envios_mes: res.data.plan_envios_mes || 100,
        licencia_inicio: res.data.licencia_inicio || '',
        licencia_fin: res.data.licencia_fin || '',
        dias_gracia: 60,
      });
    }).catch(console.error);
  };

  const handleSave = async () => {
    if (!id) return;
    setSaving(true);
    setMessage('');
    try {
      await adminApi.updateLicense(id, form);
      setMessage('Licencia actualizada correctamente');
      loadCompany();
    } catch (err: any) {
      setMessage(err.response?.data?.detail || 'Error al actualizar');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;
    setUserSaving(true);
    setUserMessage('');
    try {
      await adminApi.createUser({ ...userForm, company_id: id });
      setUserMessage('Usuario creado y asignado correctamente');
      setUserForm({ email: '', password: '', full_name: '', role: 'admin' });
      setTimeout(() => setShowUserModal(false), 1000);
      loadCompany();
    } catch (err: any) {
      setUserMessage(err.response?.data?.detail || 'Error al crear usuario');
    } finally {
      setUserSaving(false);
    }
  };

  const handleToggleActive = async (userId: string, current: boolean) => {
    if (!id) return;
    try {
      await adminApi.updateAssignment(id, userId, { is_active: !current });
      loadCompany();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleChangeRole = async (userId: string, newRole: string) => {
    if (!id) return;
    try {
      await adminApi.updateAssignment(id, userId, { role: newRole });
      loadCompany();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al actualizar');
    }
  };

  const handleRemoveUser = async (userId: string, fullName: string) => {
    if (!id) return;
    if (!confirm(`¿Eliminar a "${fullName}" de esta empresa?`)) return;
    try {
      await adminApi.removeAssignment(id, userId);
      loadCompany();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Error al eliminar');
    }
  };

  if (!company) return <div className="text-center py-20 text-gray-400">Cargando...</div>;

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <Link to="/admin/companies" className="p-2 hover:bg-gray-100 rounded-lg">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h2 className="text-xl font-bold text-gray-900">{company.name}</h2>
          <p className="text-sm text-gray-500">RUC: {company.ruc}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Save size={18} />
            Configurar Licencia
          </h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Plan de Envíos por Mes</label>
            <input
              type="number"
              value={form.plan_envios_mes}
              onChange={(e) => setForm({...form, plan_envios_mes: Number(e.target.value)})}
              className="input-field"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Inicio de Licencia</label>
              <input
                type="date"
                value={form.licencia_inicio}
                onChange={(e) => setForm({...form, licencia_inicio: e.target.value})}
                className="input-field"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Fin de Licencia</label>
              <input
                type="date"
                value={form.licencia_fin}
                onChange={(e) => setForm({...form, licencia_fin: e.target.value})}
                className="input-field"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Días de Gracia</label>
            <input
              type="number"
              value={form.dias_gracia}
              onChange={(e) => setForm({...form, dias_gracia: Number(e.target.value)})}
              className="input-field"
            />
          </div>

          {message && (
            <div className={`px-4 py-2 rounded-lg text-sm ${message.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
              {message}
            </div>
          )}

          <button onClick={handleSave} disabled={saving} className="btn-primary w-full flex items-center justify-center gap-2">
            <Save size={16} />
            {saving ? 'Guardando...' : 'Guardar Cambios'}
          </button>
        </div>

        <div className="card space-y-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <History size={18} />
            Estado Actual
          </h3>

          <div className="space-y-3 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Estado</span>
              <span className={`badge ${
                company.licencia_estado === 'activa' ? 'badge-success' :
                company.licencia_estado === 'por_vencer' ? 'badge-warning' :
                company.licencia_estado === 'grace_period' ? 'badge-info' : 'badge-danger'
              }`}>{company.licencia_estado}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Inicio</span>
              <span>{company.licencia_inicio || '-'}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Fin</span>
              <span>{company.licencia_fin || '-'}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Grace Hasta</span>
              <span>{company.licencia_grace_hasta || '-'}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-500">Plan</span>
              <span>{company.plan_envios_mes} envíos/mes</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-500">Activo</span>
              <span className={company.is_active ? 'badge-success' : 'badge-danger'}>
                {company.is_active ? 'Sí' : 'No'}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900 flex items-center gap-2">
            <Shield size={18} />
            Usuarios de la Empresa
          </h3>
          <button onClick={() => setShowUserModal(true)} className="btn-primary flex items-center gap-2 text-sm">
            <UserPlus size={16} />
            Agregar Usuario
          </button>
        </div>

        {(!company.users || company.users.length === 0) ? (
          <p className="text-sm text-gray-400 text-center py-4">No hay usuarios asignados</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-3 font-medium">Nombre</th>
                  <th className="pb-3 font-medium">Email</th>
                  <th className="pb-3 font-medium">Rol</th>
                  <th className="pb-3 font-medium">Estado</th>
                  <th className="pb-3 font-medium">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {company.users.map((u: any) => (
                  <tr key={u.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-3 font-medium">{u.full_name}</td>
                    <td className="py-3 text-gray-500">{u.email}</td>
                    <td className="py-3">
                      <select
                        value={u.role}
                        onChange={(e) => handleChangeRole(u.id, e.target.value)}
                        className="text-xs border border-gray-200 rounded px-2 py-1"
                      >
                        <option value="admin">Admin</option>
                        <option value="viewer">Viewer</option>
                      </select>
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => handleToggleActive(u.id, u.is_active)}
                        className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full ${
                          u.is_active
                            ? 'bg-green-50 text-green-700 hover:bg-green-100'
                            : 'bg-red-50 text-red-700 hover:bg-red-100'
                        }`}
                      >
                        {u.is_active ? <><ToggleRight size={14} /> Activo</> : <><ToggleLeft size={14} /> Inactivo</>}
                      </button>
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => handleRemoveUser(u.id, u.full_name)}
                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg"
                        title="Remover de la empresa"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {history.length > 0 && (
        <div className="card mt-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock size={18} />
            Historial de Cambios de Licencia
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-500 border-b">
                  <th className="pb-3 font-medium">Tipo</th>
                  <th className="pb-3 font-medium">Inicio Anterior</th>
                  <th className="pb-3 font-medium">Fin Anterior</th>
                  <th className="pb-3 font-medium">Plan Ant.</th>
                  <th className="pb-3 font-medium">Inicio Nuevo</th>
                  <th className="pb-3 font-medium">Fin Nuevo</th>
                  <th className="pb-3 font-medium">Plan Nuevo</th>
                  <th className="pb-3 font-medium">Fecha</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className="border-b last:border-0 hover:bg-gray-50 text-xs">
                    <td className="py-3 capitalize">{h.tipo}</td>
                    <td className="py-3">{h.inicio_anterior || '-'}</td>
                    <td className="py-3">{h.fin_anterior || '-'}</td>
                    <td className="py-3">{h.plan_anterior || '-'}</td>
                    <td className="py-3">{h.inicio_nuevo || '-'}</td>
                    <td className="py-3">{h.fin_nuevo || '-'}</td>
                    <td className="py-3">{h.plan_nuevo || '-'}</td>
                    <td className="py-3">{h.creado_en ? new Date(h.creado_en).toLocaleDateString('es-PE') : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showUserModal && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Agregar Usuario</h3>
            <form onSubmit={handleCreateUser} className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo</label>
                <input
                  type="text"
                  value={userForm.full_name}
                  onChange={(e) => setUserForm({...userForm, full_name: e.target.value})}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={userForm.email}
                  onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
                <input
                  type="password"
                  value={userForm.password}
                  onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                  className="input-field"
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
                <select
                  value={userForm.role}
                  onChange={(e) => setUserForm({...userForm, role: e.target.value})}
                  className="input-field"
                >
                  <option value="admin">Admin</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              {userMessage && (
                <div className={`px-4 py-2 rounded-lg text-sm ${userMessage.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                  {userMessage}
                </div>
              )}
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => { setShowUserModal(false); setUserMessage(''); }} className="btn-secondary">
                  Cancelar
                </button>
                <button type="submit" disabled={userSaving} className="btn-primary">
                  {userSaving ? 'Creando...' : 'Crear Usuario'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
