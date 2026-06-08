# Reorganizacion en 4 vistas + Kanban + Alta manual — Plan de implementacion

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir `app_servicios.html` en una app de 4 pestanas (Servicios / Agenda / Kanban / Resumen), con la agenda como pagina propia, un kanban de clientes de dos ejes (estado de gestion + revisado), y un formulario de alta manual que admite clientes nuevos.

**Architecture:** App React 18 + Babel via CDN, sin build. Toda la logica/UI vive en `app_servicios_template.html`; `app_servicios.html` se GENERA con `python generar_app_servicios.py` (sustituye `/*__DATA__*/` por el JSON, una sola linea, asi que la numeracion de lineas plantilla==generado). **Nunca editar `app_servicios.html` a mano.** Se reutilizan las claves localStorage existentes (`K_MAN`, `K_CMETA`); no se anaden nuevas.

**Tech Stack:** React 18 (CDN), Babel standalone (CDN), localStorage. Verificacion con Playwright MCP. Regeneracion con Python 3.14 + openpyxl.

**Nota sobre testing:** El proyecto no tiene framework de tests unitarios (es CDN sin build; anadir Jest/Vitest exigiria un build y choca con la restriccion "solo CDN" y con YAGNI). Por tanto el bucle no es test-unitario-primero sino **verificacion dirigida**: cada tarea (1) edita la plantilla, (2) regenera, (3) verifica en navegador con Playwright contra criterios concretos, (4) commitea. Cada "Step de verificacion" lista los criterios exactos a comprobar.

**Comandos base (PowerShell, working dir = C:\GITHUB\RENOVACIONES):**
- Regenerar: `python generar_app_servicios.py` (espera: `OK -> app_servicios.html`)
- Servir: `python -m http.server 8000` y abrir `http://localhost:8000/app_servicios.html`
- localStorage clave de datos: `renov:*` (las marcas sobreviven a la regeneracion porque van por id/codigo)

---

## Estructura de ficheros

- Modificar: `app_servicios_template.html` (unico fichero de codigo; todas las tareas lo tocan)
- Generado (no editar a mano): `app_servicios.html`
- Sin ficheros nuevos de codigo (el constraint "solo CDN, un fichero" se mantiene)

Anclas de linea actuales en `app_servicios_template.html` (== generado):
- L151: `<script>window.PAYLOAD = /*__DATA__*/;</script>`
- L174-180: `const CLI_ESTADOS = [...]`
- L254-258: `addTarea` / `borrarTarea`
- L321-345: `tareasRender`, `nActivas`, `resumen`, `totalFacturar`
- L377-383: `function addManual(...)`
- L385-397: header + KPIs
- L399-420: barra de filtros + conmutador `vista` (2 botones)
- L481-515: bloque `vista==="resumen"`
- L518-534: `<aside className="tareas">` (agenda como barra lateral)

---

## Task 1: Navegacion de 4 pestanas + Agenda como pagina propia

Convierte el conmutador de 2 a 4 pestanas y mueve la agenda del `<aside>` lateral a su propia vista a ancho completo. Tras esta tarea la app sigue funcionando con Servicios, Agenda y Resumen (Kanban se anade en Task 2).

**Files:**
- Modify: `app_servicios_template.html` (conmutador L417-420; aside L518-534; CSS de `.tareas`)

- [ ] **Step 1: Ampliar el conmutador de vista a 4 pestanas**

Localiza (L417-420):

```jsx
        <span className="seg vista" role="group" aria-label="Vista">
          <button aria-pressed={vista==="servicios"} onClick={()=>setVista("servicios")}>Servicios</button>
          <button aria-pressed={vista==="resumen"} onClick={()=>setVista("resumen")}>Resumen por cliente</button>
        </span>
```

Sustituye por:

```jsx
        <span className="seg vista" role="group" aria-label="Vista">
          <button aria-pressed={vista==="servicios"} onClick={()=>setVista("servicios")}>Servicios</button>
          <button aria-pressed={vista==="agenda"} onClick={()=>setVista("agenda")}>Agenda</button>
          <button aria-pressed={vista==="kanban"} onClick={()=>setVista("kanban")}>Kanban</button>
          <button aria-pressed={vista==="resumen"} onClick={()=>setVista("resumen")}>Resumen</button>
        </span>
```

