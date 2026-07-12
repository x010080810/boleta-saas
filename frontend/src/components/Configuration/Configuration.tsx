import { useEffect, useState } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { companiesApi, payrollApi } from '../../services/api';
import { Save, Mail, Key, Settings as SettingsIcon, Send } from 'lucide-react';

export default function Configuration() {
  const { selectedCompany, user } = useAuth();
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [quota, setQuota] = useState<any>(null);
  const [form, setForm] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_user: '',
    smtp_password: '',
    smtp_from_email: '',
    smtp_from_name: '',
    email_subject_template: 'Boleta de Pago - {{empresa}} - {{periodo}}',
    email_body_template: '',
  });

  useEffect(() => {
    if (selectedCompany) {
      companiesApi.get(selectedCompany.id).then((res) => {
        const c = res.data;
        setForm({
          smtp_host: c.smtp_host || '',
          smtp_port: c.smtp_port || 587,
          smtp_user: c.smtp_user || '',
          smtp_password: '',
          smtp_from_email: c.smtp_from_email || '',
          smtp_from_name: c.smtp_from_name || '',
          email_subject_template: c.email_subject_template || 'Boleta de Pago - {{empresa}} - {{periodo}}',
          email_body_template: c.email_body_template || '',
        });
      });
      payrollApi.quotaStatus(selectedCompany.id).then((res) => setQuota(res.data)).catch(console.error);
    }
  }, [selectedCompany]);

  const buildSaveData = () => {
    const data: any = {};
    if (form.smtp_host) data.smtp_host = form.smtp_host;
    if (form.smtp_port) data.smtp_port = form.smtp_port;
    if (form.smtp_user) data.smtp_user = form.smtp_user;
    if (form.smtp_password) data.smtp_password = form.smtp_password;
    if (form.smtp_from_email) data.smtp_from_email = form.smtp_from_email;
    if (form.smtp_from_name) data.smtp_from_name = form.smtp_from_name;
    data.email_subject_template = form.email_subject_template;
    data.email_body_template = form.email_body_template;
    return data;
  };

  const handleSave = async () => {
    if (!selectedCompany) return;
    setSaving(true);
    setMessage('');
    try {
      await companiesApi.update(selectedCompany.id, buildSaveData());
      setMessage('Configuración guardada correctamente');
    } catch (err) {
      setMessage('Error al guardar configuración');
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!selectedCompany) return;
    setTesting(true);
    setMessage('');
    try {
      const res = await companiesApi.testSmtp({
        smtp_host: form.smtp_host,
        smtp_port: form.smtp_port,
        smtp_user: form.smtp_user,
        smtp_password: form.smtp_password,
        from_email: form.smtp_from_email,
        from_name: form.smtp_from_name,
        test_email: user?.email || form.smtp_user,
      });
      await companiesApi.update(selectedCompany.id, buildSaveData());
      setMessage('Configuración guardada y conexión SMTP verificada correctamente');
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Error al probar conexión';
      setMessage(detail);
    } finally {
      setTesting(false);
    }
  };

  if (!selectedCompany) return null;

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-900 mb-6">Configuración</h2>

      {quota && (
        <div className="card mb-6">
          <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <SettingsIcon size={18} />
            Plan Mensual
          </h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Límite:</span>
              <p className="font-semibold text-lg">{quota.limite} envíos/mes</p>
            </div>
            <div>
              <span className="text-gray-500">Utilizados:</span>
              <p className="font-semibold text-lg">{quota.utilizados}</p>
            </div>
            <div>
              <span className="text-gray-500">Disponibles:</span>
              <p className={`font-semibold text-lg ${quota.disponibles < 10 ? 'text-red-600' : 'text-green-600'}`}>
                {quota.disponibles}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-2">Se reinicia cada mes</p>
        </div>
      )}

      <div className="card space-y-4">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <Mail size={18} />
          Configuración SMTP
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Servidor SMTP</label>
            <input value={form.smtp_host} onChange={(e) => setForm({...form, smtp_host: e.target.value})} className="input-field" placeholder="smtp.gmail.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Puerto</label>
            <input type="number" value={form.smtp_port} onChange={(e) => setForm({...form, smtp_port: Number(e.target.value)})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Usuario SMTP</label>
            <input value={form.smtp_user} onChange={(e) => setForm({...form, smtp_user: e.target.value})} className="input-field" placeholder="correo@empresa.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña SMTP</label>
            <input type="password" value={form.smtp_password} onChange={(e) => setForm({...form, smtp_password: e.target.value})} className="input-field" placeholder="••••••••" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correo Remitente</label>
            <input value={form.smtp_from_email} onChange={(e) => setForm({...form, smtp_from_email: e.target.value})} className="input-field" placeholder="no-reply@empresa.com" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Remitente</label>
            <input value={form.smtp_from_name} onChange={(e) => setForm({...form, smtp_from_name: e.target.value})} className="input-field" placeholder="Sistema de Boletas" />
          </div>
        </div>

        <h3 className="font-semibold text-gray-900 pt-4 flex items-center gap-2">
          <Key size={18} />
          Plantillas de Email
        </h3>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Asunto del correo
            <span className="text-gray-400 font-normal ml-2">(Variables: {'{{nombre}}'}, {'{{empresa}}'}, {'{{periodo}}'}, {'{{ticket}}'})</span>
          </label>
          <input value={form.email_subject_template} onChange={(e) => setForm({...form, email_subject_template: e.target.value})} className="input-field" />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Cuerpo del correo (HTML)
          </label>
          <textarea
            value={form.email_body_template}
            onChange={(e) => setForm({...form, email_body_template: e.target.value})}
            className="input-field h-32 font-mono text-xs"
            placeholder="<html><body>...</body></html>"
          />
        </div>

        {message && (
          <div className={`px-4 py-2 rounded-lg text-sm ${message.includes('Error') ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
            {message}
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={handleTest} disabled={testing} className="btn-secondary flex items-center justify-center gap-2 flex-1">
            <Send size={16} />
            {testing ? 'Probando...' : 'Probar Conexión'}
          </button>
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center justify-center gap-2 flex-1">
            <Save size={16} />
            {saving ? 'Guardando...' : 'Guardar Configuración'}
          </button>
        </div>
      </div>
    </div>
  );
}
