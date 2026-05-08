"""
Template: Estado del Pedido
Recibe los datos crudos de get_estado_pedido() y genera el HTML body.
"""
import html as html_module
import re
from .base import md


MONEDAS = {1: "ARS", 2: "USD", "1": "ARS", "2": "USD"}

_COLUMNAS = [
    #  label           campo                  número  mob_hide
    ("Producto",      "descripcion",          False,  False),
    ("Ítem OC",       "item_oc",              False,  True),
    ("Cant. Ped.",    "cantidad",             True,   True),
    ("Cant. Pend.",   "cantidad_pendiente",   True,   False),
    ("Precio",        "precio",               True,   True),
    ("Estado",        "estado_tracker",       False,  False),
    ("Despacho",      "fecha_despacho",       False,  True),
    ("Est. Entrega",  "fecha_necesidad",      False,  True),
    ("Plazo",         "plazo",                False,  True),
    ("Remito",        "remito",               False,  True),
    ("Factura",       "factura",              False,  True),
]


def _estado_style(estado):
    e = (estado or "").lower()
    if any(x in e for x in ("entregado", "completo", "facturado")):
        return "background:rgba(76,175,80,0.18);color:#1b5e20;font-weight:500"
    if any(x in e for x in ("tránsito", "transito", "camino", "despachado")):
        return "background:rgba(255,152,0,0.18);color:#e65100;font-weight:500"
    if any(x in e for x in ("pendiente", "fabricaci")):
        return "background:rgba(255,193,7,0.15);color:#795500;font-weight:500"
    if any(x in e for x in ("error", "problema", "rechazado")):
        return "background:rgba(244,67,54,0.15);color:#b71c1c;font-weight:500"
    return ""


def _formato_fecha(fecha):
    if not fecha or str(fecha).strip() in ("-", ""):
        return "-"
    from datetime import datetime
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(fecha).split("T")[0], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            pass
    return str(fecha)


def _formato_monto(monto, moneda="ARS"):
    try:
        valor = f"{float(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{moneda} $ {valor}"
    except Exception:
        return str(monto)


def _celda_producto(item):
    codigo = html_module.escape(str(item.get("descripcion", "") or ""))
    nombre = html_module.escape(str(item.get("rodami", "") or ""))
    if nombre:
        return f'<span class="prod-code">{codigo}</span><br><span class="prod-name">{nombre}</span>'
    return f'<span class="prod-code">{codigo}</span>' if codigo else '<span class="muted">-</span>'


def _celda_remito(item):
    remito = str(item.get("remito", "") or "").strip()
    fecha = _formato_fecha(item.get("fecha_remito", ""))
    if remito and remito != "-":
        return html_module.escape(f"{remito} - {fecha}" if fecha != "-" else remito)
    return '<span class="muted">-</span>'


def _celda_factura(item):
    factura = str(item.get("factura", "") or "").strip()
    fecha = _formato_fecha(item.get("fecha_factura", ""))
    if factura and factura != "-":
        return html_module.escape(f"{factura} - {fecha}" if fecha != "-" else factura)
    return '<span class="muted">-</span>'


_tbl_counter = 0