- [ ] **Step 2: Mover la agenda del aside a su propia vista**

Localiza el bloque completo (L518-534):

```jsx
      <aside className="tareas">
        <h3>
          Agenda de tareas ({nActivas})
          <span className="t-head-actions">
            <label className="chk" style={{paddingTop:0,fontSize:11}}><input type="checkbox" checked={verHechas} onChange={e=>setVerHechas(e.target.checked)} /> ver hechas</label>
            <button className="link" onClick={addTarea}>+ tarea</button>
          </span>
        </h3>
        <ul>
          {tareasRender.length===0 && <li className="muted">Sin tareas. Marca años a facturar (Sí), "Ofrecer mant./bonos" o pulsa "+ tarea".</li>}
          {tareasRender.map((t,i)=>(
            <TaskRow key={t.key||i} t={t}
              nota={tnotas[t.key]||""} setNota={val=>setTnotas(n=>({...n,[t.key]:val}))}
              edit={patch=>editTarea(t,patch)} del={()=>borrarTarea(t)} />
          ))}
        </ul>
      </aside>
```

Y muevelo DENTRO del `<main>`, justo despues del cierre del bloque `vista==="resumen"` (despues de `</div>}` de L515 y antes de `</main>` de L516), convertido a vista condicional:

```jsx
        {vista==="agenda" && <section className="agenda-page">
          <div className="agenda-tools">
            <label className="chk" style={{paddingTop:0}}><input type="checkbox" checked={verHechas} onChange={e=>setVerHechas(e.target.checked)} /> ver hechas</label>
            <button className="btn" onClick={addTarea}>+ tarea</button>
          </div>
          <h3 className="agenda-h">Agenda de tareas ({nActivas})</h3>
          <ul className="agenda-list">
            {tareasRender.length===0 && <li className="muted">Sin tareas. Marca años a facturar (Sí), "Ofrecer mant./bonos" o pulsa "+ tarea".</li>}
            {tareasRender.map((t,i)=>(
              <TaskRow key={t.key||i} t={t}
                nota={tnotas[t.key]||""} setNota={val=>setTnotas(n=>({...n,[t.key]:val}))}
                edit={patch=>editTarea(t,patch)} del={()=>borrarTarea(t)} />
            ))}
          </ul>
        </section>}
```

Elimina por completo el `<aside className="tareas">...</aside>` original.

- [ ] **Step 3: Ajustar CSS — quitar layout de sidebar, anadir estilos de pagina**

Localiza en el `<style>` la regla de `.tareas` (barra lateral). Busca el selector `.tareas` y cualquier `display:grid`/`grid-template-columns` del contenedor padre que reservara columna para el aside. Sustituye la maquetacion de dos columnas por una sola (el `<main>` pasa a ancho completo). Anade al final del `<style>`:

```css
  .agenda-page{max-width:780px}
  .agenda-tools{display:flex;gap:10px;align-items:center;margin-bottom:12px}
  .agenda-h{margin:0 0 8px;font-size:16px}
  .agenda-list{list-style:none;margin:0;padding:0;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
```

Si el contenedor raiz usaba grid de 2 columnas para `main + aside`, cambialo a una sola columna (p.ej. quitar `grid-template-columns` o ponerlo a `1fr`). Verifica visualmente en Step 5 que Servicios ocupa el ancho completo.

- [ ] **Step 4: Regenerar**

Run: `python generar_app_servicios.py`
Expected: `OK -> app_servicios.html` y conteos (Servicios: 197, Clientes: 114, Dominios: 93)

- [ ] **Step 5: Verificar en navegador (Playwright)**

Servir (`python -m http.server 8000`, en background) y navegar a `http://localhost:8000/app_servicios.html`. Comprobar:
1. Hay 4 pestanas: Servicios / Agenda / Kanban / Resumen.
2. Click en "Agenda" muestra la lista de tareas a ancho completo (ya no hay barra lateral fija).
3. Click en "Servicios" y "Resumen" siguen funcionando.
4. Click en "Kanban" no rompe (puede quedar en blanco; se implementa en Task 2).
5. La vista Servicios ocupa el ancho completo (no hay hueco de la antigua barra lateral).

- [ ] **Step 6: Commit**

