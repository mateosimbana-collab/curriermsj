import React, { Suspense } from "react"
import { Icon } from "@chakra-ui/react"
import { MdHome, MdPeople, MdSchedule, MdWarning, MdSecurity } from "react-icons/md"
import {
  MainDashboard,
  ObservabilityDashboard,
  ClientesDashboard,
  PendientesDashboard,
  ReportesDashboard,
} from "views/lazy"

const page = (Component) => (
  <Suspense fallback={null}>
    <Component />
  </Suspense>
)

const routes = [
  {
    name: "Main Dashboard",
    layout: "/admin",
    path: "/default",
    icon: <Icon as={MdHome} width="20px" height="20px" color="inherit" />,
    component: page(MainDashboard),
  },
  {
    name: "Clientes",
    layout: "/admin",
    path: "/clientes",
    icon: <Icon as={MdPeople} width="20px" height="20px" color="inherit" />,
    component: page(ClientesDashboard),
  },
  {
    name: "Envíos",
    layout: "/admin",
    path: "/pendientes",
    icon: <Icon as={MdSchedule} width="20px" height="20px" color="inherit" />,
    component: page(PendientesDashboard),
  },
  {
    name: "Reportes",
    layout: "/admin",
    path: "/reportes",
    icon: <Icon as={MdWarning} width="20px" height="20px" color="inherit" />,
    component: page(ReportesDashboard),
  },
  {
    name: "Observabilidad",
    layout: "/admin",
    path: "/observability",
    icon: <Icon as={MdSecurity} width="20px" height="20px" color="inherit" />,
    component: page(ObservabilityDashboard),
  },
]

export default routes
