import React, { useState, useMemo, useCallback } from "react"
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Icon,
  Text,
  Badge,
  Stack,
  Progress,
} from "@chakra-ui/react"
import {
  MdRefresh,
  MdError,
  MdCloud,
  MdStorage,
  MdRouter,
  MdSpeed,
  MdTimer,
  MdSettings,
  MdNetworkCheck,
  MdList,
} from "react-icons/md"
import Card from "components/card/Card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  AreaChart,
  Area,
} from "recharts"

function generateMockData() {
  const now = Date.now()
  const hours = Array.from({ length: 24 }, (_, i) => {
    const d = new Date(now - (23 - i) * 3600000)
    const h = d.getHours()
    const baseLatency = 80 + Math.random() * 60
    const spike = Math.random() > 0.85 ? Math.random() * 250 : 0
    return {
      hora: `${String(h).padStart(2, "0")}:00`,
      latencia: Math.round(baseLatency + spike),
      throughput: Math.round(160 + Math.random() * 240),
      errores: Math.round(Math.random() * 6),
      p99: Math.round(baseLatency + spike + Math.random() * 40 + 20),
    }
  })

  const services = [
    { name: "API Gateway", status: "healthy", uptime: "99.97%", icon: MdRouter },
    { name: "Auth Service", status: "healthy", uptime: "99.99%", icon: MdCloud },
    { name: "Payment Worker", status: "degraded", uptime: "98.2%", icon: MdStorage },
    { name: "DB Primary", status: "healthy", uptime: "99.99%", icon: MdStorage },
    { name: "DB Replica", status: "healthy", uptime: "99.95%", icon: MdStorage },
    { name: "Queue Worker", status: "healthy", uptime: "99.9%", icon: MdSpeed },
    { name: "Notification", status: "healthy", uptime: "99.8%", icon: MdNetworkCheck },
    { name: "WhatsApp Bot", status: "healthy", uptime: "99.93%", icon: MdCloud },
  ]

  const events = [
    { timestamp: new Date(now - 30000).toISOString(), app: "api-gateway", action: "POST /api/envios", latency: 1452, status: "error", requestId: "req_a1b2c3", message: "Timeout upstream" },
    { timestamp: new Date(now - 120000).toISOString(), app: "payment-worker", action: "process_payment", latency: 3200, status: "error", requestId: "pay_x9y8z7", message: "Provider timeout: bancopichincha" },
    { timestamp: new Date(now - 300000).toISOString(), app: "whatsapp-bot", action: "send_message", latency: 450, status: "ok", requestId: "msg_k4l5m6", message: "Message delivered" },
    { timestamp: new Date(now - 600000).toISOString(), app: "auth-service", action: "verify_token", latency: 12, status: "ok", requestId: "auth_p3q4r5", message: "Token valid" },
    { timestamp: new Date(now - 900000).toISOString(), app: "db-primary", action: "SELECT envios", latency: 230, status: "warning", requestId: "db_s6t7u8", message: "Slow query (>200ms)" },
    { timestamp: new Date(now - 1800000).toISOString(), app: "api-gateway", action: "GET /api/system-stats", latency: 89, status: "ok", requestId: "req_v9w0x1", message: "OK" },
    { timestamp: new Date(now - 3600000).toISOString(), app: "notification", action: "send_email", latency: 1200, status: "error", requestId: "notif_y2z3a4", message: "SMTP connection failed" },
    { timestamp: new Date(now - 7200000).toISOString(), app: "queue-worker", action: "process_retry", latency: 560, status: "ok", requestId: "queue_b5c6d7", message: "Payment retry #3 successful" },
  ]

  return { hours, services, events }
}

function StatusBadge({ status }) {
  const colorMap = {
    healthy: "green",
    ok: "green",
    degraded: "orange",
    warning: "orange",
    error: "red",
  }
  return (
    <Badge colorScheme={colorMap[status] || "gray"} variant="solid" borderRadius="full" px="2" fontSize="xs">
      {status}
    </Badge>
  )
}

function MetricCard({ label, value, subtitle, icon, color }) {
  return (
    <Card p="16px" pb="20px">
      <Flex align="center" justify="space-between" mb="12px">
        <Text fontSize="sm" fontWeight="semibold" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider">
          {label}
        </Text>
        <Icon as={icon} w="20px" h="20px" color={color} opacity="0.7" />
      </Flex>
      <Text fontSize="28px" fontWeight="extrabold" color="white" lineHeight="1.2">
        {value}
      </Text>
      {subtitle && (
        <Text fontSize="xs" color="secondaryGray.600" mt="4px">
          {subtitle}
        </Text>
      )}
    </Card>
  )
}

