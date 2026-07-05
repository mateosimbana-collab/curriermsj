# CurrierMsj — Sistema de Gestión Courier

## Arquitectura del Sistema

### Stack Tecnológico
- **Backend:** Python 3.12+ / Flask (REST API)
- **Base de Datos:** PostgreSQL v15+ (Supabase)
- **Frontend:** HTML + TailwindCSS + Chart.js + AlpineJS
- **WhatsApp:** Meta Cloud API v20.0
- **Autenticación:** JWT con flask-jwt-extended
- **ORM/DB:** Supabase REST API + SQL directo

### Capas (Clean Architecture)

```
┌─────────────────────────────────────┐
│         interfaces/api              │  ← Rutas Flask, DTOs, Webhooks
├─────────────────────────────────────┤
│         application/                │  ← Casos de uso, servicios
├─────────────────────────────────────┤
│         domain/                     │  ← Entidades, Value Objects, Reglas
├─────────────────────────────────────┤
│         infrastructure/             │  ← Repositorios Supabase, Clientes HTTP
└─────────────────────────────────────┘
```

### Módulos del Sistema

| Módulo | Descripción |
|--------|-------------|
| **Dashboard** | KPIs, gráficas, métricas en tiempo real |
| **Clientes** | Registro, grupos, mayoristas, prospectos |
| **Casilleros** | Gestión de casilleros virtuales |
| **Paquetes** | Recepción, tracking, estados, despacho |
| **Usuarios** | Administradores, roles, permisos |
| **Reportes** | Exportación CSV/XLSX, estadísticas |
| **WhatsApp** | Bot, notificaciones, consultas |
| **Auditoría** | Logs de cambios, trazabilidad |
| **Configuración** | Parámetros del sistema |

### Flujo Principal

```
WhatsApp → Webhook → Bot (procesa mensaje)
                     ↓
              API REST → Supabase
                     ↓
              Responde vía WhatsApp
```

```
Admin → Frontend Dashboard → API REST → Supabase
```

### Base de Datos (Entidades Principales)

```
usuarios ──┐
           ├── clientes ──┬── paquetes ──┬── tracking_events
           │              │              └── imagenes
           │              ├── historial_cambios
           │              └── notificaciones
           │
           ├── grupos_clientes
           ├── mayoristas
           ├── prospectos
           └── casilleros_virtuales
```

### Reglas de Negocio Clave

1. No se usan números de casillero → identificación por nombre + cédula
2. Estados mediante etiquetas configurables
3. Clientes tipo grupo comparten paquetes
4. Cotizaciones solo por operador humano (nunca automáticas)
5. Aprobación obligatoria antes del despacho
6. No interferir con llamadas simultáneas de WhatsApp Business
7. Soft delete en todas las tablas principales
8. Auditoría completa de cambios
