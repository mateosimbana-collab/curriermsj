-- Tablas financieras opcionales para el dashboard historico del dueno.
-- Es idempotente y puede aplicarse antes o despues del preflight 000.

CREATE TABLE IF NOT EXISTS movimientos_financieros (
    id SERIAL PRIMARY KEY,
    tipo TEXT NOT NULL CHECK (tipo IN ('ingreso', 'egreso')),
    categoria TEXT NOT NULL,
    descripcion TEXT,
    monto NUMERIC(10,2) NOT NULL CHECK (monto > 0),
    tipo_gasto TEXT CHECK (tipo_gasto IN ('fijo', 'variable')),
    fecha TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (tipo = 'ingreso' OR tipo_gasto IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS planilla_personal (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    cargo TEXT,
    sueldo NUMERIC(10,2) NOT NULL CHECK (sueldo > 0),
    fecha_pago TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    descuentos NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (descuentos >= 0 AND descuentos <= sueldo),
    estado_pago TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado_pago IN ('pendiente', 'pagado')),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS margenes_producto (
    id SERIAL PRIMARY KEY,
    producto TEXT NOT NULL,
    categoria TEXT,
    precio_venta NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (precio_venta >= 0),
    costo_producto NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (costo_producto >= 0),
    unidades INTEGER NOT NULL DEFAULT 1 CHECK (unidades > 0),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_movimientos_financieros_fecha
    ON movimientos_financieros (fecha DESC);
CREATE INDEX IF NOT EXISTS idx_planilla_personal_fecha_pago
    ON planilla_personal (fecha_pago DESC);
CREATE INDEX IF NOT EXISTS idx_margenes_producto_categoria
    ON margenes_producto (categoria);

ALTER TABLE movimientos_financieros ENABLE ROW LEVEL SECURITY;
ALTER TABLE planilla_personal ENABLE ROW LEVEL SECURITY;
ALTER TABLE margenes_producto ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role acceso total movimientos_financieros" ON movimientos_financieros;
CREATE POLICY "Service role acceso total movimientos_financieros" ON movimientos_financieros
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total planilla_personal" ON planilla_personal;
CREATE POLICY "Service role acceso total planilla_personal" ON planilla_personal
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role acceso total margenes_producto" ON margenes_producto;
CREATE POLICY "Service role acceso total margenes_producto" ON margenes_producto
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
