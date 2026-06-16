# -*- coding: utf-8 -*-
"""
Genera app_servicios.html — herramienta interactiva de decision de renovaciones.
Reutiliza la clasificacion de generar_informe.py. Embute los datos (abre sin servidor).
NO modifica renovaciones_data.json.
"""
import io
import re
import json
import unicodedata
from datetime import date
from collections import defaultdict
from generar_informe import clasificar_kd, clasificar_recurrente, add_months, parse_fecha

HOY = date(2026, 6, 8)
ANIOS = [2022, 2023, 2024, 2025, 2026, 2027]
DATA = "renovaciones_data.json"
DOMINIOS_XLS = "listado-dominios (1).xls"
TEMPLATE = "app_servicios_template.html"
OUT = "app_servicios.html"


def _tokens(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s).lower())
                if unicodedata.category(c) != "Mn")
    s = re.sub(r"\b(s\.?l\.?u?|s\.?a\.?|sociedad|limitada|cb|sc|sll|the)\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return set(w for w in s.split() if len(w) > 2)


def _proveedor(dns):
    d = str(dns).lower()
    for k, v in [("dinahosting", "Dinahosting"), ("lucushost", "LucusHost"),
                 ("siteground", "SiteGround"), ("ionos", "IONOS"),
                 ("1and1", "IONOS"), ("ovh", "OVH"), ("raiola", "Raiola")]:
        if k in d:
            return v
    return (d.split(",")[0].strip() or "?")


def parse_dominios():
    """Lee el listado de Dinahosting (xlsx con extension .xls). Devuelve lista de dominios."""
    try:
        with open(DOMINIOS_XLS, "rb") as fh:
            raw = fh.read()
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True)
    except Exception as e:
        print("AVISO: no se pudo leer dominios:", e)
        return []
    ws = wb.active
    out = []
    for r in list(ws.iter_rows(values_only=True))[1:]:
        if not r or not r[0]:
            continue
        exp = str(r[2])[:10] if r[2] else ""
        out.append({
            "dom": str(r[0]).strip(),
            "expira": exp,
            "expira_iso": _a_iso(exp),
            "prov": _proveedor(r[6]),
            "emp": str(r[9] or "").strip(),
        })
    return out


def _a_iso(s):
    """Convierte 'DD/MM/YYYY' o 'YYYY-MM-DD' a ISO ordenable."""
    s = str(s).strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if m:
        return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    return ""


def sugerir_dominios(nombre_cliente, dominios):
    """Devuelve dominios ordenados por similitud con el cliente (token overlap)."""
    ct = _tokens(nombre_cliente)
    if not ct:
        return []
    puntuados = []
    for d in dominios:
        et = _tokens(d["emp"]) | _tokens(d["dom"].rsplit(".", 1)[0])
        if not et:
            continue
        inter = len(ct & et)
        if inter:
            sc = inter / min(len(ct), len(et))
            puntuados.append((sc, d["dom"]))
    puntuados.sort(reverse=True)
    return [dom for sc, dom in puntuados if sc >= 0.34][:6]


def _categoria(tipo):
    t = tipo.lower()
    if "web" in t or "tienda" in t or "seo" in t or "presencia" in t:
        return "web"
    if "getradi" in t or "dolibarr" in t or "erp" in t or "crm" in t:
        return "erp"
    return "otro"


def _nuevo(nombre, origen, meses):
    return {"nombre": nombre, "origen": origen, "meses": meses,
            "anios": defaultdict(float), "kd_inicio": None,
            "ultima_fecha": None, "importe_sug": 0.0, "lineas": []}


