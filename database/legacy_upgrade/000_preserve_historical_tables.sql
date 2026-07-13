-- Ejecutar SOLO sobre una base historica antes de 001_initial_schema.sql.
-- No elimina datos: aparta las tablas cuyo nombre choca con el esquema unificado.

DO $$
BEGIN
    IF to_regclass('public.clientes') IS NOT NULL
       AND EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public' AND table_name = 'clientes' AND column_name = 'phone_number'
       )
       AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public' AND table_name = 'clientes' AND column_name = 'id'
       ) THEN
        IF to_regclass('public.clientes_legacy') IS NOT NULL THEN
            RAISE EXCEPTION 'clientes_legacy ya existe; revisa el preflight antes de continuar';
        END IF;
        ALTER TABLE clientes RENAME TO clientes_legacy;
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clientes_pkey') THEN
            ALTER TABLE clientes_legacy RENAME CONSTRAINT clientes_pkey TO clientes_legacy_pkey;
        END IF;
    END IF;

    IF to_regclass('public.reportes') IS NOT NULL
       AND EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public' AND table_name = 'reportes' AND column_name = 'phone_number'
       )
       AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public' AND table_name = 'reportes' AND column_name = 'cliente_id'
       ) THEN
        IF to_regclass('public.reportes_legacy') IS NOT NULL THEN
            RAISE EXCEPTION 'reportes_legacy ya existe; revisa el preflight antes de continuar';
        END IF;
        ALTER TABLE reportes RENAME TO reportes_legacy;
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'reportes_pkey') THEN
            ALTER TABLE reportes_legacy RENAME CONSTRAINT reportes_pkey TO reportes_legacy_pkey;
        END IF;
        IF to_regclass('public.reportes_id_seq') IS NOT NULL THEN
            ALTER SEQUENCE reportes_id_seq RENAME TO reportes_legacy_id_seq;
        END IF;
    END IF;

    IF to_regclass('public.faq') IS NOT NULL
       AND NOT EXISTS (
            SELECT 1 FROM information_schema.columns
             WHERE table_schema = 'public' AND table_name = 'faq' AND column_name = 'created_at'
       ) THEN
        IF to_regclass('public.faq_legacy') IS NOT NULL THEN
            RAISE EXCEPTION 'faq_legacy ya existe; revisa el preflight antes de continuar';
        END IF;
        ALTER TABLE faq RENAME TO faq_legacy;
        IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'faq_pkey') THEN
            ALTER TABLE faq_legacy RENAME CONSTRAINT faq_pkey TO faq_legacy_pkey;
        END IF;
        IF to_regclass('public.faq_id_seq') IS NOT NULL THEN
            ALTER SEQUENCE faq_id_seq RENAME TO faq_legacy_id_seq;
        END IF;
    END IF;
END $$;

-- El historico permanece disponible durante toda la migracion.
DO $$
BEGIN
    IF to_regclass('public.envios') IS NOT NULL THEN
        COMMENT ON TABLE envios IS 'Tabla historica conservada durante la migracion a paquetes';
    END IF;
END $$;
