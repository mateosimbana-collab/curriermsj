# CurrierMsj: instrucciones para agentes

Estas reglas aplican a todo el repositorio. Su objetivo es integrar nuevas versiones sin repetir eliminaciones de funcionalidades que parecen no tener callers estaticos.

## CodeGraph primero

Si existe `.codegraph/`, usa CodeGraph antes de `rg`, lectura masiva o cambios estructurales:

```powershell
codegraph sync
codegraph status
codegraph explore "entrypoints, rutas y superficies activas"
codegraph explore "blast radius de los simbolos que van a cambiar"
```

Despues de editar codigo, ejecuta `codegraph sync` y confirma `codegraph status`.

No guardes documentacion manual dentro de `.codegraph/`. Es un indice local, regenerable e ignorado por Git. Las decisiones permanentes pertenecen a `README.md`, `docs/` y este archivo.

## Estrategia de actualizacion

1. Registra `git status`, commit actual y diff contra la rama entrante.
2. Usa mayoritariamente la implementacion nueva cuando mejora la UI o arquitectura.
3. Conserva contratos, endpoints, scripts y paneles existentes hasta demostrar reemplazo funcional.
4. Corrige errores y seguridad en el punto compartido con menor duplicacion.
5. Mantiene cambios pequenos y compatibles; minimalismo no significa borrar superficies soportadas.
6. Documenta fuente, decisiones, migraciones e incompatibilidades en el README.

## Superficies protegidas

- `run.py`: plataforma unificada con JWT.
- `bot-mensajeria/app.py`: servidor operativo legado.
- `frontend/index.html`: panel administrativo unificado.
- `dashboard/index.html`: dashboard HTML ejecutado por Vite.
- `dashboard/react.html`: entrada del dashboard React.
- `dashboard/owner.html` y `dashboard/support.html`: paneles servidos por Flask.
- `bot-mensajeria/web/routes.py`: webhook y APIs historicas.
- `bot-mensajeria/services/supabase_repository.py`: adaptador entre bot y esquema unificado.
- `database/migrations/`: esquema nuevo aplicado en orden.
- `bot-mensajeria/supabase_schema.sql`: esquema historico conservado.
- Scripts `.bat`, migradores, cargadores, pruebas, documentos y `registro.txt`.

No elimines una superficie protegida sin aprobacion explicita, reemplazo, migracion y pruebas equivalentes.

## Codigo zombie

Un simbolo puede eliminarse solo cuando se cumplen todas estas condiciones:

1. CodeGraph no muestra callers ni dispatch dinamico.
2. `rg` no muestra imports, rutas, nombres de archivo o referencias de configuracion.
3. No es entrypoint, ruta decorada, HTML, componente lazy, SQL, script, prueba, fixture o documento.
4. La suite completa pasa sin reducir cobertura para ocultar la eliminacion.
5. El README no lo define como contrato o compatibilidad vigente.

No conviertas todas las funciones en anonimas. Conserva nombres para rutas, decoradores, trazas, pruebas y logica de dominio. Usa funciones flecha o anonimas cuando realmente reduzcan codigo sin perder observabilidad.

## Seguridad innegociable

- JWT y roles protegen la API administrativa unificada.
- HTTP Basic protege paneles y APIs historicas.
- El webhook POST exige firma HMAC de Meta.
- Tracking publico devuelve una allowlist sin PII.
- No hay secretos, IDs reales ni versiones sensibles predeterminadas en codigo.
- `service_role` nunca llega al navegador.
- CORS usa origenes exactos y credenciales solo cuando se configuran.
- HTML dinamico usa `safe-html.js`, `textContent`, `x-text` o JSX escapado.
- RLS, permisos RPC, integridad e indices no se rebajan para hacer pasar una prueba.

## Base de datos

- Instalacion nueva: aplica `001`, `002`, `003`, `004` y `005` en orden.
- Base desplegada: crea una migracion adicional; no reescribas historia sin plan aprobado.
- Haz backup y preflight antes de indices, deletes o cambios de claves foraneas.
- Mantiene 3FN practica; documenta caches y fotografias historicas desnormalizadas.
- Conserva compatibilidad hasta terminar y verificar `database/migrate_old_data.py`.

## Verificacion minima

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check backend bot-mensajeria database run.py
.\.venv\Scripts\python.exe -m compileall -q backend bot-mensajeria database run.py
npm run lint --prefix dashboard
npm run build --prefix dashboard
.\.venv\Scripts\python.exe -m pip_audit -r backend\requirements.txt
.\.venv\Scripts\python.exe -m pip_audit -r bot-mensajeria\requirements.txt
npm audit --prefix dashboard
git diff --check
codegraph sync
codegraph status
```

Actualiza `README.md`, `docs/ARCHITECTURE.md`, ejemplos de entorno y diagramas cuando cambie arquitectura, API, seguridad, base o despliegue.