def _tabla_items(items):
    global _tbl_counter
    _tbl_counter += 1
    tbl_id   = f"tbl-{_tbl_counter}"
    inp_id   = f"tbl-search-{_tbl_counter}"
    cnt_id   = f"tbl-count-{_tbl_counter}"
    n        = len(items)

    thead = "<tr>" + "".join(f"<th>{col}</th>" for col, _, _, _ in _COLUMNAS) + "</tr>"
    rows = []
    for idx, item in enumerate(items):
        cls = "r-odd" if idx % 2 else "r-even"
        moneda = MONEDAS.get(item.get("moneda", 1), "ARS")
        cells = []
        for col, campo, es_numero, mob_hide in _COLUMNAS:
            align = ' style="text-align:right;white-space:nowrap"' if es_numero else ""
            estado_style = ""

            if col == "Producto":
                val = _celda_producto(item)
            elif col == "Precio":
                val = html_module.escape(_formato_monto(item.get("precio", 0), moneda))
            elif col == "Estado":
                raw = str(item.get("estado_tracker", "") or "")
                st = _estado_style(raw)
                badge_style = f' style="{st}"' if st else ""
                val = (
                    f'<span class="estado-badge"{badge_style}>{html_module.escape(raw)}</span>'
                    if raw else '<span class="muted">-</span>'
                )
                align = ""
            elif col == "Despacho":
                val = html_module.escape(_formato_fecha(item.get("fecha_despacho")))
                align = ' style="white-space:nowrap"'
            elif col == "Est. Entrega":
                val = html_module.escape(_formato_fecha(item.get("fecha_necesidad")))
                align = ' style="white-space:nowrap"'
            elif col == "Remito":
                val = _celda_remito(item)
            elif col == "Factura":
                val = _celda_factura(item)
            else:
                raw_val = item.get(campo)
                if raw_val is None or str(raw_val).strip() in ("", "-"):
                    val = '<span class="muted">-</span>'
                else:
                    val = html_module.escape(str(raw_val).strip())

            mob_cls = ' class="mob-hide"' if mob_hide else ""
            cells.append(f'<td data-label="{col}"{mob_cls}{align}>{val}</td>')
        rows.append(f'<tr class="{cls}">{"".join(cells)}</tr>')

    no_results = (
        f'<tr id="{tbl_id}-empty" style="display:none">'
        f'<td colspan="{len(_COLUMNAS)}" class="tbl-no-results">'
        "No se encontraron ítems para esa búsqueda."
        "</td></tr>"
    )

    search_bar = f"""
<div class="tbl-search-wrap">
  <div class="tbl-search-input-wrap">
    <svg class="tbl-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
      <path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="m21 21-3.5-3.5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"/>
    </svg>
    <input id="{inp_id}" type="text" class="tbl-search-input"
           placeholder="Buscar ítem, código, estado..."
           oninput="filterTable('{tbl_id}','{inp_id}','{cnt_id}',{n})">
  </div>
  <span id="{cnt_id}" class="tbl-count">{n} {('ítem' if n == 1 else 'ítems')}</span>
</div>"""

    return (
        f'<div class="tbl-wrap">'
        f"{search_bar}"
        f'<table id="{tbl_id}" class="items-tbl">'
        f"<thead>{thead}</thead>"
        f"<tbody>{''.join(rows)}{no_results}</tbody>"
        "</table></div>"
    )


def _card(label, value, flex="1 1 0", highlight=False):
    cls   = ' hl' if highlight else ''
    style = f' style="flex:{flex}"'
    return (
        f'<div class="info-card"{style}>'
        f'<div class="info-card-label">{label}</div>'
        f'<div class="info-card-value{cls}">{value}</div>'
        f'</div>'
    )


def _cabecera_pedido(item):
    oc      = html_module.escape(str(item.get("numero_oc", "-") or "-"))
    fecha   = html_module.escape(_formato_fecha(item.get("fecha_emision", "")))
    cliente = html_module.escape(str(item.get("cliente_nombre", "-") or "-"))
    codigo  = html_module.escape(
        f"{item.get('cliente_codigo','').strip()}-{item.get('cliente_tienda','').strip()}"
    )
    pedido  = html_module.escape(str(item.get("pedido", "-") or "-"))

    # flex: grow shrink basis
    # Cliente recibe el espacio restante; Fecha y Pedido son anchos fijos cortos
    cards = "".join([
        _card("Fecha Emisión",  fecha,   flex="0 0 120px"),
        _card("Cliente",        cliente, flex="1 1 200px", highlight=True),
        _card("Código Cliente", codigo,  flex="0 0 140px"),
        _card("Pedido Nro",     pedido,  flex="0 0 120px"),
    ])

    return (
        f'<p class="hdr-sub">Detalles del Pedido &mdash; {oc}</p>'
        f'<div class="info-cards">{cards}</div>'
    )


def render_estado_pedido(info):
    """
    Recibe info (list[dict]) directo de get_estado_pedido().
    Agrupa por pedido y devuelve el HTML body completo.
    """
    if not info:
        return "<p>ℹ️ No se encontraron datos para este pedido.</p>"

    partes = []
    current_group = None
    items_grupo = []

    def _flush(items):
        if items:
            partes.append(_tabla_items(items))

    for row in info:
        group_key = (
            str(row.get("cliente_codigo", "")).strip(),
            str(row.get("cliente_tienda", "")).strip(),
            str(row.get("pedido", "")).strip(),
        )
        if group_key != current_group:
            _flush(items_grupo)
            items_grupo = []
            current_group = group_key
            partes.append(_cabecera_pedido(row))

        items_grupo.append(row)

    _flush(items_grupo)
    return "\n".join(partes)
