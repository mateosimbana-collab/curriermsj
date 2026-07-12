import React, { useState, useMemo } from "react"
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Icon,
  Text,
  Badge,
  Tabs,
  TabList,
  Tab,
} from "@chakra-ui/react"
import {
  MdRefresh,
  MdInventory2,
  MdLocationOn,
} from "react-icons/md"
import Card from "components/card/Card"
import { useEnvios } from "lib/useSupabase"

const STATUS_COLORS = {
  pendiente: "yellow",
  recibido: "blue",
  en_transito: "orange",
  en_ruta: "purple",
  entregado: "green",
}

const STATUS_LABELS = {
  pendiente: "Pendiente",
  recibido: "Recibido",
  en_transito: "En Tránsito",
  en_ruta: "En Ruta",
  entregado: "Entregado",
}

export default function PendientesDashboard() {
  const { envios, loading, refetch } = useEnvios()
  const [tabIndex, setTabIndex] = useState(0)

  const pendientes = useMemo(() => envios.filter((e) => e.estado !== "entregado"), [envios])
  const activos = useMemo(() => envios.filter((e) => e.estado === "en_transito" || e.estado === "en_ruta"), [envios])
  const entregados = useMemo(() => envios.filter((e) => e.estado === "entregado"), [envios])

  const currentList = [pendientes, activos, entregados][tabIndex]

  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      <Flex direction="column" mb="30px">
        <Flex justify="space-between" align="center" mb="8px" wrap="wrap" gap="12px">
          <Box>
            <Heading as="h1" fontSize="34px" fontWeight="bold" color="white" letterSpacing="tight">
              Envíos
            </Heading>
            <Text fontSize="md" color="secondaryGray.600" mt="4px">
              {envios.length} registros — {pendientes.length} pendientes
            </Text>
          </Box>
          <Button
            leftIcon={<Icon as={MdRefresh} w="16px" h="16px" />}
            variant="brand" fontSize="sm" fontWeight="medium" borderRadius="16px" px="24px"
            onClick={refetch} isLoading={loading}
          >
            Actualizar
          </Button>
        </Flex>

        <Tabs variant="soft-rounded" colorScheme="brand" index={tabIndex} onChange={setTabIndex}>
          <TabList>
            <Tab>Pendientes ({pendientes.length})</Tab>
            <Tab>En Ruta ({activos.length})</Tab>
            <Tab>Entregados ({entregados.length})</Tab>
          </TabList>
        </Tabs>
      </Flex>

      {/* KPIs */}
      <Grid templateColumns={{ base: "repeat(2,1fr)", md: "repeat(4,1fr)" }} gap="16px" mb="24px">
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Pendientes</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="yellow.500" lineHeight="1.2">{pendientes.length}</Text>
        </Card>
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">En Tránsito</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="orange.500" lineHeight="1.2">{activos.length}</Text>
        </Card>
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Entregados</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="green.500" lineHeight="1.2">{entregados.length}</Text>
        </Card>
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Total</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="white" lineHeight="1.2">{envios.length}</Text>
        </Card>
      </Grid>

      {/* Table */}
      <Card p="0" overflow="hidden">
        <Box overflowX="auto">
          <Box as="table" w="100%" fontSize="sm">
            <Box as="thead">
              <Box as="tr" borderBottom="1px solid" borderColor="navy.700">
                {["Tracking", "Remitente", "Destinatario", "Tipo", "Estado", "Destino", "Fecha"].map((h) => (
                  <Box as="th" key={h} px="16px" py="12px" textAlign="left" textTransform="uppercase" fontSize="xs" fontWeight="bold" color="secondaryGray.600" letterSpacing="wider">
                    {h}
                  </Box>
                ))}
              </Box>
            </Box>
            <Box as="tbody">
              {currentList.map((envio) => (
                <Box as="tr" key={envio.id} borderBottom="1px solid" borderColor="navy.700" _hover={{ bg: "navy.700" }} transition="background 0.2s">
                  <Box as="td" px="16px" py="12px">
                    <Text fontWeight="bold" color="brand.400" fontSize="xs" fontFamily="mono">
                      {envio.tracking_code || `CUR-${String(envio.id).padStart(5, "0")}`}
                    </Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontWeight="medium" color="white" noOfLines={1}>{envio.remitente || "—"}</Text>
                    <Text fontSize="xs" color="secondaryGray.600">{envio.telefono_remitente || ""}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontWeight="medium" color="white" noOfLines={1}>{envio.destinatario || "—"}</Text>
                    <Text fontSize="xs" color="secondaryGray.600">{envio.telefono_destinatario || ""}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontSize="xs" color="secondaryGray.600">{(envio.tipo_paquete || "—").replace(/[\u{1F4C4}\u{1F4E6}\u{2709}]/gu, "").trim()}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Badge colorScheme={STATUS_COLORS[envio.estado] || "gray"} variant="solid" borderRadius="full" px="3" py="1" fontSize="xs">
                      {STATUS_LABELS[envio.estado] || envio.estado}
                    </Badge>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Flex align="center" gap="4px">
                      <Icon as={MdLocationOn} w="12px" h="12px" color="secondaryGray.600" />
                      <Text fontSize="xs" color="secondaryGray.600" noOfLines={1}>{envio.direccion_destino || "—"}</Text>
                    </Flex>
                  </Box>
                  <Box as="td" px="16px" py="12px" color="secondaryGray.600" fontSize="xs" whiteSpace="nowrap">
                    {envio.creado_en
                      ? new Date(envio.creado_en).toLocaleDateString("es-EC", {
                          day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
                        })
                      : "—"}
                  </Box>
                </Box>
              ))}
              {currentList.length === 0 && (
                <Box as="tr">
                  <Box as="td" colSpan={7} textAlign="center" py="60px" color="secondaryGray.600">
                    <Icon as={MdInventory2} w="40px" h="40px" mb="8px" opacity="0.3" />
                    <Text fontSize="sm">No hay envíos en esta categoría</Text>
                  </Box>
                </Box>
              )}
            </Box>
          </Box>
        </Box>
      </Card>
    </Box>
  )
}
