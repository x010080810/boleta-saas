import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { payrollApi, templatesApi } from '../../services/api';
import { Upload, FileSpreadsheet, AlertCircle, CheckCircle, Loader, Download, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { Company } from '../../types';

export default function PayrollUpload() {
  const { selectedCompany, companies, isSuperAdmin, selectCompany } = useAuth();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const uploadIdRef = useRef<string | null>(null);
  const companyIdRef = useRef<string | null>(null);
  const processedRef = useRef(false);
  const [activeCompany, setActiveCompany] = useState<Company | null>(selectedCompany);
  const [file, setFile] = useState<File | null>(null);
  const [tipo, setTipo] = useState('ordinaria');
  const [mes, setMes] = useState(new Date().getMonth() + 1);
  const [anio, setAnio] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [preview, setPreview] = useState<any>(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    setActiveCompany(selectedCompany);
    if (selectedCompany) companyIdRef.current = selectedCompany.id;
  }, [selectedCompany]);

  useEffect(() => {
    return () => {
      if (uploadIdRef.current && !processedRef.current && companyIdRef.current) {
        payrollApi.deletePending(companyIdRef.current, uploadIdRef.current).catch(() => {});
      }
    };
  }, []);

  const handleUpload = async () => {
    if (!file || !activeCompany) return;

    if (uploadIdRef.current && !processedRef.current) {
      try {
        await payrollApi.deletePending(activeCompany.id, uploadIdRef.current);
      } catch { /* ignore */ }
    }

    setLoading(true);
    setError('');
    setPreview(null);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tipo_planilla', tipo);
    formData.append('periodo_mes', String(mes));
    formData.append('periodo_ano', String(anio));
    try {
      const res = await payrollApi.upload(activeCompany.id, formData);
      uploadIdRef.current = res.data.upload_id;
      companyIdRef.current = activeCompany.id;
      processedRef.current = false;
      setResult(res.data);
      loadPreview(res.data.upload_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al subir archivo');
    } finally {
      setLoading(false);
    }
  };

  const loadPreview = async (uploadId: string) => {
    if (!activeCompany) return;
    const res = await payrollApi.preview(activeCompany.id, uploadId);
    setPreview(res.data);
  };

  const handleProcess = async () => {
    if (!activeCompany || !result) return;
    setProcessing(true);
    try {
      const res = await payrollApi.process(activeCompany.id, result.upload_id);
      processedRef.current = true;
      navigate(`/payroll/report/${activeCompany.id}/${result.upload_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al procesar');
    } finally {
      setProcessing(false);
    }
  };

  const downloadTemplate = async () => {
    const res = await templatesApi.downloadExcel();
    const url = URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = 'plantilla_boletas.xlsx';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h2 className="text-lg md:text-xl font-bold text-gray-900">Subir Planilla</h2>
          <p className="text-sm text-gray-500">Cargue su archivo Excel para generar las boletas de pago</p>
        </div>
        <button onClick={downloadTemplate} className="btn-secondary flex items-center justify-center gap-2 sm:w-auto">
          <Download size={16} />
          Descargar Plantilla
        </button>
      </div>

      {isSuperAdmin && (
        <div className="card mb-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-medium text-gray-700">Empresa / RUC:</label>
            <select
              value={activeCompany?.id || ''}
              onChange={(e) => {
                const c = companies.find((c: Company) => c.id === e.target.value);
                if (c) { setActiveCompany(c); selectCompany(c); }
              }}
              className="input-field max-w-md"
            >
              {companies.map((c: Company) => (
                <option key={c.id} value={c.id}>{c.name} - {c.ruc}</option>
              ))}
            </select>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card space-y-4">
          <h3 className="font-semibold text-gray-900">Datos de la Planilla</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Planilla</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="input-field">
              <option value="ordinaria">Ordinaria</option>
              <option value="gratificacion">Gratificación</option>
              <option value="excepcional">Excepcional</option>
              <option value="cts">CTS</option>
              <option value="vacaciones">Vacaciones</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Mes</label>
              <select value={mes} onChange={(e) => setMes(Number(e.target.value))} className="input-field">
                {Array.from({ length: 12 }, (_, i) => (
                  <option key={i + 1} value={i + 1}>
                    {['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'][i]}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Año</label>
              <input type="number" value={anio} onChange={(e) => setAnio(Number(e.target.value))} className="input-field" min={2020} max={2035} />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Archivo Excel</label>
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className="px-4 py-2 rounded-lg text-sm font-medium bg-blue-50 text-blue-700 hover:bg-blue-100 border-0 cursor-pointer"
              >
                Seleccionar archivo
              </button>
              <span className="text-sm text-gray-500">
                {file ? file.name : 'Ningún archivo seleccionado'}
              </span>
            </div>
            <input
              type="file"
              ref={fileRef}
              accept=".xls,.xlsx"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">
              <AlertCircle size={16} />
              {error}
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? <Loader size={16} className="animate-spin" /> : <Upload size={16} />}
            {loading ? 'Subiendo...' : 'Subir y Previsualizar'}
          </button>
        </div>

        {preview && (
          <div className="card space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Vista Previa</h3>
              <span className="text-xs font-mono bg-gray-100 px-2 py-1 rounded">{result?.ticket}</span>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 text-sm">
              <p><strong>Ticket:</strong> {result?.ticket}</p>
              <p><strong>Tipo:</strong> {preview.tipo_planilla}</p>
              <p><strong>Período:</strong> {preview.periodo}</p>
              <p><strong>Empleados detectados:</strong> {preview.total_empleados}</p>
            </div>

            <div className="overflow-y-auto max-h-64">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500 border-b text-xs">
                    <th className="pb-2">Doc.</th>
                    <th className="pb-2">Nombre</th>
                    <th className="pb-2">Email</th>
                    <th className="pb-2">Neto</th>
                    <th className="pb-2">¿Registrado?</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.empleados.map((emp: any, i: number) => (
                    <tr key={i} className="border-b text-xs">
                      <td className="py-2">{emp.numero_documento}</td>
                      <td className="py-2">{emp.nombre_completo}</td>
                      <td className="py-2 text-gray-400">{emp.email || '-'}</td>
                      <td className="py-2">S/ {emp.neto_pagar?.toFixed(2)}</td>
                      <td className="py-2">
                        {emp.registrado_en_maestro
                          ? <span className="badge-success">Sí</span>
                          : <span className="badge-warning">No</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              onClick={handleProcess}
              disabled={processing}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {processing ? <Loader size={16} className="animate-spin" /> : <CheckCircle size={16} />}
              {processing ? 'Procesando...' : 'Confirmar y Procesar'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
