import { lazy } from "react"

export const MainDashboard = lazy(() => import("views/admin/default"))
export const ObservabilityDashboard = lazy(() => import("views/admin/observability"))
export const ClientesDashboard = lazy(() => import("views/admin/clientes"))
export const PendientesDashboard = lazy(() => import("views/admin/pendientes"))
export const ReportesDashboard = lazy(() => import("views/admin/reportes"))
