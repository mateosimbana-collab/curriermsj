-- Flujo operativo real: recepciones en USA, consolidacion y cobros.

CREATE TABLE IF NOT EXISTS recepciones_usa (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cliente_id UUID NOT NULL REFERENCES clientes(id),
    grupo_id UUID REFERENCES grupos_clientes(id),
    despacho_id UUID REFERENCES paquetes(id),
    tracking_externo TEXT NOT NULL,
    transportista TEXT,
    tienda TEXT,
    contenido TEXT,
    peso_kg NUMERIC(8,2) CHECK (peso_kg IS NULL OR peso_kg >= 0),
    foto_url TEXT,
    notas TEXT,
    estado_operativo TEXT NOT NULL DEFAULT 'por_procesar'
        CHECK (estado_operativo IN (
            'por_procesar',
            'fotos_enviadas',
            'esperando_decision',
            'despachar',
            'armado',
            'consolidado'
    )),
    recibido_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    fotos_enviadas_en TIMESTAMPTZ,
    created_by UUID REFERENCES usuarios(id),
    updated_by UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_recepciones_tracking_activo
    ON recepciones_usa (UPPER(tracking_externo))
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_recepciones_cliente
    ON recepciones_usa (cliente_id, recibido_en DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_recepciones_estado
    ON recepciones_usa (estado_operativo, recibido_en)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_recepciones_despacho
    ON recepciones_usa (despacho_id)
    WHERE despacho_id IS NOT NULL AND deleted_at IS NULL;

ALTER TABLE paquetes ADD COLUMN IF NOT EXISTS categoria_importacion TEXT;
ALTER TABLE paquetes ADD COLUMN IF NOT EXISTS modalidad_entrega TEXT;
ALTER TABLE paquetes ADD COLUMN IF NOT EXISTS estado_pago TEXT NOT NULL DEFAULT 'pendiente';
ALTER TABLE paquetes ADD COLUMN IF NOT EXISTS fecha_prometida DATE;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paquetes_categoria_importacion_check') THEN
        ALTER TABLE paquetes ADD CONSTRAINT paquetes_categoria_importacion_check
            CHECK (categoria_importacion IS NULL OR categoria_importacion IN ('B', 'C', 'G'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paquetes_modalidad_entrega_check') THEN
        ALTER TABLE paquetes ADD CONSTRAINT paquetes_modalidad_entrega_check
            CHECK (modalidad_entrega IS NULL OR modalidad_entrega IN ('retiro', 'domicilio'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paquetes_estado_pago_check') THEN
        ALTER TABLE paquetes ADD CONSTRAINT paquetes_estado_pago_check
            CHECK (estado_pago IN ('pendiente', 'abono', 'pagado'));
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'paquetes_valor_flete_nonnegative') THEN
        ALTER TABLE paquetes ADD CONSTRAINT paquetes_valor_flete_nonnegative
            CHECK (valor_flete IS NULL OR valor_flete >= 0);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS pagos_paquete (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paquete_id UUID NOT NULL REFERENCES paquetes(id),
    monto NUMERIC(10,2) NOT NULL CHECK (monto > 0),
    metodo TEXT NOT NULL DEFAULT 'transferencia'
        CHECK (metodo IN ('transferencia', 'efectivo', 'otro')),
    referencia TEXT,
    comprobante_url TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'verificado', 'rechazado')),
    registrado_por UUID REFERENCES usuarios(id),
    verificado_por UUID REFERENCES usuarios(id),
    verificado_en TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pagos_paquete
    ON pagos_paquete (paquete_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pagos_pendientes
    ON pagos_paquete (created_at)
    WHERE estado = 'pendiente';

CREATE OR REPLACE FUNCTION sincronizar_estado_pago_paquete()
RETURNS TRIGGER AS $$
DECLARE
    _paquete_id UUID;
    _monto_cobrar NUMERIC(10,2);
    _total_pagado NUMERIC(10,2);
    _estado TEXT;
BEGIN
    IF TG_OP = 'DELETE' THEN
        _paquete_id := OLD.paquete_id;
    ELSE
        _paquete_id := NEW.paquete_id;
    END IF;

    SELECT COALESCE(valor_flete, 0)
      INTO _monto_cobrar
      FROM paquetes
     WHERE id = _paquete_id;

    SELECT COALESCE(SUM(monto), 0)
      INTO _total_pagado
      FROM pagos_paquete
     WHERE paquete_id = _paquete_id
       AND estado = 'verificado';

    _estado := CASE
        WHEN _monto_cobrar > 0 AND _total_pagado >= _monto_cobrar THEN 'pagado'
        WHEN _total_pagado > 0 THEN 'abono'
        ELSE 'pendiente'
    END;

    UPDATE paquetes
       SET estado_pago = _estado,
           updated_at = NOW()
     WHERE id = _paquete_id;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SET search_path = public;

DROP TRIGGER IF EXISTS trg_sync_pago_paquete ON pagos_paquete;
CREATE TRIGGER trg_sync_pago_paquete
    AFTER INSERT OR UPDATE OR DELETE ON pagos_paquete
    FOR EACH ROW EXECUTE FUNCTION sincronizar_estado_pago_paquete();

DROP TRIGGER IF EXISTS trg_audit_recepciones_usa ON recepciones_usa;
CREATE TRIGGER trg_audit_recepciones_usa
    AFTER INSERT OR UPDATE OR DELETE ON recepciones_usa
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

DROP TRIGGER IF EXISTS trg_audit_pagos_paquete ON pagos_paquete;
CREATE TRIGGER trg_audit_pagos_paquete
    AFTER INSERT OR UPDATE OR DELETE ON pagos_paquete
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_func();

ALTER TABLE recepciones_usa ENABLE ROW LEVEL SECURITY;
ALTER TABLE pagos_paquete ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Service role full access" ON recepciones_usa;
CREATE POLICY "Service role full access" ON recepciones_usa
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

DROP POLICY IF EXISTS "Service role full access" ON pagos_paquete;
CREATE POLICY "Service role full access" ON pagos_paquete
    FOR ALL USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');
