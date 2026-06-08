# -*- coding: utf-8 -*-
"""
Informe servicios x anios — RENOVACIONES (jero_autonomo)
Lee renovaciones_data.json y genera informe_servicios.html (solo lectura).
NO modifica los datos. Reglas KD: 12 meses bono, 24 meses solo Procesos.
"""
import json, re, html
from datetime import date
from collections import defaultdict

HOY = date(2026, 6, 8)
ANIOS = [2022, 2023, 2024, 2025, 2026]
DATA = "renovaciones_data.json"
OUT = "informe_servicios.html"

# --- Mapeo categoria KD -> (servicio, meses_bono) ---
# 24 meses solo Procesos; resto 12.
def clasificar_kd(desc):
    u = desc.upper()
    if "PUESTO DE TRABAJO" in u or "LENOVO" in u or "THINKBOOK" in u:
        return None  # hardware, compra unica, no recurrente
    if "PROCESO" in u or "FACTURA ELECTRON" in u or "FACTURA-E" in u:
        return ("Getradi/Dolibarr (ERP)", 24)
    if "CLIENTE" in u:
        return ("Getradi/Dolibarr (CRM)", 12)
    if "COMERCIO" in u:
        return ("Web/Tienda (dominio+hosting)", 12)
    if "SITIO WEB" in u or "PAGINA WEB" in u or "PRESENCIA" in u:
        return ("Web (dominio+hosting)", 12)
    if "RED" in u and "SOCIAL" in u or "RRSS" in u:
        return ("Gestion RRSS", 12)
    if "BI" in u or "BUSINES" in u or "ANALITIC" in u or "ANALÍTIC" in u:
        return ("Business Intelligence", 12)
    if "OFICINA" in u:
        return ("M365 / Oficina", 12)
    if "CIBERSEG" in u or "ANTIMALWARE" in u or "ANTISPAM" in u or "ANTIPHIS" in u:
        return ("Ciberseguridad", 12)
    if "COMUNICAC" in u and "SEGUR" in u:
        return ("Comunicaciones seguras (VPN)", 12)
    if "SEO" in u:
        return ("Web (dominio+hosting)", 12)
    return ("KD (categoria sin mapear)", 12)

# --- Deteccion recurrente no-KD por palabra clave ---
# orden importa: primera que casa, gana.
RECUR_KW = [
    ("Backup",                 ["BACKUP", "COPIA DE SEGURIDAD", "COPIAS DE SEGURIDAD"]),
    ("Hosting/Dominio",        ["HOSTING", "DOMINIO", "WORDPRESS", "PLESK"]),
    ("Antivirus/Seguridad",    ["ANTIVIRUS", "ANTIMALWARE", "ESET", "DEFENDER"]),
    ("Licencias",              ["LICENCIA", "OFFICE 365", "M365", "ESCRITORIO REMOTO", "365"]),
    ("Mantenimiento",          ["MANTENIMIENTO"]),
    ("Renting/Copias impresora", ["CUOTA IMPRESORA", "COPIAS BLANCO", "COPIAS COLOR", "CONTADOR", "CUOTA 3"]),
    ("Servidor remoto",        ["SERVIDOR REMOTO", "COSTE SERVIDOR"]),
    ("Correo",                 ["CORREO ELECTRONICO", "BUZON", "GOOGLE WORKSPACE"]),
]

def clasificar_recurrente(desc):
    u = desc.upper()
    for nombre, kws in RECUR_KW:
        for k in kws:
            if k in u:
                return nombre
    return None  # puntual / no recurrente

def parse_fecha(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None

def add_months(d, months):
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, 28))

