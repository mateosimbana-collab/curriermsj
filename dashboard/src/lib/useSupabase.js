import { useState, useEffect, useCallback } from 'react'

const healthUrl = import.meta.env.VITE_BOT_HEALTH_URL || '/health'
const BACKEND_URL = healthUrl.endsWith('/health')
  ? healthUrl.slice(0, -'/health'.length)
  : healthUrl.replace(/\/$/, '')

const apiFetch = (path) => fetch(`${BACKEND_URL}${path}`, {
  cache: 'no-store',
  credentials: 'include',
})

/**
 * Hook para obtener los envíos desde el backend Flask (que actúa como proxy de Supabase).
 */
export function useEnvios() {
  const [envios, setEnvios] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchEnvios = useCallback(async () => {
    try {
      const response = await apiFetch('/api/envios')
      if (!response.ok) {
        throw new Error(`Error en servidor Flask: ${response.status} ${response.statusText}`)
      }
      const data = await response.json()
      if (data && data.error) {
        throw new Error(data.error)
      }
      setEnvios(data || [])
      setError(null)
    } catch (err) {
      console.error('Error al obtener envíos:', err)
      setError(err.message)
      setEnvios([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchEnvios()
    // Polling cada 5 segundos para mantener actualizado el dashboard
    const interval = setInterval(fetchEnvios, 5000)
    return () => clearInterval(interval)
  }, [fetchEnvios])

  return { envios, loading, error, refetch: fetchEnvios }
}

/**
 * Hook para obtener clientes, estados de usuario y reportes desde el backend Flask.
 */
export function useSystemStats() {
  const [stats, setStats] = useState({
    clientes: [],
    estados: [],
    reportes: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchStats = useCallback(async () => {
    try {
      const response = await apiFetch('/api/system-stats')
      if (!response.ok) {
        throw new Error(`Error en servidor Flask: ${response.status} ${response.statusText}`)
      }
      const data = await response.json()
      if (data && data.error) {
        throw new Error(data.error)
      }
      setStats({
        clientes: data.clientes || [],
        estados: data.estados || [],
        reportes: data.reportes || [],
      })
      setError(null)
    } catch (err) {
      console.error('Error al obtener estadísticas del sistema:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    // Polling cada 6 segundos
    const interval = setInterval(fetchStats, 6000)
    return () => clearInterval(interval)
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}

/**
 * Calcula métricas de KPI a partir de los datos reales.
 */
export function calcularMetricas(envios) {
  const hoy = new Date()
  const inicioHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate())
  const inicioSemana = new Date(inicioHoy)
  inicioSemana.setDate(inicioSemana.getDate() - 7)
  const inicioMes = new Date(hoy.getFullYear(), hoy.getMonth(), 1)

  const enviosHoy = envios.filter(e => e.creado_en && new Date(e.creado_en) >= inicioHoy)
  const enviosSemana = envios.filter(e => e.creado_en && new Date(e.creado_en) >= inicioSemana)
  const enviosMes = envios.filter(e => e.creado_en && new Date(e.creado_en) >= inicioMes)

  // Contar destinos únicos
  const destinosUnicos = new Set(envios.map(e => e.direccion_destino).filter(Boolean)).size

  // Tipos de paquete más comunes
  const tiposConteo = {}
  envios.forEach(e => {
    const tipo = e.tipo_paquete || 'Sin especificar'
    tiposConteo[tipo] = (tiposConteo[tipo] || 0) + 1
  })
  const tiposOrdenados = Object.entries(tiposConteo)
    .sort(([, a], [, b]) => b - a)
    .map(([nombre, cantidad]) => ({ nombre, cantidad }))

  // Envíos por día (últimos 7 días)
  const enviosPorDia = []
  for (let i = 6; i >= 0; i--) {
    const dia = new Date(inicioHoy)
    dia.setDate(dia.getDate() - i)
    const siguiente = new Date(dia)
    siguiente.setDate(siguiente.getDate() + 1)

    const count = envios.filter(e => {
      if (!e.creado_en) return false
      const fecha = new Date(e.creado_en)
      return fecha >= dia && fecha < siguiente
    }).length

    enviosPorDia.push({
      dia: dia.toLocaleDateString('es-EC', { weekday: 'short', day: 'numeric' }),
      envios: count,
    })
  }

  // Envíos por hora (hoy)
  const enviosPorHora = []
  for (let h = 6; h <= 20; h++) {
    const count = enviosHoy.filter(e => {
      if (!e.creado_en) return false
      const fecha = new Date(e.creado_en)
      return fecha.getHours() === h
    }).length
    enviosPorHora.push({
      hora: `${String(h).padStart(2, '0')}:00`,
      envios: count,
    })
  }

  return {
    totalEnvios: envios.length,
    enviosHoy: enviosHoy.length,
    enviosSemana: enviosSemana.length,
    enviosMes: enviosMes.length,
    destinosUnicos,
    tiposOrdenados,
    enviosPorDia,
    enviosPorHora,
  }
}