def construir_servicios(dominios):
    with open(DATA, encoding="utf-8") as fh:
        data = json.load(fh)
    clientes = data if isinstance(data, list) else data.get("clientes", data)

    filas = []
    for c in clientes:
        servicios = {}
        for f in c.get("facturas", []):
            anio = f.get("anio")
            fdate = parse_fecha(f.get("fecha"))
            for l in f.get("lineas", []):
                desc = str(l.get("desc", "")).strip()
                imp = float(l.get("importe") or 0)
                if not desc:
                    continue
                up = desc.upper()
                if up.startswith("KD"):
                    kd = clasificar_kd(desc)
                    if kd is None:
                        continue
                    serv, meses = kd
                    key = "KD:" + serv
                    s = servicios.setdefault(key, _nuevo(serv, "KD", meses))
                    if fdate:
                        ini = add_months(fdate, meses)
                        if s["kd_inicio"] is None or ini < s["kd_inicio"]:
                            s["kd_inicio"] = ini
                        if s["ultima_fecha"] is None or fdate > s["ultima_fecha"]:
                            s["ultima_fecha"] = fdate
                else:
                    rec = clasificar_recurrente(desc)
                    if rec is None:
                        continue
                    key = "REC:" + rec
                    s = servicios.setdefault(key, _nuevo(rec, "Recurrente", None))
                    if anio:
                        s["anios"][anio] += imp
                    if fdate and (s["ultima_fecha"] is None or fdate > s["ultima_fecha"]):
                        s["ultima_fecha"] = fdate
                        s["importe_sug"] = imp
                # linea original completa para identificar el servicio (normaliza saltos)
                desc_full = re.sub(r"\s+", " ", desc).strip()
                s["lineas"].append({"anio": anio, "fecha": fdate.isoformat() if fdate else "",
                                    "desc": desc_full[:400], "importe": round(imp, 2)})

        dom_sug = sugerir_dominios(c.get("nombre", ""), dominios)
        for key, s in sorted(servicios.items()):
            base = s["kd_inicio"] if s["origen"] == "KD" else s["ultima_fecha"]
            uso_hasta_def = add_months(base, 12).isoformat() if base else ""

            estado = ""
            if s["origen"] == "KD" and s["kd_inicio"]:
                estado = "Bono hasta " + s["kd_inicio"].strftime("%d/%m/%Y")
                if s["kd_inicio"] <= HOY:
                    estado += " | VENCIDO"
            else:
                con = {a: s["anios"].get(a, 0.0) for a in ANIOS}
                facturados = [a for a in ANIOS if con[a] > 0]
                if facturados:
                    huecos = [a for a in ANIOS if min(facturados) <= a <= HOY.year and con[a] == 0]
                    if huecos:
                        estado = "Hueco " + ",".join(str(h) for h in huecos)

            # lineas unicas (desc) para no repetir
            vistas, lineas_u = set(), []
            for ln in s["lineas"]:
                if ln["desc"] not in vistas:
                    vistas.add(ln["desc"])
                    lineas_u.append(ln)

            # primer año facturable: KD -> año fin de bono; recurrente -> primer año con factura
            if s["origen"] == "KD" and s["kd_inicio"]:
                desde_anio = s["kd_inicio"].year
            else:
                con_facturas = [a for a in ANIOS if s["anios"].get(a, 0) > 0]
                desde_anio = min(con_facturas) if con_facturas else (HOY.year)

            filas.append({
                "id": "%s__%s" % (c.get("codigo", ""), key),
                "codigo": c.get("codigo", ""),
                "cliente": c.get("nombre", ""),
                "tipo": s["nombre"],
                "categoria": _categoria(s["nombre"]),
                "origen": s["origen"],
                "desde_anio": desde_anio,
                "anios": {str(a): round(s["anios"].get(a, 0.0), 2) for a in ANIOS},
                "kd_inicio": s["kd_inicio"].isoformat() if s["kd_inicio"] else None,
                "ultima_fecha": s["ultima_fecha"].isoformat() if s["ultima_fecha"] else None,
                "uso_hasta_def": uso_hasta_def,
                "importe_sug": round(s["importe_sug"], 2),
                "estado": estado,
                "lineas": lineas_u[:6],
                "dom_sug": dom_sug,
            })
    return filas


def main():
    dominios = parse_dominios()
    filas = construir_servicios(dominios)
    payload = {"hoy": HOY.isoformat(), "anios": ANIOS, "servicios": filas,
               "dominios": dominios}
    with open(TEMPLATE, encoding="utf-8") as fh:
        tpl = fh.read()
    out = tpl.replace("/*__DATA__*/", json.dumps(payload, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(out)
    print("OK ->", OUT)
    print("Servicios:", len(filas))
    print("Clientes:", len({f["codigo"] for f in filas}))
    print("Dominios:", len(dominios))


if __name__ == "__main__":
    main()
