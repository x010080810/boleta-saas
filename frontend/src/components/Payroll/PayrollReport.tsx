import { useEffect, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { payrollApi } from '../../services/api';
import { ArrowLeft, Download, Send, CheckCircle, AlertCircle, Clock, Ban, Loader, Play } from 'lucide-react';
import type { PaySlip } from '../../types';

export default function PayrollReport() {
  const { companyId, uploadId } = useParams();
  const { selectedCompany } = useAuth();
  const navigate = useNavigate();
  const [report, setReport] = useState<any>(null);
  const [boletas, setBoletas] = useState<PaySlip[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [resending, setResending] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploadFailed, setUploadFailed] = useState(false);
  const [uploadPending, setUploadPending] = useState(false);
  const [processingPending, setProcessingPending] = useState(false);
  const pollingRef = useRef<ReturnType<typeof setInterval>>();

  const cid = companyId || selectedCompany?.id;

  useEffect(() => {
    if (!cid || !uploadId) return;
    Promise.all([
      payrollApi.report(cid, uploadId),
      payrollApi.boletas(cid, uploadId),
      payrollApi.status(cid, uploadId),
    ]).then(([rep, bol, st]) => {
      setReport(rep.data);
      setBoletas(bol.data);
      if (st.data.estado === 'processing') setProcessing(true);
      if (st.data.estado === 'failed') setUploadFailed(true);
      if (st.data.estado === 'pending') setUploadPending(true);
    }).catch((err) => {
      setError(err.response?.data?.detail || 'Error al cargar reporte');
      console.error(err);
    });
  }, [cid, uploadId]);

  useEffect(() => {
    if (!processing || !cid || !uploadId) return;

    pollingRef.current = setInterval(async () => {
      try {
        const res = await payrollApi.status(cid, uploadId);
        if (res.data.estado !== 'processing') {
          const [rep, bol] = await Promise.all([
            payrollApi.report(cid, uploadId),
            payrollApi.boletas(cid, uploadId),
          ]);
          setReport(rep.data);
          setBoletas(bol.data);
          setProcessing(false);
          if (res.data.estado === 'failed') setUploadFailed(true);
          clearInterval(pollingRef.current);
        }
      } catch {
        clearInterval(pollingRef.current);
        setProcessing(false);
      }
    }, 3000);

    return () => clearInterval(pollingRef.current);
  }, [processing, cid, uploadId]);

  const toggleSelect = (id: string) => {
    setSelected((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]);
  };

  const selectAll = () => {
    if (selected.length === boletas.length) {
      setSelected([]);
    } else {
      setSelected(boletas.map((b) => b.id));
    }
  };

  const handleResend = async () => {
    if (!cid || !uploadId || selected.length === 0) return;
    setResending(true);
    try {
      const res = await payrollApi.resend(cid, uploadId, {
        pay_slip_ids: selected,
        tipo: 'selected',
      });
      setMessage({ type: 'success', text: `Re-enviadas: ${res.data.enviados}` });
      const resB = await payrollApi.boletas(cid, uploadId);
      setBoletas(resB.data);
      setSelected([]);
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Error al re-enviar' });
      setTimeout(() => setMessage(null), 4000);
    } finally {
      setResending(false);
    }
  };

  const handleProcessPending = async () => {
    if (!cid || !uploadId) return;
    setProcessingPending(true);
    try {
      const res = await payrollApi.process(cid, uploadId);
      setUploadPending(false);
      setProcessing(true);
      setMessage({ type: 'success', text: res.data.message || 'Procesamiento iniciado' });
      setTimeout(() => setMessage(null), 4000);
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Error al iniciar procesamiento' });
      setTimeout(() => setMessage(null), 4000);
    } finally {
      setProcessingPending(false);
    }
  };

  const handleDownload = async (boletaId: string) => {
    if (!cid) return;
    const res = await payrollApi.download(cid, boletaId);
    const url = URL.createObjectURL(new Blob([res.data]));
    const a = document.createElement('a');
    a.href = url;
    a.download = `boleta_${boletaId.slice(0, 8)}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const estadoIcon = (estado: string) => {
    switch (estado) {
      case 'enviado': return <CheckCircle size={14} className="text-green-500" />;
      case 'fallido': return <AlertCircle size={14} className="text-red-500" />;
      case 'no_enviado_sin_saldo': return <Ban size={14} className="text-red-400" />;
      default: return <Clock size={14} className="text-yellow-500" />;
    }
  };

  const estadoText = (estado: string) => {
    switch (estado) {
      case 'enviado': return 'Enviado';
      case 'fallido': return 'Fallido';
      case 'no_enviado_sin_saldo': return 'Sin saldo';
      default: return 'No enviado';
    }
  };

  if (error) return (
    <div className="text-center py-20">
      <p className="text-red-500 font-medium mb-2">{error}</p>
      <Link to="/payroll/history" className="text-blue-600 hover:underline text-sm">Volver al historial</Link>
    </div>
  );

  if (!report) return <div className="text-center py-20 text-gray-400">Cargando reporte...</div>;

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-4">
          <Link to="/payroll/history" className="p-2 hover:bg-gray-100 rounded-lg shrink-0">
            <ArrowLeft size={20} />
          </Link>
          <div className="min-w-0">
            <h2 className="text-lg md:text-xl font-bold text-gray-900">Reporte de Procesamiento</h2>
            <p className="text-sm text-gray-500 font-mono truncate">{report.ticket}</p>
            {processing && (
              <p className="text-xs text-blue-600 mt-1 flex items-center gap-1">
                <Loader size={12} className="animate-spin" />
                Procesando... actualizando automáticamente
              </p>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {selected.length > 0 && (
            <button onClick={handleResend} disabled={resending} className="btn-primary flex items-center gap-2 w-full sm:w-auto justify-center">
              <Send size={16} />
              Re-enviar ({selected.length})
            </button>
          )}
        </div>
      </div>

      {uploadPending && (
        <div className="mb-6 px-4 py-3 rounded-xl text-sm bg-yellow-50 text-yellow-700 border border-yellow-200">
          <div className="flex items-center gap-2">
            <Clock size={16} />
            <span className="flex-1">Esta carga está pendiente de procesamiento.</span>
            <button
              onClick={handleProcessPending}
              disabled={processingPending}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-yellow-100 text-yellow-800 hover:bg-yellow-200 disabled:opacity-50"
            >
              {processingPending ? <Loader size={14} className="animate-spin" /> : <Play size={14} />}
              {processingPending ? 'Procesando...' : 'Procesar ahora'}
            </button>
          </div>
        </div>
      )}
      {uploadFailed && (
        <div className="mb-6 px-4 py-3 rounded-xl text-sm flex items-center gap-2 bg-red-50 text-red-700 border border-red-200">
          <AlertCircle size={16} />
          Esta carga finalizó con errores. Es posible que no se hayan generado todas las boletas.
        </div>
      )}

      {message && (
        <div className={`mb-6 px-4 py-3 rounded-xl text-sm flex items-center gap-2 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
          {message.type === 'success' ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
          {message.text}
        </div>
      )}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
        {[
          { label: 'Registros', value: report.resumen?.total_registros || 0, color: 'text-blue-600 bg-blue-50' },
          { label: 'Procesados', value: report.resumen?.total_procesados || 0, color: 'text-green-600 bg-green-50' },
          { label: 'Observaciones', value: report.resumen?.total_observaciones || 0, color: 'text-yellow-600 bg-yellow-50' },
          { label: 'Enviados', value: report.resumen?.total_enviados || 0, color: 'text-green-600 bg-green-50' },
          { label: 'Fallidos', value: report.resumen?.total_fallidos || 0, color: 'text-red-600 bg-red-50' },
          { label: 'Sin saldo', value: report.resumen?.total_sin_saldo || 0, color: 'text-orange-600 bg-orange-50' },
        ].map((stat) => (
          <div key={stat.label} className="card text-center py-4">
            <p className={`text-2xl font-bold ${stat.color.split(' ')[0]}`}>{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {report.observaciones?.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
          <h4 className="font-medium text-yellow-800 mb-2">Observaciones ({report.observaciones.length})</h4>
          <ul className="space-y-1">
            {report.observaciones.map((obs: any, i: number) => (
              <li key={i} className="text-sm text-yellow-700 flex items-start gap-2">
                <AlertCircle size={14} className="mt-0.5 shrink-0" />
                <span><strong>{obs.nombre}</strong> - {obs.motivo} → {obs.accion}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            checked={selected.length === boletas.length && boletas.length > 0}
            onChange={selectAll}
            className="rounded border-gray-300"
          />
          <span className="text-sm font-medium">Seleccionar todo</span>
          <span className="text-xs text-gray-400">({boletas.length} registros)</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b text-xs">
                <th className="pb-3 w-8"></th>
                <th className="pb-3 font-medium">Documento</th>
                <th className="pb-3 font-medium">Nombre</th>
                <th className="pb-3 font-medium">Ingresos</th>
                <th className="pb-3 font-medium">Descuentos</th>
                <th className="pb-3 font-medium">Neto</th>
                <th className="pb-3 font-medium">Envío</th>
                <th className="pb-3 font-medium">PDF</th>
              </tr>
            </thead>
            <tbody>
              {boletas.map((b) => (
                <tr key={b.id} className={`border-b hover:bg-gray-50 ${b.es_observacion ? 'bg-yellow-50/50' : ''}`}>
                  <td className="py-2">
                    <input
                      type="checkbox"
                      checked={selected.includes(b.id)}
                      onChange={() => toggleSelect(b.id)}
                      className="rounded border-gray-300"
                    />
                  </td>
                  <td className="py-2 font-mono text-xs">{b.numero_documento}</td>
                  <td className="py-2">
                    <span className={b.es_observacion ? 'text-yellow-700' : ''}>
                      {b.nombre_completo}
                    </span>
                    {b.es_observacion && (
                      <span className="badge-warning ml-1 text-[10px]">Obs</span>
                    )}
                  </td>
                  <td className="py-2">S/ {b.total_ingresos.toFixed(2)}</td>
                  <td className="py-2">S/ {b.total_descuentos.toFixed(2)}</td>
                  <td className="py-2 font-medium">S/ {b.neto_pagar.toFixed(2)}</td>
                  <td className="py-2">
                    <div className="flex items-center gap-1">
                      {estadoIcon(b.estado_envio)}
                      <span className="text-xs">{estadoText(b.estado_envio)}</span>
                    </div>
                    {b.email_destino && (
                      <p className="text-[10px] text-gray-500 mt-0.5 truncate max-w-[180px]" title={b.email_destino}>
                        {b.email_destino}
                      </p>
                    )}
                    {b.error_message && (
                      <p className="text-[10px] text-red-400 mt-0.5 truncate max-w-[180px]" title={b.error_message}>
                        {b.error_message}
                      </p>
                    )}
                  </td>
                  <td className="py-2">
                    <button
                      onClick={() => handleDownload(b.id)}
                      className="p-1.5 text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="Descargar PDF"
                    >
                      <Download size={14} />
                    </button>
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
