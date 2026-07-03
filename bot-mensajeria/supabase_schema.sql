-- ============================================
-- CurrierMsj - Schema de Supabase
-- Ruta principal: Estados Unidos -> Ecuador
-- Ejecutar en SQL Editor de Supabase
-- ============================================

-- Tabla principal de envios
CREATE TABLE IF NOT EXISTS envios (
    id SERIAL PRIMARY KEY,
    tracking_code TEXT UNIQUE,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    remitente TEXT,
    telefono_remitente TEXT,
    destinatario TEXT,
    telefono_destinatario TEXT,
    direccion_origen TEXT,
    direccion_destino TEXT,
    tipo_paquete TEXT,
    peso TEXT,
    dimensiones TEXT,
    servicio_envio TEXT,
    valor_cotizado NUMERIC(10,2),
    entrega_estimada TEXT,
    imagen_url TEXT,
    fecha_envio TEXT,
    hora_envio TEXT,
    instrucciones TEXT,
    chat_id INTEGER DEFAULT 0,
    phone_number TEXT,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE envios ADD COLUMN IF NOT EXISTS phone_number TEXT;

-- Compatibilidad si la tabla envios ya existia
ALTER TABLE envios ADD COLUMN IF NOT EXISTS tracking_code TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'pendiente';
ALTER TABLE envios ADD COLUMN IF NOT EXISTS remitente TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS telefono_remitente TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS destinatario TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS telefono_destinatario TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS direccion_origen TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS direccion_destino TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS tipo_paquete TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS peso TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS dimensiones TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS servicio_envio TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS valor_cotizado NUMERIC(10,2);
ALTER TABLE envios ADD COLUMN IF NOT EXISTS costo_producto NUMERIC(10,2) DEFAULT 0;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS entrega_estimada TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS imagen_url TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS fecha_envio TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS hora_envio TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS instrucciones TEXT;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS chat_id INTEGER DEFAULT 0;
ALTER TABLE envios ADD COLUMN IF NOT EXISTS creado_en TIMESTAMPTZ DEFAULT NOW();

-- Tabla de clientes registrados
CREATE TABLE IF NOT EXISTS clientes (
    phone_number TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellido TEXT,
    ciudad TEXT,
    telefono_contacto TEXT,
    registrado_en TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de estado por usuario (reemplaza ConversationHandler de Telegram)
CREATE TABLE IF NOT EXISTS estado_usuario (
    phone_number TEXT PRIMARY KEY,
    paso_actual TEXT NOT NULL DEFAULT 'menu',
    datos_temp JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabla de FAQ para respuestas automaticas
CREATE TABLE IF NOT EXISTS faq (
    id SERIAL PRIMARY KEY,
    pregunta TEXT NOT NULL,
    respuesta TEXT NOT NULL,
    categoria TEXT DEFAULT 'general'
);

CREATE UNIQUE INDEX IF NOT EXISTS faq_pregunta_unique ON faq (pregunta);

-- Tabla de reportes de problemas
CREATE TABLE IF NOT EXISTS reportes (
    id SERIAL PRIMARY KEY,
    phone_number TEXT NOT NULL,
    tracking_code TEXT,
    categoria TEXT,
    descripcion TEXT NOT NULL,
    estado TEXT DEFAULT 'abierto',
    agente_asignado TEXT DEFAULT 'Equipo soporte',
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE reportes ADD COLUMN IF NOT EXISTS tracking_code TEXT;
ALTER TABLE reportes ADD COLUMN IF NOT EXISTS categoria TEXT;
ALTER TABLE reportes ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'abierto';
ALTER TABLE reportes ADD COLUMN IF NOT EXISTS agente_asignado TEXT DEFAULT 'Equipo soporte';

-- Finanzas del dueno: caja, gastos, planilla y margenes
CREATE TABLE IF NOT EXISTS movimientos_financieros (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'egreso')),
    categoria TEXT NOT NULL,
    descripcion TEXT,
    monto NUMERIC(10,2) NOT NULL DEFAULT 0,
    tipo_gasto TEXT CHECK (tipo_gasto IN ('fijo', 'variable')),
    fecha TIMESTAMPTZ DEFAULT NOW(),
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planilla_personal (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    cargo TEXT,
    sueldo NUMERIC(10,2) NOT NULL DEFAULT 0,
    fecha_pago TIMESTAMPTZ,
    descuentos NUMERIC(10,2) DEFAULT 0,
    estado_pago TEXT DEFAULT 'pendiente',
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS margenes_producto (
    id SERIAL PRIMARY KEY,
    producto TEXT NOT NULL,
    categoria TEXT,
    precio_venta NUMERIC(10,2) NOT NULL DEFAULT 0,
    costo_producto NUMERIC(10,2) NOT NULL DEFAULT 0,
    unidades INTEGER DEFAULT 1,
    creado_en TIMESTAMPTZ DEFAULT NOW()
);

-- Funcion para generar tracking code automatico
CREATE OR REPLACE FUNCTION generar_tracking_code()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.tracking_code IS NULL OR NEW.tracking_code = '' THEN
        NEW.tracking_code := 'CUR-' || LPAD(NEW.id::TEXT, 5, '0');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para auto-generar tracking_code antes de insertar
DROP TRIGGER IF EXISTS trg_tracking ON envios;
CREATE TRIGGER trg_tracking
    BEFORE INSERT ON envios
    FOR EACH ROW
    EXECUTE FUNCTION generar_tracking_code();

-- Completar tracking_code en datos antiguos si estan vacios
UPDATE envios
SET tracking_code = 'CUR-' || LPAD(id::TEXT, 5, '0')
WHERE tracking_code IS NULL OR tracking_code = '';

CREATE UNIQUE INDEX IF NOT EXISTS envios_tracking_code_unique
    ON envios (tracking_code)
    WHERE tracking_code IS NOT NULL AND tracking_code <> '';

-- Habilitar RLS (Row Level Security)
ALTER TABLE envios ENABLE ROW LEVEL SECURITY;
ALTER TABLE estado_usuario ENABLE ROW LEVEL SECURITY;
ALTER TABLE faq ENABLE ROW LEVEL SECURITY;
ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimientos_financieros ENABLE ROW LEVEL SECURITY;
ALTER TABLE planilla_personal ENABLE ROW LEVEL SECURITY;
ALTER TABLE margenes_producto ENABLE ROW LEVEL SECURITY;

-- Politicas de acceso.
-- El backend Flask debe usar service_role key, no anon key.
DROP POLICY IF EXISTS "Service role acceso total envios" ON envios;
CREATE POLICY "Service role acceso total envios" ON envios
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total estado_usuario" ON estado_usuario;
CREATE POLICY "Service role acceso total estado_usuario" ON estado_usuario
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total faq" ON faq;
CREATE POLICY "Service role acceso total faq" ON faq
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Anon lectura faq" ON faq;
CREATE POLICY "Anon lectura faq" ON faq
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Service role acceso total reportes" ON reportes;
CREATE POLICY "Service role acceso total reportes" ON reportes
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total movimientos_financieros" ON movimientos_financieros;
CREATE POLICY "Service role acceso total movimientos_financieros" ON movimientos_financieros
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total planilla_personal" ON planilla_personal;
CREATE POLICY "Service role acceso total planilla_personal" ON planilla_personal
    FOR ALL USING (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total margenes_producto" ON margenes_producto;
CREATE POLICY "Service role acceso total margenes_producto" ON margenes_producto
    FOR ALL USING (auth.role() = 'service_role');

ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role acceso total clientes" ON clientes;
CREATE POLICY "Service role acceso total clientes" ON clientes
    FOR ALL USING (auth.role() = 'service_role');

-- Llaves foraneas
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_envios_phone'
    ) THEN
        ALTER TABLE envios ADD CONSTRAINT fk_envios_phone
            FOREIGN KEY (phone_number) REFERENCES clientes(phone_number)
            ON DELETE SET NULL ON UPDATE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_reportes_phone'
    ) THEN
        ALTER TABLE reportes ADD CONSTRAINT fk_reportes_phone
            FOREIGN KEY (phone_number) REFERENCES clientes(phone_number)
            ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_reportes_tracking'
    ) THEN
        ALTER TABLE reportes ADD CONSTRAINT fk_reportes_tracking
            FOREIGN KEY (tracking_code) REFERENCES envios(tracking_code)
            ON DELETE SET NULL ON UPDATE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_estado_usuario_phone'
    ) THEN
        ALTER TABLE estado_usuario ADD CONSTRAINT fk_estado_usuario_phone
            FOREIGN KEY (phone_number) REFERENCES clientes(phone_number)
            ON DELETE CASCADE ON UPDATE CASCADE;
    END IF;
END $$;

-- Datos iniciales de FAQ
INSERT INTO faq (pregunta, respuesta, categoria) VALUES
    ('horario', 'Nuestro horario de atencion es de Lunes a Sabado de 8:00 a 18:00.', 'general'),
    ('costo', 'El costo depende del peso y la ruta. Usa la opcion Cotizar envio para obtener un estimado.', 'envios'),
    ('tiempo entrega', 'El tiempo estimado EE.UU. a Ecuador depende del servicio y aduana.', 'envios'),
    ('formas pago', 'Aceptamos efectivo, transferencia bancaria y pago acordado con el agente.', 'pagos'),
    ('cobertura', 'La ruta principal del servicio es Estados Unidos hacia Ecuador.', 'general'),
    ('abono', 'Puedes coordinar abono o pago completo con el agente antes del envio.', 'pagos')
ON CONFLICT (pregunta) DO UPDATE SET
    respuesta = EXCLUDED.respuesta,
    categoria = EXCLUDED.categoria;
