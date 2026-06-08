# Herramienta de Marcado de Renovaciones — Entreredes

Herramienta local para clasificar conceptos de facturas historicas (FactuSol)
de cara a regularizar servicios recurrentes y renovaciones pendientes.
Es la fase previa al modulo de Renovaciones de Asktivia: lo que se marca aqui
es la fuente de verdad para generar despues `servicios_contratados`,
`periodos_facturacion` y `reglas_clasificacion`.

## Entidad
Todos los datos son de `jero_autonomo` (JERONIMO YUGO SANCHEZ).
NUNCA mezclar con `entreredes_sl`. Si se anaden datos de la S.L., separar por
`entidad_emisora`.

## Archivos
- `index.html` — app (React 18 + Babel via CDN, sin build). Toda la logica y estilos aqui.
- `renovaciones_data.json` — datos de entrada: 135 clientes, 522 facturas, 773 lineas.
  Generado por parser de los 3 Excel FactuSol (2022-2024). NO editar a mano.
- `marcas.json` — export de las marcas del usuario (se descarga desde la app).
- `CLAUDE.md` — este archivo.

## Como ejecutar (local)
    php -S localhost:8000
    # abrir http://localhost:8000
Abrir el HTML con doble clic NO funciona (el fetch del JSON requiere servidor).
Tambien vale: `python3 -m http.server 8000`.

## Modelo de datos (renovaciones_data.json)
Cliente: { codigo, nombre, nif, anios[], total, n_facturas, n_lineas, facturas[] }
Factura: { fecha, anio, num, total, lineas[] }
Linea:   { id, desc, importe, sug }   // sug = "renov:<tipo>" | "conciliar" | "no" | null

El `codigo` es el codigo de cliente de FactuSol (viene en el prefijo del campo
Cliente, ej. "000331-DACRIDENTAL S.L"). Es la clave de matching dentro de FactuSol
(sin matching difuso). El NIF solo aparece en facturas de 2024 (formato variante B).

## Variantes de formato FactuSol (para el parser, no para la app)
- Variante A (2022, 2023): sin columna N.I.F., con Alm./Est./For. pag.
- Variante B (2024): con columna N.I.F., sin esas columnas.
La deteccion es por la fila de cabecera (presencia de "N.I.F."), NO por el anio.

## Marcas (lo que produce el usuario)
Tres acciones por linea:
- renov     — servicio recurrente. Campos: tipo, uso_hasta (fecha), estado (activo|baja)
- conciliar — venta de consumible (toner) a cruzar con pedidos del mayorista. Campo: mayorista
- no        — no facturable (KD subvencionado, comisiones, trabajos sueltos)

Export (marcas.json): array de
{ codigo, cliente, fecha, desc, importe, accion, tipo, uso_hasta, estado, mayorista }

Persistencia en navegador: localStorage, clave `renov:marcas3`.

## Fuentes pendientes de integrar (otras bolsas, NO estan en FactuSol)
- Incidencias/averias arregladas sin facturar -> export de Coda (cada incidencia
  = concepto puntual facturable con fecha y cliente).
- Pedidos del mayorista de toner -> para el cruce de conciliacion.

## Convenciones Entreredes
- Sin emojis en codigo.
- WCAG 2.1 AA si esto evoluciona a vista de cara a usuario.
- Validacion fiscal: Sara (DAE) valida que periodos 2022-2024 se pueden emitir
  antes de cualquier facturacion masiva. La accion "no" cubre lo que no procede.

## Aviso EU AI Act
La sugerencia automatica (campo `sug`) es un clasificador regex en cascada,
riesgo minimo. La decision final es siempre humana (el usuario marca/confirma).
