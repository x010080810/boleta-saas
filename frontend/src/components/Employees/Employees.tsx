import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { companiesApi } from '../../services/api';
import { UserPlus, Download } from 'lucide-react';
import type { Employee, Company } from '../../types';

export default function Employees() {
  const { selectedCompany, companies, isSuperAdmin } = useAuth();
  const [employees, setEmployees] = useState<(Employee & { company_name?: string; company_id?: string })[]>([]);
  const [companyFilter, setCompanyFilter] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    tipo_documento: '01',
    numero_documento: '',
    nombre_completo: '',
    email: '',
    cargo: '',
    fecha_ingreso: '',
  });

  useEffect(() => {
    if (selectedCompany) loadEmployees();
  }, [selectedCompany]);

  const loadEmployees = async () => {
    if (!selectedCompany) return;
    const targetCompanies = isSuperAdmin ? companies : [selectedCompany];
    const results = await Promise.all(
      targetCompanies.map(async (c: Company) => {
        try {
          const res = await companiesApi.employees(c.id);
          return (res.data || []).map((emp: Employee) => ({ ...emp, company_name: c.name, company_id: c.id }));
        } catch {
          return [];
        }
      })
    );
    const merged = results.flat();
    setEmployees(merged);
    if (isSuperAdmin && !companyFilter) {
      setCompanyFilter('');
    }
  };

  const handleCreateEmployee = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCompany) return;
    await companiesApi.createEmployee(selectedCompany.id, form);
    setShowForm(false);
    setForm({ tipo_documento: '01', numero_documento: '', nombre_completo: '', email: '', cargo: '', fecha_ingreso: '' });
    loadEmployees();
  };

  const filteredEmployees = companyFilter
    ? employees.filter((emp) => emp.company_id === companyFilter)
    : employees;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-gray-900">Empleados</h2>
          <p className="text-sm text-gray-500">{filteredEmployees.length} registrados</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2 w-full sm:w-auto justify-center">
            <UserPlus size={16} />
            Nuevo Empleado
          </button>
        </div>
      </div>

      {isSuperAdmin && (
        <div className="card mb-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Filtrar por Empresa:</label>
            <select value={companyFilter} onChange={(e) => setCompanyFilter(e.target.value)} className="input-field max-w-xs">
              <option value="">Todas las empresas</option>
              {companies.map((c: Company) => (
                <option key={c.id} value={c.id}>{c.name} - {c.ruc}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      {showForm && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">Registrar Empleado</h3>
            <form onSubmit={handleCreateEmployee} className="space-y-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo Doc.</label>
                  <select value={form.tipo_documento} onChange={(e) => setForm({...form, tipo_documento: e.target.value})} className="input-field">
                    <option value="01">DNI</option>
                    <option value="04">Carné de Extranjería</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">N° Documento</label>
                  <input value={form.numero_documento} onChange={(e) => setForm({...form, numero_documento: e.target.value})} className="input-field" required />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Completo</label>
                <input value={form.nombre_completo} onChange={(e) => setForm({...form, nombre_completo: e.target.value})} className="input-field" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} className="input-field" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cargo</label>
                  <input value={form.cargo} onChange={(e) => setForm({...form, cargo: e.target.value})} className="input-field" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha Ingreso</label>
                  <input type="date" value={form.fecha_ingreso} onChange={(e) => setForm({...form, fecha_ingreso: e.target.value})} className="input-field" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
                <button type="submit" className="btn-primary">Guardar</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                {isSuperAdmin && <th className="pb-3 font-medium">Empresa</th>}
                <th className="pb-3 font-medium">Documento</th>
                <th className="pb-3 font-medium">Nombre</th>
                <th className="pb-3 font-medium">Email</th>
                <th className="pb-3 font-medium">Cargo</th>
                <th className="pb-3 font-medium">Ingreso</th>
              </tr>
            </thead>
            <tbody>
              {filteredEmployees.map((emp) => (
                <tr key={emp.id} className="border-b last:border-0 hover:bg-gray-50">
                  {isSuperAdmin && <td className="py-3 text-xs text-gray-500 max-w-[120px] truncate">{emp.company_name}</td>}
                  <td className="py-3">{emp.tipo_documento === '01' ? 'DNI' : 'CE'} {emp.numero_documento}</td>
                  <td className="py-3 font-medium">{emp.nombre_completo}</td>
                  <td className="py-3 text-gray-500">{emp.email || '-'}</td>
                  <td className="py-3 text-gray-500">{emp.cargo || '-'}</td>
                  <td className="py-3 text-gray-500">{emp.fecha_ingreso || '-'}</td>
                </tr>
              ))}
              {filteredEmployees.length === 0 && (
                <tr><td colSpan={isSuperAdmin ? 6 : 5} className="py-8 text-center text-gray-400">No hay empleados registrados</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