```powershell
git add app_servicios_template.html app_servicios.html
git commit -m "feat: navegacion de 4 pestanas y agenda como pagina propia"
```

---

## Task 2: Kanban de clientes (dos ejes)

Anade la vista Kanban: 5 columnas por estado de gestion + eje "revisado" independiente, con drag&drop nativo, `<select>` de estado como alternativa accesible, badge de revisado por tarjeta, barra de progreso y filtros.

**Files:**
- Modify: `app_servicios_template.html` (constantes tras L180; estado nuevo en `App`; memo `kanbanData`; componente `Kanban`; vista condicional; CSS)

- [ ] **Step 1: Anadir definicion de columnas del kanban**

Justo despues de `const CLI_ESTADOS = [...]` (tras L180), anade:

```jsx
const KANBAN_COLS = [
  ["",          "Sin clasificar",     "d-sin"],
  ["hablar",    "Hablar con cliente", "d-hab"],
  ["pdte_fact", "Pendiente facturar", "d-pf"],
  ["facturado", "Facturado",          "d-fac"],
  ["terminado", "Terminado",          "d-ter"],
];
```

- [ ] **Step 2: Anadir estado de filtros del kanban en App**

Junto a los demas `useState` de `App` (cerca de L233-239), anade:

```jsx
  const [kbSinRev, setKbSinRev] = useState(false);
  const [kbConEur, setKbConEur] = useState(false);
```

- [ ] **Step 3: Anadir memo `kanbanData`**

Despues del memo `resumen` y `totalFacturar` (tras L345), anade:

```jsx
  const kanbanData = useMemo(()=>{
    const porCod = {};
    resumen.forEach(g=>{ if(g.codigo) porCod[g.codigo] = g; });
    const nServ = {}, nombre = {};
    todos.forEach(s=>{ nServ[s.codigo] = (nServ[s.codigo]||0)+1; if(!nombre[s.codigo]) nombre[s.codigo] = s.cliente; });
    return codigosTodos.map(cod=>{
      const v = cmeta[cod]||{}; const r = porCod[cod]||{};
      return { codigo:cod, cliente:nombre[cod]||cod, nServ:nServ[cod]||0,
               total:r.total||0, prox:r.prox||"", estado:v.estado||"", revisado:!!v.revisado };
    }).sort((a,b)=>a.cliente.localeCompare(b.cliente));
  }, [codigosTodos, cmeta, resumen, todos]);
```

- [ ] **Step 4: Anadir el componente `Kanban`**

Anade un componente nuevo a nivel de fichero (junto a `Servicio` y `TaskRow`, p.ej. tras el cierre de `function App(){...}` o antes de `Servicio`):

```jsx
function Kanban({data, cols, total, nRevisados, sinRev, conEur, setSinRev, setConEur, onEstado, onRevisado}){
  function visible(c){
    if(sinRev && c.revisado) return false;
    if(conEur && !(c.total>0)) return false;
    return true;
  }
  const filt = data.filter(visible);
  const pct = total ? Math.round(100*nRevisados/total) : 0;
  return (
    <section className="kanban">
      <div className="kb-bar">
        <div className="kb-prog">
          <small><b>{nRevisados} / {total}</b> revisados · eje independiente de la columna</small>
          <div className="kb-track"><div className="kb-fill" style={{width:pct+"%"}}></div></div>
        </div>
        <label className="chk"><input type="checkbox" checked={sinRev} onChange={e=>setSinRev(e.target.checked)} /> Solo sin revisar</label>
        <label className="chk"><input type="checkbox" checked={conEur} onChange={e=>setConEur(e.target.checked)} /> Solo con € pendiente</label>
      </div>
      <div className="kb-board">
        {cols.map(([val,label,dot])=>{
          const items = filt.filter(c=>(c.estado||"")===val);
          return (
            <div className="kb-col" key={val||"__sin"}
                 onDragOver={e=>e.preventDefault()}
                 onDrop={e=>{ const cod=e.dataTransfer.getData("text/cod"); if(cod) onEstado(cod, val); }}>
              <h3><span className={"kb-dot "+dot}></span> {label} <span className="kb-count">{items.length}</span></h3>
              {items.map(c=>(
                <div className="kb-card" key={c.codigo} draggable
                     onDragStart={e=>e.dataTransfer.setData("text/cod", c.codigo)}>
                  <div className="kb-nm">{c.cliente} <span className="kb-cod">{c.codigo}</span></div>
                  <div className="kb-meta">
                    <span className="kb-tag">{c.nServ} {c.nServ===1?"servicio":"servicios"}</span>
                    {c.total>0 && <span className="kb-tag eur">{Math.round(c.total)} €</span>}
                    {c.prox && <span className="kb-tag fch">{fmt(c.prox)}</span>}
                  </div>
                  <div className="kb-foot">
                    <label className={"kb-rev "+(c.revisado?"yes":"no")}>
                      <input type="checkbox" checked={c.revisado} onChange={e=>onRevisado(c.codigo, e.target.checked)} />
                      {c.revisado ? "revisado" : "sin revisar"}
                    </label>
                    <select className="kb-sel" value={c.estado||""} onChange={e=>onEstado(c.codigo, e.target.value)} aria-label="Estado del cliente">
                      {cols.map(([v,l])=><option key={v} value={v}>{l}</option>)}
                    </select>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </section>
  );
}
```

