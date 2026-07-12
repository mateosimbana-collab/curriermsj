import React, { useMemo } from "react"
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Icon,
  Text,
  useColorModeValue,
} from "@chakra-ui/react"
import {
  MdInventory2,
  MdRefresh,
  MdBarChart,
  MdPeople,
  MdMap,
  MdLayers,
  MdCalendarToday,
  MdTrendingUp,
} from "react-icons/md"
import Card from "components/card/Card"
import { useEnvios, calcularMetricas } from "lib/useSupabase"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts"

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <Box bg="navy.800" border="1px solid" borderColor="navy.700" borderRadius="12px" px="4" py="3" shadow="xl">
      <Text fontSize="xs" color="secondaryGray.600" fontWeight="medium" mb="1">{label}</Text>
      <Text fontSize="lg" fontWeight="bold" color="white">{payload[0].value} envíos</Text>
    </Box>
  )
}

function KpiCard({ label, value, icon, color }) {
  return (
    <Card p="16px" pb="20px">
      <Flex align="center" justify="space-between" mb="12px">
        <Text fontSize="sm" fontWeight="semibold" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider">
          {label}
        </Text>
        <Icon as={icon} w="20px" h="20px" color={color} opacity="0.7" />
      </Flex>
      <Text fontSize="28px" fontWeight="extrabold" color="white" lineHeight="1.2">
        {typeof value === "number" ? value.toLocaleString("es-EC") : value}
      </Text>
    </Card>
  )
}