export default function ObservabilityDashboard() {
  const [mockData, setMockData] = useState(generateMockData)

  const refresh = useCallback(() => {
    setMockData(generateMockData())
  }, [])

  const { hours, services, events } = mockData

  const currentMetrics = useMemo(() => {
    const lastHour = hours.slice(-2)
    const avgLatency = Math.round(lastHour.reduce((s, h) => s + h.latencia, 0) / lastHour.length)
    const avgThroughput = Math.round(lastHour.reduce((s, h) => s + h.throughput, 0) / lastHour.length)
    const totalErrors = lastHour.reduce((s, h) => s + h.errores, 0)
    const totalReqs = lastHour.reduce((s, h) => s + h.throughput, 0)
    const errorRate = totalReqs > 0 ? ((totalErrors / totalReqs) * 100).toFixed(1) : "0.0"
    const maxP99 = Math.round(lastHour.reduce((s, h) => Math.max(s, h.p99), 0))
    return {
      errorRate: `${errorRate}%`,
      latencia: `${avgLatency}ms`,
      p99: `${maxP99}ms`,
      throughput: `${avgThroughput.toLocaleString()} req/min`,
      dbPool: "42 / 100",
    }
  }, [hours])

  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      <Flex direction="column" mb="30px">
        <Flex justify="space-between" align="center" mb="8px" wrap="wrap" gap="12px">
          <Box>
            <Heading as="h1" fontSize="34px" fontWeight="bold" color="white" letterSpacing="tight">
              Observabilidad
            </Heading>
            <Text fontSize="md" color="secondaryGray.600" mt="4px">
              Monitoreo de infraestructura, rendimiento y logs del sistema
            </Text>
          </Box>
          <Button
            leftIcon={<Icon as={MdRefresh} w="16px" h="16px" />}
            variant="brand"
            fontSize="sm"
            fontWeight="medium"
            borderRadius="16px"
            px="24px"
            onClick={refresh}
          >
            Actualizar
          </Button>
        </Flex>
      </Flex>

      <Grid templateColumns={{ base: "repeat(2, 1fr)", md: "repeat(4, 1fr)" }} gap={{ base: "16px", md: "20px" }} mb="24px">
        <MetricCard label="Tasa de Error" value={currentMetrics.errorRate} icon={MdError} color="red.500" subtitle="Última hora" />
        <MetricCard label="Latencia (p99)" value={currentMetrics.p99} icon={MdTimer} color="orange.500" subtitle="Promedio última hora" />
        <MetricCard label="Throughput" value={currentMetrics.throughput} icon={MdSpeed} color="blue.500" subtitle="Última hora" />
        <MetricCard label="DB Pool" value={currentMetrics.dbPool} icon={MdStorage} color="green.500" subtitle="Conexiones activas" />
      </Grid>

      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap="24px" mb="24px">
        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex w="44px" h="44px" borderRadius="12px" bg="rgba(66, 42, 251, 0.1)" align="center" justify="center" me="12px">
              <Icon as={MdTimer} w="20px" h="20px" color="brand.400" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">Latencia (p99) por Hora</Text>
              <Text fontSize="sm" color="secondaryGray.600">Últimas 24 horas</Text>
            </Box>
          </Flex>
          <Box h="260px">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={hours}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1B254B" vertical={false} />
                <XAxis dataKey="hora" stroke="#A3AED0" tick={{ fontSize: 11, fill: "#A3AED0" }} axisLine={false} tickLine={false} interval={3} />
                <YAxis stroke="#A3AED0" tick={{ fontSize: 11, fill: "#A3AED0" }} axisLine={false} tickLine={false} unit="ms" />
                <Tooltip contentStyle={{ background: "#0b1437", border: "1px solid #1B254B", borderRadius: "12px", color: "#f1f5f9" }} />
                <defs>
                  <linearGradient id="latenciaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7551FF" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#7551FF" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="p99" stroke="#7551FF" fill="url(#latenciaGrad)" strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        </Card>

        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex w="44px" h="44px" borderRadius="12px" bg="rgba(1, 181, 116, 0.1)" align="center" justify="center" me="12px">
              <Icon as={MdSpeed} w="20px" h="20px" color="green.500" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">Throughput</Text>
              <Text fontSize="sm" color="secondaryGray.600">Solicitudes por minuto</Text>
            </Box>
          </Flex>
          <Box h="260px">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hours} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="#1B254B" vertical={false} />
                <XAxis dataKey="hora" stroke="#A3AED0" tick={{ fontSize: 11, fill: "#A3AED0" }} axisLine={false} tickLine={false} interval={3} />
                <YAxis stroke="#A3AED0" tick={{ fontSize: 11, fill: "#A3AED0" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: "#0b1437", border: "1px solid #1B254B", borderRadius: "12px", color: "#f1f5f9" }} />
                <Bar dataKey="throughput" radius={[4, 4, 0, 0]} maxBarSize={24}>
                  {hours.map((entry, i) => (
                    <Cell key={i} fill={entry.errores > 5 ? "#EE5D50" : "#01B574"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid>

      <Grid templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap="24px" mb="24px">
        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex w="44px" h="44px" borderRadius="12px" bg="rgba(57, 101, 255, 0.1)" align="center" justify="center" me="12px">
              <Icon as={MdCloud} w="20px" h="20px" color="blue.500" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">Estado de Servicios</Text>
              <Text fontSize="sm" color="secondaryGray.600">{services.filter((s) => s.status === "healthy").length}/{services.length} saludables</Text>
            </Box>
          </Flex>
          <Stack spacing="12px">
            {services.map((svc) => (
              <Flex key={svc.name} align="center" justify="space-between" p="8px 12px" borderRadius="8px" bg="navy.800">
                <Flex align="center" gap="10px">
                  <Icon
                    as={svc.icon}
                    w="16px"
                    h="16px"
                    color={svc.status === "healthy" ? "green.500" : svc.status === "degraded" ? "orange.500" : "red.500"}
                  />
                  <Text fontSize="sm" fontWeight="medium" color="white">{svc.name}</Text>
                </Flex>
                <Flex align="center" gap="8px">
                  <Text fontSize="xs" color="secondaryGray.600">{svc.uptime}</Text>
                  <StatusBadge status={svc.status} />
                </Flex>
              </Flex>
            ))}
          </Stack>
        </Card>

        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex w="44px" h="44px" borderRadius="12px" bg="rgba(255, 181, 71, 0.1)" align="center" justify="center" me="12px">
              <Icon as={MdSettings} w="20px" h="20px" color="orange.500" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">Recursos del Sistema</Text>
              <Text fontSize="sm" color="secondaryGray.600">Uso actual de recursos</Text>
            </Box>
          </Flex>
          <Stack spacing="16px">
            <Box>
              <Flex justify="space-between" mb="4px">
                <Text fontSize="sm" color="secondaryGray.600">CPU</Text>
                <Text fontSize="sm" fontWeight="bold" color="white">67%</Text>
              </Flex>
              <Progress value={67} colorScheme="orange" borderRadius="6px" size="sm" />
            </Box>
            <Box>
              <Flex justify="space-between" mb="4px">
                <Text fontSize="sm" color="secondaryGray.600">Memoria</Text>
                <Text fontSize="sm" fontWeight="bold" color="white">4.2 / 8 GB</Text>
              </Flex>
              <Progress value={52} colorScheme="blue" borderRadius="6px" size="sm" />
            </Box>
            <Box>
              <Flex justify="space-between" mb="4px">
                <Text fontSize="sm" color="secondaryGray.600">Disco</Text>
                <Text fontSize="sm" fontWeight="bold" color="white">120 / 500 GB</Text>
              </Flex>
              <Progress value={24} colorScheme="green" borderRadius="6px" size="sm" />
            </Box>
            <Box>
              <Flex justify="space-between" mb="4px">
                <Text fontSize="sm" color="secondaryGray.600">Red (entrada/salida)</Text>
                <Text fontSize="sm" fontWeight="bold" color="white">45 / 120 Mbps</Text>
              </Flex>
              <Progress value={37} colorScheme="purple" borderRadius="6px" size="sm" />
            </Box>
          </Stack>
        </Card>
      </Grid>

      <Card p="0" overflow="hidden">
        <Box p="24px" pb="0">
          <Flex align="center" mb="16px">
            <Flex w="44px" h="44px" borderRadius="12px" bg="rgba(238, 93, 80, 0.1)" align="center" justify="center" me="12px">
              <Icon as={MdList} w="20px" h="20px" color="red.500" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">Eventos Recientes</Text>
              <Text fontSize="sm" color="secondaryGray.600">Últimos eventos del sistema</Text>
            </Box>
          </Flex>
        </Box>
        <Box overflowX="auto" pb="16px">
          <Box as="table" w="100%" fontSize="sm">
            <Box as="thead">
              <Box as="tr" borderBottom="1px solid" borderColor="navy.700">
                {["Timestamp", "Servicio", "Acción", "Latencia", "Estado", "Detalle"].map((h) => (
                  <Box as="th" key={h} px="16px" py="12px" textAlign="left" textTransform="uppercase" fontSize="xs" fontWeight="bold" color="secondaryGray.600" letterSpacing="wider">
                    {h}
                  </Box>
                ))}
              </Box>
            </Box>
            <Box as="tbody">
              {events.map((evt, idx) => (
                <Box as="tr" key={idx} borderBottom="1px solid" borderColor="navy.700" _hover={{ bg: "navy.700" }} transition="background 0.2s">
                  <Box as="td" px="16px" py="12px" color="secondaryGray.600" fontSize="xs" whiteSpace="nowrap">
                    {new Date(evt.timestamp).toLocaleTimeString("es-EC")}
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontWeight="medium" color="white" fontSize="xs">{evt.app}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text color="secondaryGray.600" fontSize="xs" fontFamily="mono">{evt.action}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px" fontSize="xs" color={evt.latency > 1000 ? "red.500" : "secondaryGray.600"}>
                    {evt.latency}ms
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <StatusBadge status={evt.status} />
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text color="secondaryGray.600" fontSize="xs" maxW="200px" noOfLines={1}>{evt.message}</Text>
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        </Box>
      </Card>
    </Box>
  )
}