Nota: `fmt` es el helper de fecha ya existente en el fichero (usado en Servicio/header). Acepta string ISO o Date.

- [ ] **Step 5: Renderizar la vista Kanban en App**

Junto a las otras vistas en `<main>` (despues del bloque `vista==="agenda"` de Task 1), anade:

```jsx
        {vista==="kanban" && <Kanban
          data={kanbanData} cols={KANBAN_COLS}
          total={codigosTodos.length} nRevisados={nRevisados}
          sinRev={kbSinRev} conEur={kbConEur} setSinRev={setKbSinRev} setConEur={setKbConEur}
          onEstado={(cod,estado)=>setCM(cod,{estado})}
          onRevisado={(cod,val)=>setCM(cod,{revisado:val})} />}
```

- [ ] **Step 6: Anadir CSS del kanban**

Anade al final del `<style>`:

```css
  .kanban{}
  .kb-bar{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:14px}
  .kb-prog{flex:1;min-width:200px;max-width:340px}
  .kb-prog small{color:var(--muted)}
  .kb-track{height:9px;background:#e7ecf3;border-radius:6px;overflow:hidden;margin-top:4px}
  .kb-fill{height:100%;background:var(--blue)}
  .kb-board{display:flex;gap:13px;overflow-x:auto;align-items:flex-start;padding-bottom:6px}
  .kb-col{flex:0 0 240px;background:#eef1f6;border:1px solid var(--line);border-radius:12px;padding:10px;min-height:60px}
  .kb-col > h3{margin:2px 4px 10px;font-size:13px;display:flex;align-items:center;gap:8px;color:#374151}
  .kb-dot{width:9px;height:9px;border-radius:50%}
  .kb-count{margin-left:auto;background:#fff;border:1px solid var(--line);border-radius:20px;font-size:11px;padding:1px 9px;color:var(--muted)}
  .d-sin{background:#9aa4b2}.d-hab{background:#e0a800}.d-pf{background:#1f6feb}.d-fac{background:#16a34a}.d-ter{background:#6b7280}
  .kb-card{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 11px;margin-bottom:9px;box-shadow:0 1px 2px rgba(16,24,40,.04);cursor:grab}
  .kb-card:hover{border-color:#c5d3e8}
  .kb-nm{font-weight:600;font-size:13px}
  .kb-cod{font-size:11px;color:#9aa4b2;font-weight:500}
  .kb-meta{display:flex;gap:6px;flex-wrap:wrap;margin-top:7px;font-size:11px}
  .kb-tag{background:#f3f5f9;border:1px solid var(--line);border-radius:6px;padding:1px 7px;color:#4b5563}
  .kb-tag.eur{background:#eafaf0;border-color:#bbe7cb;color:#15803d}
  .kb-tag.fch{background:#fff4e5;border-color:#ffd9a8;color:#b45309}
  .kb-foot{display:flex;align-items:center;gap:8px;margin-top:9px;justify-content:space-between}
  .kb-rev{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;padding:2px 8px;border-radius:20px}
  .kb-rev.yes{background:#e7f6ec;color:#15803d;border:1px solid #bbe7cb}
  .kb-rev.no{background:#fdeced;color:#b42318;border:1px solid #f5c2c7}
  .kb-sel{font-size:11px;padding:3px 5px}
```

