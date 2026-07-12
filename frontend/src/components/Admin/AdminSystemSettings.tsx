import { useEffect, useState } from 'react';
import { adminApi, companiesApi } from '../../services/api';
import { Save, Loader, AlertCircle, CheckCircle, Mail } from 'lucide-react';

export default function AdminSystemSettings() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    adminApi.getSystemSettings().then((res) => {
      setSettings(res.data);
    }).catch(() => {
      setMessage({ type: 'error', text: 'Error al cargar configuración' });
    }).finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      await adminApi.updateSystemSettings(settings);
      setMessage({ type: 'success', text: 'Configuración guardada correctamente' });
    } catch {
      setMessage({ type: 'error', text: 'Error al guardar configuración' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    if (!settings?.notification_email) {
      setMessage({ type: 'error', text: 'Ingrese un email de notificación para la prueba' });
      return;
    }
    setTesting(true);
    setMessage(null);
    try {
      await companiesApi.testSmtp({
        smtp_host: settings.smtp_host,
        smtp_port: Number(settings.smtp_port),
        smtp_user: settings.smtp_user,
        smtp_password: settings.smtp_password,
        from_email: settings.smtp_from_email,
        from_name: settings.smtp_from_name,
        test_email: settings.notification_email,
      });
      setMessage({ type: 'success', text: `Email de prueba enviado a ${settings.notification_email}` });
    } catch (err: any) {
      const detail = err?.response?.data?.detail || err?.message || 'Error al enviar email de prueba';
      setMessage({ type: 'error', text: detail });
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center py-12"><Loader size={24} className="animate-spin text-blue-500" /></div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Configuración del Sistema</h2>
      </div>

      <div className="card space-y-4 max-w-2xl">
        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
          <Mail size={18} className="text-blue-500" />
          Configuración SMTP del Sistema
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SMTP Host</label>
            <input value={settings?.smtp_host || ''} onChange={(e) => setSettings({...settings, smtp_host: e.target.value})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SMTP Puerto</label>
            <input type="number" value={settings?.smtp_port || ''} onChange={(e) => setSettings({...settings, smtp_port: e.target.value})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Usuario SMTP</label>
            <input value={settings?.smtp_user || ''} onChange={(e) => setSettings({...settings, smtp_user: e.target.value})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña SMTP</label>
            <input type="password" value={settings?.smtp_password || ''} onChange={(e) => setSettings({...settings, smtp_password: e.target.value})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email Remitente</label>
            <input value={settings?.smtp_from_email || ''} onChange={(e) => setSettings({...settings, smtp_from_email: e.target.value})} className="input-field" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre Remitente</label>
            <input value={settings?.smtp_from_name || ''} onChange={(e) => setSettings({...settings, smtp_from_name: e.target.value})} className="input-field" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Email de Notificaciones (Super Admin)</label>
          <input type="email" value={settings?.notification_email || ''} onChange={(e) => setSettings({...settings, notification_email: e.target.value})} className="input-field" placeholder="admin@ejemplo.com" />
          <p className="text-xs text-gray-400 mt-1">Se usará para recibir notificaciones de nuevas empresas registradas</p>
        </div>

        {message && (
          <div className={`flex items-center gap-2 px-4 py-3 rounded-lg text-sm ${
            message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
            {message.text}
          </div>
        )}

        <div className="flex gap-3 pt-2">
          <button onClick={handleSave} disabled={saving} className="btn-primary flex items-center gap-2">
            {saving ? <Loader size={16} className="animate-spin" /> : <Save size={16} />}
            {saving ? 'Guardando...' : 'Guardar Configuración'}
          </button>
          <button onClick={handleTest} disabled={testing} className="btn-secondary flex items-center gap-2">
            {testing ? <Loader size={16} className="animate-spin" /> : <Mail size={16} />}
            {testing ? 'Enviando...' : 'Probar Conexión SMTP'}
          </button>
        </div>
      </div>
    </div>
  );
}
