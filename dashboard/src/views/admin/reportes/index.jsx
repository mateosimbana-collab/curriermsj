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
  MdWarning,
  MdPerson,
} from "react-icons/md"
import Card from "components/card/Card"
import { useSystemStats } from "lib/useSupabase"

export default function ReportesDashboard() {
  const { stats, loading, refetch } = useSystemStats()
  const [tabIndex, setTabIndex] = useState(0)

  const reportes = useMemo(() => stats.reportes || [], [stats.reportes])
  const abiertos = useMemo(() => reportes.filter((r) => r.estado === "abierto"), [reportes])
  const cerrados = useMemo(() => reportes.filter((r) => r.estado !== "abierto"), [reportes])
  const currentList = [reportes, abiertos, cerrados][tabIndex]

  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      <Flex direction="column" mb="30px">
        <Flex justify="space-between" align="center" mb="8px" wrap="wrap" gap="12px">
          <Box>
            <Heading as="h1" fontSize="34px" fontWeight="bold" color="white" letterSpacing="tight">
              Reportes e Incidencias
            </Heading>
            <Text fontSize="md" color="secondaryGray.600" mt="4px">
              {reportes.length} reportes — {abiertos.length} abiertos
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
            <Tab>Todos ({reportes.length})</Tab>
            <Tab>Abiertos ({abiertos.length})</Tab>
            <Tab>Cerrados ({cerrados.length})</Tab>
          </TabList>
        </Tabs>
      </Flex>

      <Grid templateColumns={{ base: "repeat(3,1fr)" }} gap="16px" mb="24px">
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Abiertos</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="red.500" lineHeight="1.2">{abiertos.length}</Text>
        </Card>
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Cerrados</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="green.500" lineHeight="1.2">{cerrados.length}</Text>
        </Card>
        <Card p="14px">
          <Text fontSize="sm" color="secondaryGray.600" textTransform="uppercase" letterSpacing="wider" fontWeight="semibold">Total</Text>
          <Text fontSize="28px" fontWeight="extrabold" color="white" lineHeight="1.2">{reportes.length}</Text>
        </Card>
      </Grid>

      <Card p="0" overflow="hidden">
        <Box overflowX="auto">
          <Box as="table" w="100%" fontSize="sm">
            <Box as="thead">
              <Box as="tr" borderBottom="1px solid" borderColor="navy.700">
                {["ID", "Cliente", "Tracking", "Categoría", "Descripción", "Estado", "Asignado", "Fecha"].map((h) => (
                  <Box as="th" key={h} px="16px" py="12px" textAlign="left" textTransform="uppercase" fontSize="xs" fontWeight="bold" color="secondaryGray.600" letterSpacing="wider">
                    {h}
                  </Box>
                ))}
              </Box>
            </Box>
            <Box as="tbody">
              {currentList.map((r) => (
                <Box as="tr" key={r.id} borderBottom="1px solid" borderColor="navy.700" _hover={{ bg: "navy.700" }} transition="background 0.2s">
                  <Box as="td" px="16px" py="12px">
                    <Text fontWeight="bold" color="red.500" fontSize="xs" fontFamily="mono">
                      #{String(r.id).padStart(4, "0")}
                    </Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Flex align="center" gap="6px">
                      <Icon as={MdPerson} w="12px" h="12px" color="secondaryGray.600" />
                      <Text color="white" fontSize="xs">{r.phone_number}</Text>
                    </Flex>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontSize="xs" color="brand.400" fontFamily="mono">{r.tracking_code || "—"}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Badge colorScheme="purple" variant="subtle" borderRadius="full" px="2" fontSize="xs">{r.categoria || "General"}</Badge>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontSize="xs" color="secondaryGray.600" maxW="200px" noOfLines={2}>{r.descripcion}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Badge colorScheme={r.estado === "abierto" ? "red" : "green"} variant="solid" borderRadius="full" px="2" fontSize="xs">
                      {r.estado}
                    </Badge>
                  </Box>
                  <Box as="td" px="16px" py="12px">
                    <Text fontSize="xs" color="secondaryGray.600">{r.agente_asignado || "—"}</Text>
                  </Box>
                  <Box as="td" px="16px" py="12px" color="secondaryGray.600" fontSize="xs" whiteSpace="nowrap">
                    {r.creado_en ? new Date(r.creado_en).toLocaleDateString("es-EC") : "—"}
                  </Box>
                </Box>
              ))}
              {currentList.length === 0 && (
                <Box as="tr">
                  <Box as="td" colSpan={8} textAlign="center" py="60px" color="secondaryGray.600">
                    <Icon as={MdWarning} w="40px" h="40px" mb="8px" opacity="0.3" />
                    <Text fontSize="sm">No hay reportes</Text>
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