Si `--blue`/`--line`/`--muted` no existen como variables CSS en el fichero, usar los valores literales correspondientes ya usados en el resto del `<style>` (revisar la cabecera del bloque de estilos).

- [ ] **Step 7: Regenerar**

Run: `python generar_app_servicios.py`
Expected: `OK -> app_servicios.html`

- [ ] **Step 8: Verificar en navegador (Playwright)**

Navegar a `http://localhost:8000/app_servicios.html`, pestana Kanban. Comprobar:
1. Se ven 5 columnas: Sin clasificar / Hablar con cliente / Pendiente facturar / Facturado / Terminado.
2. Hay tarjetas de cliente con nombre, codigo, nº de servicios; algunas con € y fecha.
3. Barra de progreso "X / N revisados" arriba.
4. **Drag&drop:** arrastrar una tarjeta de "Sin clasificar" a "Hablar con cliente". La tarjeta cambia de columna. Recargar la pagina (F5) -> la tarjeta sigue en "Hablar con cliente" (persistencia via `cmeta`).
5. **Select fallback:** cambiar el estado de una tarjeta con el `<select>` -> se mueve de columna.
6. **Eje revisado:** marcar el check de revisado de una tarjeta que esta en "Pendiente facturar" -> el badge pasa a "revisado" y el contador de progreso sube, sin cambiar de columna.
7. **Filtros:** "Solo sin revisar" oculta las revisadas; "Solo con € pendiente" deja solo las que tienen €.

- [ ] **Step 9: Commit**

```powershell
git add app_servicios_template.html app_servicios.html
git commit -m "feat: kanban de clientes con dos ejes (estado de gestion + revisado)"
```

---

## Task 3: Alta manual con formulario + clientes nuevos

Sustituye el `prompt()` de alta manual por un formulario en modal que permite anadir un servicio a un cliente existente o crear un cliente nuevo (no presente en FactuSol).

**Files:**
- Modify: `app_servicios_template.html` (estado de modal en App; handler `addServicioManual`; componente `AltaManualForm`; boton que abre el modal; CSS)

- [ ] **Step 1: Anadir estado del modal en App**

Junto a los demas `useState` de `App`:

```jsx
  const [modalAlta, setModalAlta] = useState(false);
```

- [ ] **Step 2: Anadir el handler `addServicioManual` en App**

Sustituye la funcion existente `addManual` (L377-383):

```jsx
  function addManual(codigo, cliente){
    const tipo = prompt("Servicio (tipo):"); if(!tipo) return;
    const id = "MAN__"+codigo+"__"+Date.now();
    setManual(ms=>[...ms, {id, codigo, cliente, tipo, origen:"Manual",
      anios:{}, kd_inicio:null, ultima_fecha:null, uso_hasta_def:"", importe_sug:0, estado:"alta manual"}]);
    setOpen(o=>({...o,[id]:true}));
  }
```

por:

```jsx
  function addServicioManual({modo, codigo, cliente, tipo, periodicidad, importe, fecha}){
    const nuevo = modo==="nuevo";
    const cod = nuevo ? ("MAN-"+Date.now()) : codigo;
    const nom = nuevo ? cliente : cliente;
    const id = "MAN__"+cod+"__"+Date.now();
    setManual(ms=>[...ms, {id, codigo:cod, cliente:nom, tipo, origen:"Manual",
      anios:{}, kd_inicio:null, ultima_fecha:fecha||null, uso_hasta_def:"",
      importe_sug:Number(importe)||0, periodicidad:periodicidad||"anual", estado:"alta manual"}]);
    setOpen(o=>({...o,[id]:true}));
    setModalAlta(false);
  }
```

Nota: la firma de `addManual` antigua (codigo, cliente) ya no se usa; revisa que no quede ninguna llamada `addManual(...)` colgando. Si existe un boton "+ servicio" por cliente que llamaba a `addManual`, redirigelo a abrir el modal con el cliente preseleccionado (Step 5) o, de forma minima, a `setModalAlta(true)`.

- [ ] **Step 3: Anadir lista de clientes para el desplegable**

En `App`, junto a otros memos, anade:

