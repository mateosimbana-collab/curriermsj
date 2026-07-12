-- Apply this migration to databases created before 001 was hardened.

CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_cedula_activa
    ON clientes(cedula) WHERE deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_clientes_telefono_activo
    ON clientes(telefono) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS reportes (
    id BIGSERIAL PRIMARY KEY,
    cliente_id UUID REFERENCES clientes(id),
    paquete_id UUID REFERENCES paquetes(id),
    telefono_contacto TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    categoria TEXT,
    estado TEXT NOT NULL DEFAULT 'abierto'
        CHECK (estado IN ('abierto', 'en_proceso', 'resuelto', 'cerrado')),
    agente_asignado_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_reportes_cliente ON reportes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_reportes_estado ON reportes(estado, created_at DESC);

CREATE TABLE IF NOT EXISTS faq (
    id BIGSERIAL PRIMARY KEY,
    pregunta TEXT UNIQUE NOT NULL,
    respuesta TEXT NOT NULL,
    categoria TEXT NOT NULL DEFAULT 'general',
    activo BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO faq (pregunta, respuesta, categoria) VALUES
    ('horario', 'Nuestro horario de atencion es de Lunes a Sabado de 8:00 a 18:00.', 'general'),
    ('costo', 'El costo depende del peso y la ruta. Solicita una cotizacion para obtener un estimado.', 'envios'),
    ('tiempo entrega', 'El tiempo estimado entre EE.UU. y Ecuador depende del servicio y aduana.', 'envios'),
    ('formas pago', 'Aceptamos los medios de pago coordinados con el agente.', 'pagos'),
    ('cobertura', 'La ruta principal del servicio es Estados Unidos hacia Ecuador.', 'general')
ON CONFLICT (pregunta) DO UPDATE SET
    respuesta = EXCLUDED.respuesta,
    categoria = EXCLUDED.categoria,
    updated_at = NOW();

ALTER TABLE grupos_clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE mayoristas ENABLE ROW LEVEL SECURITY;
ALTER TABLE prospectos ENABLE ROW LEVEL SECURITY;
ALTER TABLE etiquetas_estado ENABLE ROW LEVEL SECURITY;
ALTER TABLE imagenes_paquete ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificaciones ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracion ENABLE ROW LEVEL SECURITY;
ALTER TABLE sesiones_whatsapp ENABLE ROW LEVEL SECURITY;
ALTER TABLE reportes_generados ENABLE ROW LEVEL SECURITY;
ALTER TABLE reportes ENABLE ROW LEVEL SECURITY;
ALTER TABLE faq ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access" ON grupos_clientes;
CREATE POLICY "Service role full access" ON grupos_clientes FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON mayoristas;
CREATE POLICY "Service role full access" ON mayoristas FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON prospectos;
CREATE POLICY "Service role full access" ON prospectos FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON etiquetas_estado;
CREATE POLICY "Service role full access" ON etiquetas_estado FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON imagenes_paquete;
CREATE POLICY "Service role full access" ON imagenes_paquete FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON notificaciones;
CREATE POLICY "Service role full access" ON notificaciones FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON configuracion;
CREATE POLICY "Service role full access" ON configuracion FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON sesiones_whatsapp;
CREATE POLICY "Service role full access" ON sesiones_whatsapp FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON reportes_generados;
CREATE POLICY "Service role full access" ON reportes_generados FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON reportes;
CREATE POLICY "Service role full access" ON reportes FOR ALL USING (auth.role() = 'service_role');
DROP POLICY IF EXISTS "Service role full access" ON faq;
CREATE POLICY "Service role full access" ON faq FOR ALL USING (auth.role() = 'service_role');
