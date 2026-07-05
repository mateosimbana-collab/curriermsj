-- RPC: Paquetes agrupados por estado
CREATE OR REPLACE FUNCTION paquetes_por_estado()
RETURNS TABLE(estado TEXT, count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT p.estado_actual AS estado, COUNT(*)::BIGINT
    FROM paquetes p
    WHERE p.deleted_at IS NULL
    GROUP BY p.estado_actual
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;
