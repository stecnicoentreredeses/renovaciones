# Diseno — Reorganizacion en 4 vistas + Kanban de clientes + Alta manual

Fecha: 2026-06-08
Proyecto: RENOVACIONES (herramienta de marcado de renovaciones, jero_autonomo)
Estado: aprobado, pendiente de plan de implementacion

## Objetivo

Reorganizar `app_servicios.html` para que el flujo de trabajo principal sea:
dar de alta servicios manualmente, gestionar la agenda de tareas en su propia
pagina, y tener una vista tipo kanban del estado de revision de cada cliente.

## Contexto / arquitectura existente

- App de una sola pagina, React 18 + Babel via CDN, sin build.
- `app_servicios.html` es un fichero GENERADO. La fuente real es
  `app_servicios_template.html`. `generar_app_servicios.py` sustituye el
  marcador `/*__DATA__*/` de la plantilla por el JSON de datos y escribe
  `app_servicios.html`. **Nunca se edita el HTML generado a mano** (se
  sobrescribe en la siguiente regeneracion).
- Componentes actuales: `App`, `Servicio`, `TaskRow`.
- Conmutador de vista actual: estado `vista` con valores `servicios` | `resumen`.
- La agenda es hoy un `<aside className="tareas">` siempre visible (barra lateral).
- Persistencia en localStorage (claves existentes, se reutilizan):
  - `K_MARKS` decisiones por servicio
  - `K_MAN` servicios manuales (array)
  - `K_TNOTAS` notas de tareas
  - `K_CMETA` metadatos por cliente: `revisado` (bool), `estado` (string), `collapsed`
  - `K_TOV` overrides de tareas auto-generadas
  - `K_TMAN` tareas manuales
  - `K_TOOLS` herramientas
- `CLI_ESTADOS` = ["", hablar, pdte_fact, facturado, terminado].
- `addManual(codigo, cliente)` da de alta un servicio a un cliente existente con `prompt()`.

## Alcance del cambio

### 1. Navegacion — 4 pestanas

- El conmutador `vista` pasa de 2 a 4 valores:
  `servicios` | `agenda` | `kanban` | `resumen`.
- La barra de KPIs de la cabecera se mantiene (es global): servicios, decididos,
  sin decidir, clientes revisados, tareas activas.
- Solo una vista visible a la vez.

### 2. Agenda como pagina propia

- Se elimina el `<aside className="tareas">` siempre visible.
- Su contenido pasa a renderizarse en `{vista==="agenda" && ...}` a ancho completo.
- Se reutilizan sin cambios de logica: `TaskRow`, `tareasRender`, filtro
  "ver hechas", boton "+ tarea", notas por tarea, marcado de hecha, override y borrado.
- Solo cambia la ubicacion y el ancho (de sidebar a pagina).

### 3. Kanban de clientes — dos ejes separados

Dos ejes independientes:
- **Eje columna** = estado de gestion del cobro.
- **Eje revisado** = progreso de revision (badge por tarjeta + barra de progreso global).

Columnas (5): `Sin clasificar` (sin estado) + las 4 de `CLI_ESTADOS`:
`Hablar con cliente`, `Pendiente facturar`, `Facturado`, `Terminado`.

- Se agrupan todos los codigos de cliente (`codigosTodos`) por `cmeta[cod].estado`.
  Los que no tienen estado caen en "Sin clasificar".
- Cada tarjeta muestra: nombre, codigo, nº de servicios, € pendiente (suma de
  tareas de tipo "facturar" del cliente), proxima fecha de renovacion, y badge
  `✓ revisado` / `○ sin revisar`.
- Drag & drop nativo HTML5 (sin librerias, se respeta la restriccion "solo CDN"):
  arrastrar una tarjeta a otra columna ejecuta `setCM(cod, {estado})`.
- Alternativa accesible (teclado / sin arrastrar): cada tarjeta lleva un `<select>`
  de estado equivalente al drag.
- El check de `revisado` se marca por tarjeta (independiente de la columna).
- Barra superior del kanban: progreso "X/total revisados" + filtros
  "solo sin revisar" y "solo con € pendiente".

### 4. Alta manual — formulario + clientes nuevos

- Se sustituye el `prompt()` de `addManual` por un formulario en modal (overlay
  centrado, como en el mockup `mockup_app.html`).
- Campos: cliente (elegir existente **o** "cliente nuevo" -> nombre libre),
  tipo de servicio, periodicidad (anual/mensual/puntual), importe sugerido, fecha de referencia.
- Un **cliente nuevo** (no presente en FactuSol) se modela como un servicio manual
  con un codigo sintetico (ej. `MAN-<timestamp>`), de modo que aparece igual que
  cualquier otro cliente en Servicios, Kanban y Resumen (el agrupado es por codigo).
- Se persiste en `K_MAN`. Su `cmeta` (estado/revisado) funciona por codigo, asi que
  el cliente nuevo tambien tiene tarjeta en el kanban.

## Modelo de datos

- No se anaden claves nuevas de localStorage. Se reutilizan `K_MAN` y `K_CMETA`.
- El objeto de servicio manual ya lleva `cliente`, `codigo`, `tipo`, `origen`,
  `importe_sug`, `anios`, etc. El formulario rellena estos campos.

## Componentes / organizacion

- `App` (existente): gestiona estado y conmuta entre las 4 vistas.
- `Servicio` (existente): sin cambios funcionales.
- `TaskRow` (existente): reutilizado en la vista Agenda y en Resumen.
- `Kanban` (nuevo): recibe codigos agrupados + handlers; renderiza columnas y tarjetas.
- `AltaManualForm` (nuevo): formulario controlado para alta de servicio/cliente.

## Regeneracion y verificacion

1. Editar `app_servicios_template.html`.
2. Regenerar: `python generar_app_servicios.py` (requiere Python + openpyxl).
   (Confirmar quien lo ejecuta: agente o Jero).
3. Servir local: `php -S localhost:8000` o `python -m http.server 8000`.
4. Verificacion con Playwright:
   - Cambiar entre las 4 pestanas.
   - Arrastrar una tarjeta del kanban a otra columna -> el estado persiste tras recargar.
   - Marcar/desmarcar revisado en una tarjeta -> persiste, independiente de la columna.
   - Alta de cliente nuevo via formulario -> aparece en Servicios, Kanban y Resumen.
5. Commit en git.

## Riesgos y notas

- Drag & drop nativo en React requiere manejar `onDragStart` / `onDragOver` /
  `onDrop` con cuidado; sin libreria para mantener el "solo CDN".
- Las marcas en localStorage estan keyed por id/codigo, por lo que sobreviven a la
  regeneracion del HTML.
- Cumplimiento: herramienta interna de Jero; WCAG 2.1 AA es aspiracional (el
  `<select>` de estado por tarjeta cubre la alternativa por teclado al drag).
- Sin emojis en codigo (convencion del proyecto). Los indicadores visuales del
  kanban/agenda se hacen con CSS (puntos de color), no con emojis.

## Fuera de alcance (YAGNI)

- Integracion de incidencias de Coda.
- Cruce de pedidos del mayorista de toner.
- Volcado del export a Asktivia.
