export interface User {
  id: string;
  email: string;
  full_name: string;
  type: 'company_user' | 'super_admin';
}

export interface Company {
  id: string;
  name: string;
  ruc: string;
  plan_envios_mes: number;
  licencia_estado: string;
  licencia_fin: string | null;
  is_active: boolean;
  logo_url?: string;
  licencia_inicio?: string;
  licencia_grace_hasta?: string;
  smtp_host?: string;
  smtp_port?: number;
  smtp_from_email?: string;
  smtp_from_name?: string;
  admins?: any[];
}

export interface Employee {
  id: string;
  tipo_documento: string;
  numero_documento: string;
  nombre_completo: string;
  email: string | null;
  cargo: string | null;
  fecha_ingreso: string | null;
}

export interface PayrollUpload {
  id: string;
  ticket_number: string;
  tipo_planilla: string;
  periodo: string;
  filename: string;
  total_registros: number;
  total_procesados: number;
  total_observaciones: number;
  total_enviados: number;
  total_fallidos: number;
  total_sin_saldo: number;
  estado: string;
  created_at: string;
}

export interface PaySlip {
  id: string;
  tipo_documento: string;
  numero_documento: string;
  nombre_completo: string;
  email_destino: string;
  total_ingresos: number;
  total_descuentos: number;
  neto_pagar: number;
  es_observacion: boolean;
  motivo_observacion: string | null;
  estado_envio: string;
  error_message: string | null;
  enviado_en: string | null;
}

export interface QuotaStatus {
  mes: number;
  anio: number;
  limite: number;
  utilizados: number;
  disponibles: number;
}
