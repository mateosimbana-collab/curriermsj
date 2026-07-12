-- RPC: Paquetes agrupados por estado
CREATE OR REPLACE FUNCTION paquetes_por_estado()
RETURNS TABLE(estado_actual TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT p.estado_actual, COUNT(*)::BIGINT
    FROM paquetes p
    WHERE p.deleted_at IS NULL
    GROUP BY p.estado_actual
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql SET search_path = public;

REVOKE ALL ON FUNCTION paquetes_por_estado() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION paquetes_por_estado() TO service_role;
