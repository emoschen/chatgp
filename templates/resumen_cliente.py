"""
Template: Resumen de Cuenta Cliente
Recibe los datos de get_resumen_cliente() + get_movimientos_cliente() y genera el HTML body.
"""
import html as html_module
from datetime import datetime


def _formato_fecha(fecha):
    if not fecha or str(fecha).strip() in ("-", ""):
        return "-"
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(fecha).split("T")[0], "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            pass
    return str(fecha)


def _formato_monto(monto):
    try:
        valor = f"{float(monto):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"$ {valor}"
    except Exception:
        return str(monto)


def _card(label, value, flex="1 1 0", highlight=False, value_style="", mob_hide=False):
    cls     = " hl" if highlight else ""
    mob_cls = " mob-hide-card" if mob_hide else ""
    style   = f' style="flex:{flex}"'
    v_style = f' style="{value_style}"' if value_style else ""
    return (
        f'<div class="info-card{mob_cls}"{style}>'
        f'<div class="info-card-label">{label}</div>'
        f'<div class="info-card-value{cls}"{v_style}>{value}</div>'
        f'</div>'
    )


def _tipo_badge(tipo):
    tipo = (tipo or "").strip().upper()
    estilos = {
        "NF":  "background:rgba(0,75,161,0.12);color:#004ba1",
        "NCC": "background:rgba(76,175,80,0.18);color:#1b5e20",
        "RA":  "background:rgba(76,175,80,0.18);color:#1b5e20",
        "NDC": "background:rgba(231,74,15,0.15);color:#b83500",
    }
    st = estilos.get(tipo, "background:rgba(0,0,0,0.07);color:rgba(0,0,0,0.6)")
    return f'<span class="estado-badge" style="{st}">{html_module.escape(tipo)}</span>'


def _es_vencido(fecha_str):
    try:
        return datetime.strptime(fecha_str, "%d/%m/%Y") < datetime.today()
    except Exception:
        return False


def _saldo_html(saldo, fecha_venc_str):
    try:
        valor = float(saldo)
    except Exception:
        return html_module.escape(str(saldo))
    monto = _formato_monto(valor)
    if valor < 0:
        color = "color:#1b5e20;font-weight:500"
    elif _es_vencido(fecha_venc_str):
        color = "color:#b71c1c;font-weight:500"
    else:
        color = "color:#004ba1;font-weight:500"
    return f'<span style="{color}">{html_module.escape(monto)}</span>'


_COLUMNAS = [
    #  label          número  mob_hide
    ("Tipo",          False,  False),
    ("Documento",     False,  False),
    ("Emisión",       False,  True),
    ("Vencimiento",   False,  True),
    ("Saldo",         True,   False),
]

_tbl_counter = 0


def _tabla_movimientos(movimientos, subtotal=0.0):
    global _tbl_counter
    _tbl_counter += 1
    tbl_id = f"tbl-rc-{_tbl_counter}"
    inp_id = f"tbl-search-rc-{_tbl_counter}"
    cnt_id = f"tbl-count-rc-{_tbl_counter}"
    n = len(movimientos)

    _right = 'style="text-align:right"'
    thead = "<tr>" + "".join(
        f'<th class="mob-hide">{col}</th>' if mob else
        (f'<th {_right}>{col}</th>' if num else f'<th>{col}</th>')
        for col, num, mob in _COLUMNAS
    ) + "</tr>"

    rows = []
    for idx, mov in enumerate(movimientos):
        cls  = "r-odd" if idx % 2 else "r-even"
        tipo = str(mov.get("tipo", "")).strip().upper()
        doc  = html_module.escape(str(mov.get("documento", "-") or "-").strip())

        emision  = html_module.escape(_formato_fecha(mov.get("emision", "")))
        venc_raw = _formato_fecha(mov.get("vencimiento", ""))
        venc     = html_module.escape(venc_raw)

        saldo = mov.get("saldo", 0) or 0
        if tipo in ("RA", "NCC"):
            saldo = -abs(float(saldo))

        cells = [
            f'<td data-label="Tipo">{_tipo_badge(tipo)}</td>',
            f'<td data-label="Documento">{doc}</td>',
            f'<td data-label="Emisión" class="mob-hide" style="white-space:nowrap">{emision}</td>',
            f'<td data-label="Vencimiento" class="mob-hide" style="white-space:nowrap">{venc}</td>',
            f'<td data-label="Saldo" style="text-align:right;white-space:nowrap">{_saldo_html(saldo, venc_raw)}</td>',
        ]
        rows.append(f'<tr class="{cls}">{"".join(cells)}</tr>')

    no_results = (
        f'<tr id="{tbl_id}-empty" style="display:none">'
        f'<td colspan="{len(_COLUMNAS)}" class="tbl-no-results">'
        "No se encontraron comprobantes para esa búsqueda."
        "</td></tr>"
    )

    search_bar = f"""
<div class="tbl-search-wrap">
  <div class="tbl-search-input-wrap">
    <svg class="tbl-search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24">
      <path stroke="currentColor" stroke-linecap="round" stroke-width="2" d="m21 21-3.5-3.5M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z"/>
    </svg>
    <input id="{inp_id}" type="text" class="tbl-search-input"
           placeholder="Buscar comprobante, tipo, fecha..."
           oninput="filterTable('{tbl_id}','{inp_id}','{cnt_id}',{n})">
  </div>
  <span id="{cnt_id}" class="tbl-count">{n} {"comprobante" if n == 1 else "comprobantes"}</span>
</div>"""

    sub_val = float(subtotal)
    sub_color = "#1b5e20" if sub_val <= 0 else "#004ba1"
    _lbl_st = "padding:6px 8px;font-weight:600;font-size:0.73rem;color:#004ba1;letter-spacing:0.02em"
    _val_st = f"text-align:right;padding:6px 8px;white-space:nowrap;font-weight:700;font-size:0.8rem;color:{sub_color}"
    _row_st = "background:rgba(0,75,161,0.09);border-top:2px solid rgba(0,75,161,0.25)"
    tfoot = (
        f'<tfoot>'
        f'<tr style="{_row_st}">'
        f'<td colspan="2" style="{_lbl_st}">Subtotal tienda</td>'
        f'<td class="mob-hide"></td>'
        f'<td class="mob-hide"></td>'
        f'<td style="{_val_st}">{html_module.escape(_formato_monto(sub_val))}</td>'
        f'</tr>'
        f'</tfoot>'
    )

    return (
        f'<div class="tbl-wrap">'
        f"{search_bar}"
        f'<table id="{tbl_id}" class="items-tbl rc-tbl">'
        f"<thead>{thead}</thead>"
        f"<tbody>{''.join(rows)}{no_results}</tbody>"
        f"{tfoot}"
        "</table></div>"
    )