def main():
    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    clientes = data if isinstance(data, list) else data.get("clientes", data)

    informe = []          # por cliente
    tot_pendiente_eur = 0.0
    tot_kd_vencidos = 0
    catalogo = defaultdict(lambda: {"n": 0, "ej": ""})

    for c in clientes:
        # servicio -> {anios:{anio:importe}, origen, kd_inicio, kd_servicio}
        servicios = {}
        for f in c.get("facturas", []):
            anio = f.get("anio")
            fdate = parse_fecha(f.get("fecha"))
            for l in f.get("lineas", []):
                desc = str(l.get("desc", "")).strip()
                imp = l.get("importe") or 0
                if not desc:
                    continue
                up = desc.upper()
                if up.startswith("KD"):
                    kd = clasificar_kd(desc)
                    if kd is None:
                        continue  # hardware
                    serv, meses = kd
                    key = ("KD:" + serv)
                    s = servicios.setdefault(key, {"nombre": serv, "origen": "KD",
                                                    "anios": defaultdict(float),
                                                    "kd_inicio": None, "meses": meses})
                    if fdate:
                        ini = add_months(fdate, meses)
                        if s["kd_inicio"] is None or ini < s["kd_inicio"]:
                            s["kd_inicio"] = ini
                    catalogo["KD: " + serv]["n"] += 1
                    if not catalogo["KD: " + serv]["ej"]:
                        catalogo["KD: " + serv]["ej"] = desc[:60]
                else:
                    rec = clasificar_recurrente(desc)
                    if rec is None:
                        continue
                    key = ("REC:" + rec)
                    s = servicios.setdefault(key, {"nombre": rec, "origen": "Recurrente",
                                                   "anios": defaultdict(float),
                                                   "kd_inicio": None, "meses": None})
                    if anio:
                        s["anios"][anio] += float(imp)
                    catalogo[rec]["n"] += 1
                    if not catalogo[rec]["ej"]:
                        catalogo[rec]["ej"] = desc[:60]

        if not servicios:
            continue

        filas = []
        for key, s in sorted(servicios.items()):
            estado = ""
            pendiente_eur = 0.0
            anios_imp = {a: s["anios"].get(a, 0.0) for a in ANIOS}

            if s["origen"] == "KD":
                ini = s["kd_inicio"]
                if ini:
                    estado = "Bono hasta %s" % ini.isoformat()
                    if ini <= HOY:
                        estado += "  → VENCIDO: verificar activacion + facturar"
                        tot_kd_vencidos += 1
                        s["_vencido"] = True
            else:
                # hueco: anios con facturacion entre el primero y HOY que faltan
                con_imp = [a for a in ANIOS if anios_imp[a] > 0]
                if con_imp:
                    ultimo = max(con_imp)
                    ult_imp = anios_imp[ultimo]
                    primero = min(con_imp)
                    huecos = [a for a in ANIOS if primero <= a <= HOY.year and anios_imp[a] == 0]
                    if huecos:
                        pendiente_eur = ult_imp * len(huecos)
                        tot_pendiente_eur += pendiente_eur
                        estado = "Hueco %s (est. %.0f €)" % (
                            ",".join(str(h) for h in huecos), pendiente_eur)
            filas.append({"s": s, "anios": anios_imp, "estado": estado,
                          "pend": pendiente_eur})

        informe.append({"cliente": c.get("nombre", ""), "codigo": c.get("codigo", ""),
                        "filas": filas})

    # --- HTML ---
    def cell(serv, a, anios_imp, vencido_year=None):
        v = anios_imp.get(a, 0.0)
        if serv["origen"] == "KD":
            ini = serv.get("kd_inicio")
            if ini and a >= ini.year:
                cls = "kd" ; txt = "verificar"
            else:
                cls = "" ; txt = ""
        else:
            if v > 0:
                cls = "ok" ; txt = "%.0f" % v
            else:
                cls = "" ; txt = ""
        return '<td class="%s">%s</td>' % (cls, txt)

    rows = []
    for cli in sorted(informe, key=lambda x: x["cliente"]):
        rows.append('<tr class="cli"><td colspan="%d"><b>%s</b> <span class="cod">%s</span></td></tr>'
                    % (len(ANIOS) + 3, html.escape(cli["cliente"]), cli["codigo"]))
        for fila in cli["filas"]:
            s = fila["s"]
            tds = "".join(cell(s, a, fila["anios"]) for a in ANIOS)
            est = fila["estado"]
            est_cls = "venc" if "VENCIDO" in est else ("hueco" if "Hueco" in est else "")
            rows.append(
                '<tr><td class="serv">%s</td><td class="org %s">%s</td>%s<td class="est %s">%s</td></tr>'
                % (html.escape(s["nombre"]),
                   "okd" if s["origen"] == "KD" else "orec", s["origen"],
                   tds, est_cls, html.escape(est)))

    cat_rows = "".join(
        "<tr><td>%s</td><td>%d</td><td>%s</td></tr>" % (html.escape(k), v["n"], html.escape(v["ej"]))
        for k, v in sorted(catalogo.items(), key=lambda kv: -kv[1]["n"]))

    th_anios = "".join("<th>%d</th>" % a for a in ANIOS)
    doc = """<!doctype html><html lang=es><meta charset=utf-8>
<title>Informe servicios x anios</title>
<style>
body{{font:14px/1.4 system-ui,Segoe UI,Arial;margin:24px;color:#1a1a1a}}
h1{{font-size:20px}} .sub{{color:#555;margin-bottom:18px}}
.kpi{{display:flex;gap:16px;margin:18px 0}}
.kpi div{{background:#f4f6f8;border:1px solid #e0e4e8;border-radius:8px;padding:14px 18px}}
.kpi b{{font-size:24px;display:block}}
table{{border-collapse:collapse;width:100%;margin-top:8px}}
th,td{{border:1px solid #e3e6ea;padding:5px 8px;text-align:left;font-size:13px}}
th{{background:#2c3e50;color:#fff;position:sticky;top:0}}
tr.cli td{{background:#eef2f6;border-top:2px solid #2c3e50}}
.cod{{color:#888;font-weight:normal;font-size:12px}}
.serv{{min-width:220px}}
td.ok{{background:#d4edda;text-align:right;font-variant-numeric:tabular-nums}}
td.kd{{background:#fff3cd;text-align:center;color:#8a6d00;font-size:11px}}
.org{{font-size:11px;text-align:center}}
.okd{{color:#8a6d00}} .orec{{color:#0a6}}
.est{{font-size:12px}} .est.venc{{color:#b30000;font-weight:600}}
.est.hueco{{color:#b36b00;font-weight:600}}
.leg span{{display:inline-block;padding:2px 8px;border-radius:4px;margin-right:8px;font-size:12px}}
.cat{{margin-top:32px}} .cat table{{width:auto}}
</style>
<h1>Informe servicios &times; a&ntilde;os &mdash; jero_autonomo</h1>
<div class=sub>Generado {hoy} &middot; solo lectura &middot; reglas KD: bono 12 meses (24 Procesos)</div>
<div class=kpi>
  <div><b>{neur:,.0f} &euro;</b>Pendiente estimado<br><small>recurrentes con hueco</small></div>
  <div><b>{nkd}</b>Servicios KD vencidos<br><small>verificar activaci&oacute;n + facturar</small></div>
  <div><b>{ncli}</b>Clientes con servicios</div>
</div>
<div class="leg">
  <span style="background:#d4edda">facturado (&euro;)</span>
  <span style="background:#fff3cd">KD: verificar/facturar</span>
  <span style="color:#b30000">VENCIDO</span>
  <span style="color:#b36b00">hueco</span>
</div>
<table>
<tr><th>Servicio</th><th>Origen</th>{thanios}<th>Estado</th></tr>
{rows}
</table>
<div class=cat>
<h2 style="font-size:16px">Cat&aacute;logo de servicios detectados (revisa reglas)</h2>
<table><tr><th>Servicio / categor&iacute;a</th><th>L&iacute;neas</th><th>Ejemplo</th></tr>
{cat}
</table></div>
</html>""".format(
        hoy=HOY.isoformat(), neur=tot_pendiente_eur, nkd=tot_kd_vencidos,
        ncli=len(informe), thanios=th_anios, rows="\n".join(rows), cat=cat_rows)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print("OK ->", OUT)
    print("Clientes con servicios:", len(informe))
    print("Pendiente estimado (recurrentes con hueco): %.0f EUR" % tot_pendiente_eur)
    print("Servicios KD vencidos a verificar:", tot_kd_vencidos)

if __name__ == "__main__":
    main()
