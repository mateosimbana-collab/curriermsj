import React, { useState, useMemo } from "react"
import {
  Box,
  Button,
  Flex,
  Grid,
  Heading,
  Icon,
  Text,
  Input,
  InputGroup,
  InputLeftElement,
} from "@chakra-ui/react"
import {
  MdPeople,
  MdRefresh,
  MdSearch,
  MdPhone,
  MdLocationOn,
  MdCalendarToday,
} from "react-icons/md"
import Card from "components/card/Card"
import { useEnvios, useSystemStats } from "lib/useSupabase"

export default function ClientesDashboard() {
  const { stats, loading, refetch } = useSystemStats()
  const { envios } = useEnvios()
  const [search, setSearch] = useState("")

  const clientesConEnvios = useMemo(() => {
    const clientes = stats.clientes || []
    return clientes.map((c) => ({
      ...c,
      totalEnvios: envios.filter((e) => e.telefono_remitente === c.phone_number).length,
      enviosPendientes: envios.filter(
        (e) => e.telefono_remitente === c.phone_number && e.estado !== "entregado"
      ).length,
      ultimoEnvio: envios
        .filter((e) => e.telefono_remitente === c.phone_number)
        .sort((a, b) => new Date(b.creado_en) - new Date(a.creado_en))[0],
    }))
  }, [stats.clientes, envios])

  const filtered = useMemo(() => {
    if (!search) return clientesConEnvios
    const q = search.toLowerCase()
    return clientesConEnvios.filter(
      (c) =>
        c.nombre?.toLowerCase().includes(q) ||
        c.apellido?.toLowerCase().includes(q) ||
        c.phone_number?.includes(q) ||
        c.ciudad?.toLowerCase().includes(q)
    )
  }, [clientesConEnvios, search])

  return (
    <Box pt={{ base: "180px", md: "80px", xl: "80px" }}>
      <Flex direction="column" mb="30px">
        <Flex justify="space-between" align="center" mb="8px" wrap="wrap" gap="12px">
          <Box>
            <Heading as="h1" fontSize="34px" fontWeight="bold" color="white" letterSpacing="tight">
              Clientes
            </Heading>
            <Text fontSize="md" color="secondaryGray.600" mt="4px">
              {stats.clientes?.length || 0} clientes registrados en el bot
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
        <InputGroup maxW="400px">
          <InputLeftElement pointerEvents="none">
            <Icon as={MdSearch} color="secondaryGray.600" />
          </InputLeftElement>
          <Input
            placeholder="Buscar por nombre, teléfono o ciudad..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            variant="main" borderRadius="12px"
          />
        </InputGroup>
      </Flex>

      <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", xl: "repeat(3, 1fr)" }} gap="20px">
        {filtered.map((cliente) => (
          <Card key={cliente.phone_number} p="20px">
            <Flex align="center" mb="12px">
              <Flex
                w="44px" h="44px" borderRadius="12px" bg="rgba(66, 42, 251, 0.1)"
                align="center" justify="center" me="12px"
              >
                <Icon as={MdPeople} w="20px" h="20px" color="brand.400" />
              </Flex>
              <Box>
                <Text fontSize="md" fontWeight="bold" color="white">
                  {cliente.nombre} {cliente.apellido || ""}
                </Text>
                <Flex align="center" gap="4px">
                  <Icon as={MdPhone} w="12px" h="12px" color="secondaryGray.600" />
                  <Text fontSize="xs" color="secondaryGray.600">{cliente.phone_number}</Text>
                </Flex>
              </Box>
            </Flex>

            {cliente.ciudad && (
              <Flex align="center" gap="4px" mb="8px">
                <Icon as={MdLocationOn} w="14px" h="14px" color="secondaryGray.600" />
                <Text fontSize="xs" color="secondaryGray.600">{cliente.ciudad}</Text>
              </Flex>
            )}

            <Flex gap="12px" mb="12px">
              <Box flex="1" p="10px" bg="navy.800" borderRadius="8px" textAlign="center">
                <Text fontSize="xl" fontWeight="bold" color="white">{cliente.totalEnvios}</Text>
                <Text fontSize="xs" color="secondaryGray.600">Total</Text>
              </Box>
              <Box flex="1" p="10px" bg="navy.800" borderRadius="8px" textAlign="center">
                <Text fontSize="xl" fontWeight="bold" color="orange.500">{cliente.enviosPendientes}</Text>
                <Text fontSize="xs" color="secondaryGray.600">Pendientes</Text>
              </Box>
            </Flex>

            {cliente.ultimoEnvio && (
              <Flex align="center" gap="4px">
                <Icon as={MdCalendarToday} w="12px" h="12px" color="secondaryGray.600" />
                <Text fontSize="xs" color="secondaryGray.600">
                  Último envío: {new Date(cliente.ultimoEnvio.creado_en).toLocaleDateString("es-EC")}
                </Text>
              </Flex>
            )}
          </Card>
        ))}
        {filtered.length === 0 && (
          <Box gridColumn="1 / -1" textAlign="center" py="60px" color="secondaryGray.600">
            <Icon as={MdPeople} w="48px" h="48px" mb="12px" opacity="0.3" />
            <Text fontSize="lg">No se encontraron clientes</Text>
          </Box>
        )}
      </Grid>
    </Box>
  )
}