def _cabecera_cliente(info):
    nombre    = html_module.escape(str(info.get("nombre",    "-") or "-"))
    cuit      = html_module.escape(str(info.get("cuit",      "-") or "-"))
    ciudad    = html_module.escape(str(info.get("ciudad",    "-") or "-"))
    condicion = html_module.escape(str(info.get("condicion", "-") or "-"))
    persona   = html_module.escape(str(info.get("persona",   "-") or "-"))
    tipo_cli  = html_module.escape(str(info.get("tipo",      "-") or "-"))
    riesgo    = html_module.escape(str(info.get("riesgo",    "-") or "-"))
    clase     = html_module.escape(str(info.get("clase",     "-") or "-"))
    bloqueado = info.get("bloqueado", False)
    bloq_txt  = "Sí" if bloqueado else "No"
    bloq_st   = "color:#b71c1c;font-weight:500" if bloqueado else "color:#1b5e20;font-weight:500"

    cards = "".join([
        _card("Cliente",            nombre,                    flex="2 1 220px", highlight=True),
        _card("CUIT",               cuit,                      flex="0 0 155px"),
        _card("Ciudad",             ciudad,                    flex="0 0 130px",  mob_hide=True),
        _card("Condición de Venta", condicion,                 flex="1 1 160px",  mob_hide=True),
        _card("Persona / Tipo",     f"{persona} · {tipo_cli}", flex="1 1 180px",  mob_hide=True),
        _card("Riesgo / Clase",     f"{riesgo} / {clase}",     flex="0 0 110px",  mob_hide=True),
        _card("Bloqueado",          bloq_txt,                  flex="0 0 95px",   mob_hide=True, value_style=bloq_st),
    ])
    return f'<div class="info-cards">{cards}</div>'


def _cards_totales(total_saldo, total_saldo_vencido):
    venc_color = "#b71c1c" if float(total_saldo_vencido or 0) > 0 else "#1b5e20"
    card_total = (
        f'<div class="info-card" style="flex:1 1 220px;border-left:3px solid #004ba1">'
        f'<div class="info-card-label">Saldo Pendiente Total</div>'
        f'<div class="info-card-value hl" style="font-size:1.05rem">'
        f'{html_module.escape(_formato_monto(total_saldo))}</div>'
        f'</div>'
    )
    card_vencido = (
        f'<div class="info-card" style="flex:1 1 220px;border-left:3px solid {venc_color}">'
        f'<div class="info-card-label">Saldo Vencido</div>'
        f'<div class="info-card-value" style="font-size:1.05rem;color:{venc_color};font-weight:500">'
        f'{html_module.escape(_formato_monto(total_saldo_vencido))}</div>'
        f'</div>'
    )
    return f'<p class="hdr-main">Saldos Pendientes</p><div class="info-cards">{card_total}{card_vencido}</div>'


def render_resumen_cliente(info, tiendas_data, total_saldo, total_saldo_vencido):
    """
    info:             dict con datos del cliente.
    tiendas_data:     list de dicts:
                        { "tienda": {"tienda": "01", "nombre": "OP. CAMPO"},
                          "movimientos": [...],
                          "subtotal": float }
    total_saldo:      float — suma global de saldos.
    total_saldo_vencido: float — suma de saldos vencidos.
    """
    partes = []

    if info:
        partes.append(_cabecera_cliente(info))

    partes.append(_cards_totales(total_saldo, total_saldo_vencido))

    partes.append('<p class="hdr-main">Cuenta Corriente por Tienda</p>')

    for item in tiendas_data:
        tienda   = item.get("tienda", {})
        movs     = item.get("movimientos", [])
        subtotal = item.get("subtotal", 0.0)
        cod      = html_module.escape(str(tienda.get("tienda", "-")))
        nombre_t = html_module.escape(str(tienda.get("nombre", f"Tienda {cod}")))
        n        = len(movs)

        partes.append(
            f'<p class="hdr-store">🏪 Tienda {cod} &mdash; {nombre_t} '
            f'<span style="font-weight:300;font-size:0.78rem">'
            f'({n} comprobante{"s" if n != 1 else ""})</span></p>'
        )

        if movs:
            partes.append(_tabla_movimientos(movs, subtotal))
        else:
            partes.append(
                '<p class="muted" style="padding:8px 0 16px">ℹ️ Sin movimientos registrados.</p>'
            )

    return "\n".join(partes)