```jsx
  const clientesLista = useMemo(()=>{
    const m = {};
    todos.forEach(s=>{ if(!m[s.codigo]) m[s.codigo] = s.cliente; });
    return Object.entries(m).map(([codigo,cliente])=>({codigo,cliente})).sort((a,b)=>a.cliente.localeCompare(b.cliente));
  }, [todos]);
```

- [ ] **Step 4: Anadir el componente `AltaManualForm`**

A nivel de fichero (junto a `Kanban`):

```jsx
function AltaManualForm({clientes, onClose, onAdd}){
  const [modo, setModo] = useState("existente");
  const [codigo, setCodigo] = useState("");
  const [nuevoNom, setNuevoNom] = useState("");
  const [tipo, setTipo] = useState("");
  const [periodicidad, setPeriodicidad] = useState("anual");
  const [importe, setImporte] = useState("");
  const [fecha, setFecha] = useState("");
  function submit(e){
    e.preventDefault();
    if(!tipo.trim()) return;
    if(modo==="existente" && !codigo) return;
    if(modo==="nuevo" && !nuevoNom.trim()) return;
    const cli = modo==="existente" ? (clientes.find(c=>c.codigo===codigo)||{}).cliente : nuevoNom.trim();
    onAdd({modo, codigo, cliente:cli, tipo:tipo.trim(), periodicidad, importe, fecha});
  }
  return (
    <div className="ov on" onMouseDown={e=>{ if(e.target.classList.contains("ov")) onClose(); }}>
      <form className="modal" onSubmit={submit}>
        <h3>Añadir servicio manual</h3>
        <div className="fld">
          <label>Cliente</label>
          <select value={modo==="nuevo"?"__new":codigo} onChange={e=>{
            if(e.target.value==="__new"){ setModo("nuevo"); }
            else { setModo("existente"); setCodigo(e.target.value); }
          }}>
            <option value="">— elegir cliente existente —</option>
            {clientes.map(c=><option key={c.codigo} value={c.codigo}>{c.cliente} ({c.codigo})</option>)}
            <option value="__new">+ Cliente nuevo (no está en FactuSol)…</option>
          </select>
        </div>
        {modo==="nuevo" && <div className="fld">
          <label>Nombre del cliente nuevo</label>
          <input value={nuevoNom} onChange={e=>setNuevoNom(e.target.value)} placeholder="Ej. CARPINTERÍAS DEL SUR" autoFocus />
        </div>}
        <div className="fld"><label>Servicio (tipo)</label>
          <input value={tipo} onChange={e=>setTipo(e.target.value)} placeholder="Ej. Mantenimiento web" /></div>
        <div className="fld"><label>Periodicidad</label>
          <select value={periodicidad} onChange={e=>setPeriodicidad(e.target.value)}>
            <option value="anual">Anual</option><option value="mensual">Mensual</option><option value="puntual">Puntual</option>
          </select></div>
        <div className="fld"><label>Importe sugerido (€)</label>
          <input type="number" value={importe} onChange={e=>setImporte(e.target.value)} placeholder="0" /></div>
        <div className="fld"><label>Fecha de referencia</label>
          <input type="date" value={fecha} onChange={e=>setFecha(e.target.value)} /></div>
        <div className="acts">
          <button type="button" className="btn ghost" onClick={onClose}>Cancelar</button>
          <button type="submit" className="btn">Añadir</button>
        </div>
      </form>
    </div>
  );
}
```

- [ ] **Step 5: Anadir boton de apertura + render del modal**

En la barra de herramientas de la vista Servicios (cerca del conmutador / filtros, L399-420), anade un boton:

```jsx
        <button className="btn" onClick={()=>setModalAlta(true)}>+ Añadir servicio manual</button>
```

Y al final del JSX de `App` (antes del cierre `</div>` del return principal), anade el render condicional del modal:

```jsx
      {modalAlta && <AltaManualForm
        clientes={clientesLista}
        onClose={()=>setModalAlta(false)}
        onAdd={addServicioManual} />}
```

- [ ] **Step 6: Anadir CSS del modal**

Al final del `<style>`:

