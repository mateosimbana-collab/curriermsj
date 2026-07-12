-- RPC unificado: todas las estadisticas del dashboard en una sola llamada
CREATE OR REPLACE FUNCTION dashboard_stats()
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_clientes', (SELECT COUNT(*) FROM clientes WHERE deleted_at IS NULL),
        'total_paquetes', (SELECT COUNT(*) FROM paquetes WHERE deleted_at IS NULL),
        'paquetes_hoy', (SELECT COUNT(*) FROM paquetes WHERE deleted_at IS NULL AND created_at >= CURRENT_DATE),
        'paquetes_pendientes', (SELECT COUNT(*) FROM paquetes WHERE deleted_at IS NULL AND estado_actual IN ('recibido_en_usa', 'en_transito', 'en_aduana', 'en_destino', 'en_ruta_de_entrega')),
        'paquetes_entregados', (SELECT COUNT(*) FROM paquetes WHERE deleted_at IS NULL AND estado_actual = 'entregado'),
        'total_prospectos', (SELECT COUNT(*) FROM prospectos WHERE estado = 'activo'),
        'sesiones_activas', (SELECT COUNT(*) FROM sesiones_whatsapp),
        'ultimos_paquetes', (SELECT jsonb_agg(row_to_json(t)) FROM (SELECT p.*, row_to_json(c.*) AS clientes FROM paquetes p LEFT JOIN clientes c ON c.id = p.cliente_id WHERE p.deleted_at IS NULL ORDER BY p.created_at DESC LIMIT 10) t),
        'paquetes_por_estado', (SELECT jsonb_agg(jsonb_build_object('estado_actual', estado_actual, 'count', count)) FROM (SELECT p.estado_actual, COUNT(*)::INT AS count FROM paquetes p WHERE p.deleted_at IS NULL GROUP BY p.estado_actual ORDER BY count DESC) sub)
    ) INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql SET search_path = public;

REVOKE ALL ON FUNCTION dashboard_stats() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION dashboard_stats() TO service_role;