export default function MainDashboard() {
  const { envios, loading: loadingEnvios, refetch: refetchEnvios } = useEnvios()
  
  const metricas = useMemo(() => calcularMetricas(envios), [envios])
  
  const chartData = metricas.enviosPorDia
  
  const maxVal = useMemo(() =>
    Math.max(...chartData.map((d) => d.envios), 1),
    [chartData]
  )
  const brandColor = useColorModeValue("brand.500", "brand.400")

  const kpiCards = useMemo(() => [
    { label: "Total Envíos", value: metricas.totalEnvios, icon: MdInventory2, color: "brand.400" },
    { label: "Hoy", value: metricas.enviosHoy, icon: MdCalendarToday, color: "green.500" },
    { label: "Esta Semana", value: metricas.enviosSemana, icon: MdTrendingUp, color: "blue.500" },
    { label: "Este Mes", value: metricas.enviosMes, icon: MdLayers, color: "orange.500" },
    { label: "Clientes", value: metricas.clientesUnicos || envios.length, icon: MdPeople, color: "red.500" },
    { label: "Destinos", value: metricas.destinosUnicos, icon: MdMap, color: "brand.300" },
  ], [metricas, envios.length])

  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      {/* Header */}
      <Flex direction="column" mb="30px">
        <Flex justify="space-between" align="center" mb="8px" wrap="wrap" gap="12px">
          <Box>
            <Heading as="h1" fontSize="34px" fontWeight="bold" color="white" letterSpacing="tight">
              Gestión Courier
            </Heading>
            <Text fontSize="md" color="secondaryGray.600" mt="4px">
              Monitoreo y administración de envíos de usuarios de CurrierMsj
            </Text>
          </Box>
          <Button
            leftIcon={<Icon as={MdRefresh} w="16px" h="16px" />}
            variant="brand"
            fontSize="sm"
            fontWeight="medium"
            borderRadius="16px"
            px="24px"
            onClick={refetchEnvios}
            isLoading={loadingEnvios}
          >
            Actualizar Envíos
          </Button>
        </Flex>
      </Flex>

      {/* KPI Cards */}
      <Grid
        templateColumns={{ base: "repeat(2, 1fr)", md: "repeat(3, 1fr)", xl: "repeat(6, 1fr)" }}
        gap={{ base: "16px", md: "20px" }}
        mb="24px"
      >
        {kpiCards.map((kpi) => (
          <KpiCard key={kpi.label} {...kpi} />
        ))}
      </Grid>

      {/* Charts Row */}
      <Grid templateColumns={{ base: "1fr", lg: "2fr 1fr" }} gap="24px" mb="24px">
        {/* Envíos por Día */}
        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex
              w="44px"
              h="44px"
              borderRadius="12px"
              bg="rgba(66, 42, 251, 0.1)"
              align="center"
              justify="center"
              me="12px"
            >
              <Icon as={MdTrendingUp} w="20px" h="20px" color="brand.400" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">
                Envíos por Día
              </Text>
              <Text fontSize="sm" color="secondaryGray.600">
                Últimos 7 días
              </Text>
            </Box>
          </Flex>
          <Box h="260px">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} barCategoryGap="20%">
                <CartesianGrid strokeDasharray="3 3" stroke="#1B254B" vertical={false} />
                <XAxis
                  dataKey="dia"
                  stroke="#A3AED0"
                  tick={{ fontSize: 12, fill: "#A3AED0" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  stroke="#A3AED0"
                  tick={{ fontSize: 12, fill: "#A3AED0" }}
                  axisLine={false}
                  tickLine={false}
                  allowDecimals={false}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(27, 37, 75, 0.5)" }} />
                <Bar dataKey="envios" radius={[8, 8, 4, 4]} maxBarSize={48}>
                  {chartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.envios === maxVal ? brandColor : `${brandColor}66`}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>

        {/* Tipos de Paquete */}
        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex
              w="44px"
              h="44px"
              borderRadius="12px"
              bg="rgba(66, 42, 251, 0.1)"
              align="center"
              justify="center"
              me="12px"
            >
              <Icon as={MdBarChart} w="20px" h="20px" color="brand.400" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">
                Tipos de Paquete
              </Text>
              <Text fontSize="sm" color="secondaryGray.600">
                {metricas.totalEnvios} total
              </Text>
            </Box>
          </Flex>
          <Box h="260px">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={metricas.tiposOrdenados.slice(0, 8)}
                layout="vertical"
                barCategoryGap="15%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#1B254B" horizontal={false} />
                <XAxis
                  type="number"
                  stroke="#A3AED0"
                  tick={{ fontSize: 11, fill: "#A3AED0" }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="nombre"
                  stroke="#A3AED0"
                  tick={{ fontSize: 11, fill: "#A3AED0" }}
                  axisLine={false}
                  tickLine={false}
                  width={90}
                />
                <Tooltip
                  contentStyle={{
                    background: "#0b1437",
                    border: "1px solid #1B254B",
                    borderRadius: "12px",
                    color: "#f1f5f9",
                  }}
                />
                <Bar dataKey="cantidad" radius={[0, 8, 8, 0]} maxBarSize={20}>
                  {metricas.tiposOrdenados.slice(0, 8).map((entry, index) => {
                    const colors = ["#422AFB", "#7551FF", "#01B574", "#FFB547", "#EE5D50", "#3965FF", "#A3AED0", "#1B254B"]
                    return <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Box>
        </Card>
      </Grid>

      {/* Activity Hourly + Shipments Table */}
      <Grid templateColumns={{ base: "1fr", lg: "1fr 2fr" }} gap="24px">
        {/* Actividad por Hora */}
        <Card p="24px">
          <Flex align="center" mb="20px">
            <Flex
              w="44px"
              h="44px"
              borderRadius="12px"
              bg="rgba(1, 181, 116, 0.1)"
              align="center"
              justify="center"
              me="12px"
            >
              <Icon as={MdBarChart} w="20px" h="20px" color="green.500" />
            </Flex>
            <Box>
              <Text fontSize="md" fontWeight="bold" color="white">
                Actividad Hoy
              </Text>
              <Text fontSize="sm" color="secondaryGray.600">
                {metricas.enviosHoy} envíos registrados
              </Text>
            </Box>
          </Flex>
          <Box>
            {metricas.enviosPorHora.map((item) => {
              const maxH = Math.max(...metricas.enviosPorHora.map((d) => d.envios), 1)
              const pct = item.envios > 0 ? Math.max((item.envios / maxH) * 100, 6) : 0
              return (
                <Flex key={item.hora} align="center" mb="6px">
                  <Text
                    w="50px"
                    fontSize="xs"
                    color="secondaryGray.600"
                    fontFamily="mono"
                    fontWeight="medium"
                  >
                    {item.hora}
                  </Text>
                  <Box flex="1" h="20px" bg="navy.700" borderRadius="6px" overflow="hidden" position="relative">
                    <Box
                      h="100%"
                      bg="linear-gradient(90deg, rgba(1, 181, 116, 0.6), rgba(1, 181, 116, 1))"
                      borderRadius="6px"
                      transition="width 0.7s ease-out"
                      w={`${pct}%`}
                    />
                    {item.envios > 0 && (
                      <Text
                        position="absolute"
                        right="8px"
                        top="50%"
                        transform="translateY(-50%)"
                        fontSize="xs"
                        fontWeight="bold"
                        color="white"
                      >
                        {item.envios}
                      </Text>
                    )}
                  </Box>
                </Flex>
              )
            })}
          </Box>
        </Card>

        {/* Tabla de Envíos Recientes */}
        <Card p="0" overflow="hidden">
          <Box p="24px" pb="0">
            <Flex align="center" mb="16px">
              <Flex
                w="44px"
                h="44px"
                borderRadius="12px"
                bg="rgba(57, 101, 255, 0.1)"
                align="center"
                justify="center"
                me="12px"
              >
                <Icon as={MdInventory2} w="20px" h="20px" color="blue.500" />
              </Flex>
              <Box>
                <Text fontSize="md" fontWeight="bold" color="white">
                  Envíos Recientes
                </Text>
                <Text fontSize="sm" color="secondaryGray.600">
                  {envios.length} registros
                </Text>
              </Box>
            </Flex>
          </Box>
          <Box overflowX="auto" pb="16px">
            <Box as="table" w="100%" fontSize="sm">
              <Box as="thead">
                <Box as="tr" borderBottom="1px solid" borderColor="navy.700">
                  {["ID", "Remitente", "Destinatario", "Tipo", "Fecha"].map((h) => (
                    <Box
                      as="th"
                      key={h}
                      px="16px"
                      py="12px"
                      textAlign="left"
                      textTransform="uppercase"
                      fontSize="xs"
                      fontWeight="bold"
                      color="secondaryGray.600"
                      letterSpacing="wider"
                    >
                      {h}
                    </Box>
                  ))}
                </Box>
              </Box>
              <Box as="tbody">
                {envios.slice(0, 10).map((envio) => (
                  <Box
                    as="tr"
                    key={envio.id}
                    borderBottom="1px solid"
                    borderColor="navy.700"
                    _hover={{ bg: "navy.700" }}
                    transition="background 0.2s"
                  >
                    <Box as="td" px="16px" py="12px" fontWeight="semibold" color="white">
                      #{envio.id}
                    </Box>
                    <Box as="td" px="16px" py="12px">
                      <Text fontWeight="medium" color="white" noOfLines={1}>
                        {envio.remitente || "—"}
                      </Text>
                      <Text fontSize="xs" color="secondaryGray.600">
                        {envio.telefono_remitente || ""}
                      </Text>
                    </Box>
                    <Box as="td" px="16px" py="12px">
                      <Text fontWeight="medium" color="white" noOfLines={1}>
                        {envio.destinatario || "—"}
                      </Text>
                      <Text fontSize="xs" color="secondaryGray.600">
                        {envio.telefono_destinatario || ""}
                      </Text>
                    </Box>
                    <Box as="td" px="16px" py="12px">
                      <Box
                        as="span"
                        bg="rgba(66, 42, 251, 0.1)"
                        color="brand.300"
                        border="1px solid"
                        borderColor="rgba(66, 42, 251, 0.2)"
                        borderRadius="full"
                        px="10px"
                        py="4px"
                        fontSize="xs"
                        fontWeight="medium"
                      >
                        {(envio.tipo_paquete || "—").replace(/[\u{1F4C4}\u{1F4E6}\u{2709}]/gu, "").trim()}
                      </Box>
                    </Box>
                    <Box as="td" px="16px" py="12px" color="secondaryGray.600" fontSize="xs">
                      {envio.creado_en
                        ? new Date(envio.creado_en).toLocaleDateString("es-EC", {
                            day: "2-digit",
                            month: "short",
                            hour: "2-digit",
                            minute: "2-digit",
                          })
                        : "—"}
                    </Box>
                  </Box>
                ))}
                {envios.length === 0 && (
                  <Box as="tr">
                    <Box as="td" colSpan={5} textAlign="center" py="40px" color="secondaryGray.600">
                      <Icon as={MdInventory2} w="40px" h="40px" mb="8px" opacity="0.3" />
                      <Text fontSize="sm">No se encontraron envíos</Text>
                    </Box>
                  </Box>
                )}
              </Box>
            </Box>
          </Box>
        </Card>
      </Grid>
    </Box>
  )
}