```css
  .ov{position:fixed;inset:0;background:rgba(15,23,42,.45);display:flex;align-items:center;justify-content:center;padding:20px;z-index:50}
  .modal{background:#fff;border-radius:14px;width:100%;max-width:440px;padding:20px 22px;box-shadow:0 20px 50px rgba(0,0,0,.3)}
  .modal h3{margin:0 0 14px;font-size:17px}
  .fld{margin-bottom:12px}
  .fld label{display:block;font-size:12px;font-weight:600;color:#374151;margin-bottom:5px}
  .fld input,.fld select{width:100%}
  .modal .acts{display:flex;gap:9px;justify-content:flex-end;margin-top:8px}
  .btn.ghost{background:#fff;color:var(--blue);border:1px solid #cdddf5}
```

Si la clase `.btn` no existe en el fichero, revisa como se estilan los botones actuales (`.link`, etc.) y reutiliza esa convencion en lugar de `.btn`.

- [ ] **Step 7: Regenerar**

Run: `python generar_app_servicios.py`
Expected: `OK -> app_servicios.html`

- [ ] **Step 8: Verificar en navegador (Playwright)**

Navegar a `http://localhost:8000/app_servicios.html`, pestana Servicios. Comprobar:
1. Boton "+ Añadir servicio manual" abre un modal.
2. **Cliente existente:** elegir un cliente del desplegable, escribir tipo "Prueba mantenimiento", importe 99, Añadir. El modal se cierra y el servicio aparece bajo ese cliente en Servicios.
3. **Cliente nuevo:** abrir de nuevo, elegir "+ Cliente nuevo…", escribir nombre "CARPINTERÍAS TEST", tipo "Web", Añadir. Aparece un cliente nuevo en Servicios con codigo `MAN-...`.
4. Ir a Kanban -> el cliente nuevo aparece como tarjeta en "Sin clasificar".
5. Ir a Resumen -> si el servicio nuevo genera tarea de facturar, aparece; si no, al menos no rompe.
6. Recargar (F5) -> los servicios/clientes manuales persisten (via `K_MAN`).
7. Cancelar / click fuera del modal lo cierra sin anadir nada.

- [ ] **Step 9: Commit**

```powershell
git add app_servicios_template.html app_servicios.html
git commit -m "feat: alta manual con formulario en modal y soporte de clientes nuevos"
```

---

## Task 4: Verificacion integral + limpieza

Pasada final de regresion sobre las 4 vistas y persistencia, y limpieza de mockups.

**Files:**
- Modify: ninguno de codigo (solo verificacion). Posible borrado de mockups.

- [ ] **Step 1: Regresion completa (Playwright)**

Con la app servida, recorrer:
1. Las 4 pestanas cargan sin errores de consola.
2. Servicios: decidir un año (Sí) en un servicio -> genera tarea en Agenda.
3. Agenda: marcar una tarea como hecha -> con "ver hechas" off desaparece; on reaparece tachada.
4. Kanban: drag de una tarjeta + marcar revisado; F5 -> ambos persisten.
5. Resumen: el total a facturar refleja las tareas de facturar activas.
6. Export (`decisiones_renovaciones.json`): descarga e incluye `clientes` con estado/revisado.

- [ ] **Step 2: Revisar consola del navegador**

Run (Playwright): leer mensajes de consola. Expected: sin errores rojos (warnings de React en modo dev son tolerables).

- [ ] **Step 3: Limpieza de mockups (opcional, confirmar con Jero)**

Los mockups `mockup_kanban.html` y `mockup_app.html` cumplieron su funcion. Preguntar a Jero si se borran o se conservan. Si se borran:

```powershell
git rm mockup_kanban.html mockup_app.html
git commit -m "chore: eliminar mockups de diseno ya implementados"
```

- [ ] **Step 4: Push**

```powershell
git push
```

---

## Self-review (cobertura del spec)

- Navegacion 4 pestanas -> Task 1 Step 1.
- Agenda como pagina -> Task 1 Steps 2-3.
- Kanban dos ejes (5 columnas, drag&drop, select fallback, revisado, progreso, filtros) -> Task 2.
- Alta manual formulario + clientes nuevos -> Task 3.
- Regeneracion con Python + verificacion Playwright + commits -> en cada tarea.
- Sin claves localStorage nuevas (reutiliza `K_MAN`, `K_CMETA`) -> Tasks 2 y 3.
- Sin emojis en codigo; indicadores con CSS -> Task 2 Step 6 (puntos de color).
- Fuera de alcance (Coda, toner, Asktivia) -> no hay tareas, correcto.
