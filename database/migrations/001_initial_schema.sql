-- ============================================
-- CurrierMsj - Schema Completo v2.0
-- Sistema de Gestion Courier
-- ============================================

-- EXTENSIONES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- TABLAS BASE
-- ============================================

-- 1. USUARIOS DEL SISTEMA (admin, agentes, operadores)
CREATE TABLE IF NOT EXISTS usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    telefono TEXT,
    rol TEXT NOT NULL DEFAULT 'agente' CHECK (rol IN ('admin', 'supervisor', 'agente', 'soporte')),
    activo BOOLEAN DEFAULT true,
    ultimo_acceso TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 2. CLIENTES (personas naturales que reciben/envian paquetes)
CREATE TABLE IF NOT EXISTS clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cedula TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    telefono TEXT NOT NULL,
    telefono_alternativo TEXT,
    email TEXT,
    direccion TEXT,
    ciudad TEXT DEFAULT 'Guayaquil',
    pais TEXT DEFAULT 'Ecuador',
    tipo_cliente TEXT DEFAULT 'regular' CHECK (tipo_cliente IN ('regular', 'grupo', 'mayorista')),
    grupo_id UUID REFERENCES grupos_clientes(id),
    mayorista_id UUID REFERENCES mayoristas(id),
    notas TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(cedula, deleted_at)
);

-- 3. GRUPOS DE CLIENTES
CREATE TABLE IF NOT EXISTS grupos_clientes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    descripcion TEXT,
    responsable_telefono TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 4. CLIENTES MAYORISTAS
CREATE TABLE IF NOT EXISTS mayoristas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre_empresa TEXT NOT NULL,
    ruc TEXT,
    contacto_nombre TEXT NOT NULL,
    contacto_telefono TEXT NOT NULL,
    contacto_email TEXT,
    telefono_oficina TEXT,
    condiciones_pago TEXT,
    credito_asignado NUMERIC(10,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 5. PROSPECTOS (leads de WhatsApp)
CREATE TABLE IF NOT EXISTS prospectos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telefono TEXT NOT NULL,
    nombre TEXT,
    origen TEXT DEFAULT 'whatsapp',
    ultimo_mensaje TEXT,
    paso_actual TEXT DEFAULT 'nuevo',
    estado TEXT DEFAULT 'activo' CHECK (estado IN ('activo', 'convertido', 'perdido')),
    cliente_convertido_id UUID REFERENCES clientes(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. PAQUETES
CREATE TABLE IF NOT EXISTS paquetes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_code TEXT UNIQUE,
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    grupo_id UUID REFERENCES grupos_clientes(id),
    remitente_nombre TEXT NOT NULL,
    remitente_direccion TEXT,
    remitente_telefono TEXT,
    remitente_pais TEXT DEFAULT 'Estados Unidos',
    destinatario_nombre TEXT NOT NULL,
    destinatario_telefono TEXT,
    destinatario_direccion TEXT NOT NULL,
    destinatario_ciudad TEXT,
    tipo_paquete TEXT,
    peso_kg NUMERIC(8,2),
    dimensiones TEXT,
    contenido TEXT,
    valor_declarado NUMERIC(10,2) DEFAULT 0,
    valor_flete NUMERIC(10,2),
    servicio_envio TEXT,
    estado_actual TEXT NOT NULL DEFAULT 'recibido',
    etiqueta_actual TEXT,
    usuario_asignado_id UUID REFERENCES usuarios(id),
    fecha_recepcion TIMESTAMPTZ DEFAULT NOW(),
    fecha_despacho TIMESTAMPTZ,
    fecha_entrega TIMESTAMPTZ,
    imagen_url TEXT,
    notas_internas TEXT,
    requiere_aprobacion BOOLEAN DEFAULT false,
    aprobado_por UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_paquetes_tracking ON paquetes(tracking_code) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_paquetes_cliente ON paquetes(cliente_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_paquetes_estado ON paquetes(estado_actual) WHERE deleted_at IS NULL;

-- 7. ESTADOS / ETIQUETAS
CREATE TABLE IF NOT EXISTS etiquetas_estado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    color TEXT DEFAULT '#3b82f6',
    posicion INT DEFAULT 0,
    es_final BOOLEAN DEFAULT false,
    notificar_cliente BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- 8. HISTORIAL DE TRACKING
CREATE TABLE IF NOT EXISTS tracking_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paquete_id UUID NOT NULL REFERENCES paquetes(id),
    etiqueta TEXT NOT NULL,
    descripcion TEXT,
    ubicacion TEXT,
    foto_url TEXT,
    usuario_id UUID REFERENCES usuarios(id),
    es_automatico BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tracking_paquete ON tracking_events(paquete_id);
CREATE INDEX IF NOT EXISTS idx_tracking_fecha ON tracking_events(created_at DESC);

-- 9. IMAGENES DE PAQUETES
CREATE TABLE IF NOT EXISTS imagenes_paquete (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paquete_id UUID NOT NULL REFERENCES paquetes(id),
    url TEXT NOT NULL,
    tipo TEXT DEFAULT 'foto' CHECK (tipo IN ('foto', 'documento', 'firma')),
    descripcion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 10. NOTIFICACIONES
CREATE TABLE IF NOT EXISTS notificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paquete_id UUID REFERENCES paquetes(id),
    cliente_id UUID REFERENCES clientes(id),
    telefono_destino TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('tracking', 'alerta', 'promocion', 'recordatorio')),
    mensaje TEXT NOT NULL,
    estado_envio TEXT DEFAULT 'pendiente' CHECK (estado_envio IN ('pendiente', 'enviado', 'fallido', 'leido')),
    whatsapp_msg_id TEXT,
    error_msg TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    sent_at TIMESTAMPTZ
);

-- 11. AUDITORIA
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tabla TEXT NOT NULL,
    registro_id UUID,
    accion TEXT NOT NULL CHECK (accion IN ('CREATE', 'UPDATE', 'DELETE', 'RESTORE')),
    usuario_id UUID REFERENCES usuarios(id),
    valores_anteriores JSONB,
    valores_nuevos JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tabla ON audit_log(tabla, registro_id);
CREATE INDEX IF NOT EXISTS idx_audit_fecha ON audit_log(created_at DESC);

-- 12. CONFIGURACION DEL SISTEMA
CREATE TABLE IF NOT EXISTS configuracion (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clave TEXT UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    tipo TEXT DEFAULT 'texto' CHECK (tipo IN ('texto', 'numero', 'booleano', 'json')),
    descripcion TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 13. SESIONES WHATSAPP (para estado del bot)
CREATE TABLE IF NOT EXISTS sesiones_whatsapp (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telefono TEXT NOT NULL,
    cliente_id UUID REFERENCES clientes(id),
    paso_actual TEXT DEFAULT 'menu',
    datos_temp JSONB DEFAULT '{}',
    ultimo_mensaje TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sesiones_telefono ON sesiones_whatsapp(telefono);

-- 14. REPORTES GENERADOS
CREATE TABLE IF NOT EXISTS reportes_generados (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tipo TEXT NOT NULL CHECK (tipo IN ('clientes', 'paquetes', 'ingresos', 'tracking', 'personalizado')),
    formato TEXT DEFAULT 'csv' CHECK (formato IN ('csv', 'xlsx', 'pdf')),
    filtros JSONB,
    url_descarga TEXT,
    usuario_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- FUNCIONES Y TRIGGERS
-- ============================================

-- Auto-generar tracking code
CREATE OR REPLACE FUNCTION generar_tracking_code()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tracking_code IS NULL OR NEW.tracking_code = '' THEN
        NEW.tracking_code := 'CUR-' || LPAD(nextval('paquetes_seq'::regclass)::TEXT, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE SEQUENCE IF NOT EXISTS paquetes_seq START 1000;

DROP TRIGGER IF EXISTS trg_paquetes_tracking ON paquetes;
CREATE TRIGGER trg_paquetes_tracking
    BEFORE INSERT ON paquetes
    FOR EACH ROW EXECUTE FUNCTION generar_tracking_code();

-- Auditoria automatica
CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
DECLARE
    _usuario_id UUID;
BEGIN
    _usuario_id := current_setting('app.usuario_id', true)::UUID;
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, usuario_id, valores_anteriores)
        VALUES (TG_TABLE_NAME, OLD.id, 'DELETE', _usuario_id, row_to_json(OLD)::jsonb);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, usuario_id, valores_anteriores, valores_nuevos)
        VALUES (TG_TABLE_NAME, NEW.id, 'UPDATE', _usuario_id, row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (tabla, registro_id, accion, usuario_id, valores_nuevos)
        VALUES (TG_TABLE_NAME, NEW.id, 'CREATE', _usuario_id, row_to_json(NEW)::jsonb);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger de auditoria para tablas principales
CREATE TRIGGER trg_audit_paquetes AFTER INSERT OR UPDATE OR DELETE ON paquetes
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();
CREATE TRIGGER trg_audit_clientes AFTER INSERT OR UPDATE OR DELETE ON clientes
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

-- ============================================
-- SEEDS: CONFIGURACION INICIAL
-- ============================================

INSERT INTO configuracion (clave, valor, tipo, descripcion) VALUES
    ('business_name', 'CurrierMsj', 'texto', 'Nombre del negocio'),
    ('bot_name', 'Rex', 'texto', 'Nombre del asistente virtual'),
    ('route_label', 'EE.UU. -> Ecuador', 'texto', 'Ruta principal'),
    ('support_hours', 'Lunes a Sabado 8:00-18:00', 'texto', 'Horario de atencion'),
    ('whatsapp_phone_id', '1238571072668582', 'texto', 'ID del telefono de WhatsApp'),
    ('whatsapp_waba_id', '1768778814289159', 'texto', 'ID de WABA'),
    ('max_notifications_per_hour', '20', 'numero', 'Limite de notificaciones por hora'),
    ('require_approval_for_dispatch', 'true', 'booleano', 'Requiere aprobacion para despachar')
ON CONFLICT (clave) DO NOTHING;

INSERT INTO etiquetas_estado (nombre, descripcion, color, posicion, notificar_cliente) VALUES
    ('Recibido en USA', 'Paquete recibido en bodega USA', '#3b82f6', 1, true),
    ('En transito', 'En camino a Ecuador', '#f59e0b', 2, true),
    ('En aduana', 'En proceso aduanero', '#8b5cf6', 3, true),
    ('En destino', 'En bodega Ecuador', '#06b6d4', 4, true),
    ('En ruta de entrega', 'Repartidor en camino', '#22c55e', 5, true),
    ('Entregado', 'Entregado al destinatario', '#16a34a', 6, true),
    ('Devuelto', 'Devuelto al remitente', '#ef4444', 7, true),
    ('Retenido', 'Retenido por agente', '#dc2626', 8, false)
ON CONFLICT (nombre) DO NOTHING;

-- ============================================
-- RLS (Row Level Security)
-- ============================================
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE paquetes ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracking_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Políticas: solo service_role (backend) tiene acceso total
CREATE POLICY "Service role full access" ON usuarios FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON clientes FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON paquetes FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON tracking_events FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role full access" ON audit_log FOR ALL USING (auth.role() = 'service_role');
