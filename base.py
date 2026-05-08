"""
Shell HTML compartido por todos los templates.
Contiene: logo, CSS global, función envolver_en_html().
"""
import os
import re
import base64
import html as html_module
from datetime import datetime


def _logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
    try:
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ''


def md(line):
    """Convierte markdown de WhatsApp (*bold*, _italic_, `code`) a HTML."""
    escaped = html_module.escape(line)
    escaped = re.sub(r'\*([^*]+)\*', r'<strong>\1</strong>', escaped)
    escaped = re.sub(r'_([^_]+)_', r'<em>\1</em>', escaped)
    escaped = re.sub(r'`([^`]+)`', r'<code>\1</code>', escaped)
    return escaped


_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
      background-color: #eee;
      color: rgba(0,0,0,0.87);
      min-height: 100vh;
      padding: 30px;
      font-size: 0.875rem;
      line-height: 1.25;
    }
    .container { max-width: 1200px; margin: 0 auto; }
    .header {
      background-color: #004ba1;
      color: #fff;
      padding: 16px 24px;
      border-radius: 4px 4px 0 0;
      border-bottom: 3px solid #e74a0f;
    }
    .header h1 { font-size: 1.15rem; font-weight: 700; letter-spacing: 0.01em; }
    .header span { font-size: 0.75rem; opacity: 0.8; display: block; margin-top: 4px; font-weight: 300; }
    .body {
      background: #fff;
      padding: 0 24px 24px;
      border-radius: 0 0 4px 4px;
      box-shadow: 0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12);
    }
    .body > p.hdr-main:first-child,
    .body > p.hdr-sub:first-child  { margin-top: 0; }
    p { font-size: 0.875rem; line-height: 1.75; color: rgba(0,0,0,0.87); margin: 2px 0; }
    strong { color: #004ba1; font-weight: 500; }
    em { color: rgba(0,0,0,0.6); font-style: italic; }
    code {
      font-family: 'Courier New', Consolas, monospace;
      font-size: 0.8125rem;
      background: rgba(0,75,161,0.06);
      color: #e74a0f;
      padding: 1px 5px;
      border-radius: 4px;
    }
    hr { border: none; border-top: 1px solid rgba(0,0,0,0.12); margin: 6px 0; }
    .gap { height: 8px; }
    .muted { color: rgba(0,0,0,0.38); }
    /* --- Sección headers --- */
    .hdr-main {
      background-color: #004ba1;
      color: #fff !important;
      padding: 8px 16px;
      margin: 16px -24px 8px;
      font-weight: 500;
    }
    .hdr-main strong { color: #fff !important; }
    .hdr-sub {
      background-color: rgba(0,75,161,0.1);
      color: #004ba1 !important;
      padding: 6px 16px;
      margin: 10px -24px 4px;
      border-left: 4px solid #004ba1;
      font-weight: 500;
    }
    .hdr-sub strong { color: #004ba1 !important; }
    .hdr-store {
      background-color: rgba(231,74,15,0.08);
      color: #b83500 !important;
      padding: 6px 16px;
      margin: 10px -24px 4px;
      border-left: 4px solid #e74a0f;
      font-weight: 500;
    }
    .hdr-store strong { color: #b83500 !important; }
    .total-line {
      font-weight: 500;
      color: #004ba1 !important;
      padding: 4px 0;
      border-top: 1px solid rgba(0,75,161,0.2);
      margin-top: 4px;
    }
    .total-line strong { color: #004ba1 !important; }
    /* --- Tabla de ítems --- */
    .tbl-wrap { overflow-x: auto; margin: 4px 0 16px; border-radius: 2px; border: 1px solid #bdbdbd; }
    .items-tbl { width: 100%; border-collapse: collapse; font-size: 0.72rem; line-height: 1.3; }
    .items-tbl thead { position: sticky; top: 0; z-index: 1; }
    .items-tbl thead tr { background-color: #004ba1; color: #fff; }
    .items-tbl th {
      padding: 6px 8px;
      text-align: left;
      font-weight: 500;
      white-space: nowrap;
      font-size: 0.72rem;
      letter-spacing: 0.02em;
      border-right: 1px solid rgba(255,255,255,0.2);
    }
    .items-tbl td {
      padding: 4px 7px;
      vertical-align: top;
      border: 1px solid rgba(0,0,0,0.09);
      font-size: 0.72rem;
    }
    .items-tbl tr.r-even { background: #fff; }
    .items-tbl tr.r-odd { background: #f5f7ff; }
    .items-tbl tr:hover td { background: rgba(0,75,161,0.08) !important; }
    .prod-code { font-weight: 500; color: rgba(0,0,0,0.87); }
    .prod-name { font-size: 0.68rem; color: rgba(0,0,0,0.54); }
    .estado-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 0.68rem;
      font-weight: 500;
      white-space: nowrap;
    }
    .footer {
      text-align: center;
      font-size: 0.75rem;
      color: rgba(0,0,0,0.54);
      margin-top: 12px;
      padding-bottom: 8px;
    }

    /* ================================================================ */
    /* --- Indicator cards (Detalles del Pedido, etc.) --- */
    .info-cards {
      display: flex;
      flex-wrap: nowrap;
      gap: 10px;
      margin: 10px 0 16px;
    }
    .info-card {
      min-width: 0;
      background: rgba(0,75,161,0.04);
      border: 1px solid rgba(0,75,161,0.14);
      border-left: 3px solid #004ba1;
      border-radius: 4px;
      padding: 10px 14px;
    }
    .info-card-label {
      font-size: 0.62rem;
      font-weight: 500;
      color: rgba(0,0,0,0.50);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 5px;
    }
    .info-card-value {
      font-size: 0.875rem;
      font-weight: 500;
      color: rgba(0,0,0,0.87);
      line-height: 1.3;
      word-break: break-word;
    }
    .info-card-value.hl { color: #004ba1; }

    /* --- Buscador de tabla --- */
    /* ================================================================ */
    .tbl-search-wrap {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 10px 12px;
      background: rgba(0,75,161,0.04);
      border-bottom: 1px solid #bdbdbd;
      gap: 12px;
      flex-wrap: wrap;
    }
    .tbl-search-input-wrap {
      position: relative;
      flex: 1;
      max-width: 360px;
      min-width: 180px;
    }
    .tbl-search-icon {
      position: absolute;
      left: 10px;
      top: 50%;
      transform: translateY(-50%);
      color: rgba(0,0,0,0.38);
      pointer-events: none;
    }
    .tbl-search-input {
      width: 100%;
      padding: 7px 12px 7px 34px;
      font-family: inherit;
      font-size: 0.8rem;
      border: 1px solid #bdbdbd;
      border-radius: 4px;
      background: #fff;
      color: rgba(0,0,0,0.87);
      outline: none;
      transition: border-color 0.15s;
    }
    .tbl-search-input:focus { border-color: #004ba1; box-shadow: 0 0 0 2px rgba(0,75,161,0.15); }
    .tbl-search-input::placeholder { color: rgba(0,0,0,0.38); }
    .tbl-count {
      font-size: 0.72rem;
      color: rgba(0,0,0,0.54);
      white-space: nowrap;
      flex-shrink: 0;
    }
    .tbl-no-results {
      text-align: center;
      padding: 20px;
      color: rgba(0,0,0,0.54);
      font-style: italic;
      font-size: 0.8rem;
    }

    /* ================================================================
       MOBILE — card view para tablas, layout adaptado
       Breakpoint: 640px cubre todos los celulares modernos (320–430px)
       ================================================================ */
    /* Cards: wrap en landscape mobile y tablets angostas */
    @media (max-width: 960px) {
      .info-cards { flex-wrap: wrap; }
      .info-card { flex: 1 1 140px !important; }
    }

    @media (max-width: 640px) {
      body { padding: 8px; }
      .body { padding: 0 16px 16px; }

      /* Ajustar márgenes negativos de headers al nuevo padding */
      .hdr-main  { margin: 12px -16px 6px; }
      .hdr-sub   { margin: 8px  -16px 4px; }
      .hdr-store { margin: 8px  -16px 4px; }

      /* Header: logo + texto apilados verticalmente */
      .header { padding: 12px 16px; }
      .header div[style] { flex-direction: column; align-items: flex-start !important; gap: 8px !important; }
      .header img { height: 44px !important; }
      .header h1 { font-size: 1rem; }

      /* Tabla → card view */
      .tbl-wrap  { border: none; margin: 4px 0 12px; }
      .items-tbl { font-size: 0.8rem; }
      .items-tbl thead { display: none; }
      .items-tbl tbody, .items-tbl tr, .items-tbl td { display: block; width: 100%; }
      .items-tbl tr {
        border: 1px solid #bdbdbd;
        border-radius: 4px;
        margin-bottom: 8px;
        overflow: hidden;
      }
      .items-tbl tr.r-even, .items-tbl tr.r-odd { background: #fff; }
      .items-tbl td {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        padding: 7px 12px;
        border: none;
        border-bottom: 1px solid rgba(0,0,0,0.06);
        font-size: 0.8rem;
        text-align: right !important;
      }
      .items-tbl td::before {
        content: attr(data-label);
        font-weight: 500;
        color: rgba(0,0,0,0.55);
        font-size: 0.72rem;
        flex-shrink: 0;
        margin-right: 12px;
        text-align: left;
        white-space: nowrap;
      }
      /* Primera celda (Producto) se destaca como título de la tarjeta */
      .items-tbl td:first-child {
        background: rgba(0,75,161,0.05);
        font-weight: 500;
        justify-content: flex-start;
        text-align: left !important;
        flex-direction: column;
        gap: 2px;
        padding: 10px 12px;
      }
      .items-tbl td:first-child::before { display: none; }
      /* Ocultar cards secundarias en portrait mobile */
      .mob-hide-card { display: none !important; }
      /* Ocultar columnas secundarias en mobile */
      .items-tbl td.mob-hide { display: none !important; }

      /* rc-tbl: mantener como tabla real (no card-view) en portrait mobile */
      .rc-tbl.items-tbl        { display: table !important; width: 100% !important; }
      .rc-tbl thead            { display: table-header-group !important; }
      .rc-tbl tbody            { display: table-row-group !important; }
      .rc-tbl tfoot            { display: table-footer-group !important; }
      .rc-tbl tr               { display: table-row !important; border: none !important;
                                  border-radius: 0 !important; margin-bottom: 0 !important;
                                  overflow: visible !important; }
      .rc-tbl tr.r-even        { background: #fff !important; }
      .rc-tbl tr.r-odd         { background: #f5f7ff !important; }
      .rc-tbl td,
      .rc-tbl th               { display: table-cell !important; width: auto !important;
                                  padding: 5px 7px !important;
                                  border-bottom: 1px solid rgba(0,0,0,0.06) !important; }
      .rc-tbl td               { text-align: left !important; justify-content: unset !important;
                                  flex-direction: unset !important; align-items: unset !important; }
      .rc-tbl td[style*="text-align:right"] { text-align: right !important; }
      .rc-tbl td::before       { display: none !important; }
      .rc-tbl td:first-child   { background: none !important; font-weight: normal !important;
                                  padding: 5px 7px !important; }
      .rc-tbl th.mob-hide,
      .rc-tbl td.mob-hide      { display: none !important; }
      .rc-tbl tr[id$="-empty"] { display: none !important; }
      .items-tbl tr:hover td { background: inherit !important; }
    }

    /* Toast "girá la pantalla" — solo mobile */
    #mob-rotate-tip {
      display: none;
    }
    @media (max-width: 640px) {
      #mob-rotate-tip {
        display: flex;
        align-items: center;
        gap: 10px;
        position: fixed;
        bottom: 28px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(0,0,0,0.82);
        color: #fff;
        padding: 10px 20px;
        border-radius: 24px;
        font-size: 0.78rem;
        font-family: inherit;
        white-space: nowrap;
        box-shadow: 0 4px 16px rgba(0,0,0,0.35);
        z-index: 9999;
        animation: mobTipFadeOut 0.5s ease 5s forwards;
        pointer-events: none;
      }
    }
    @keyframes mobTipFadeOut {
      to { opacity: 0; }
    }
"""


def envolver_en_html(body_content, titulo="Consulta"):
    """Envuelve un body HTML con el shell completo: logo, CSS, header, footer."""
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    logo = _logo_b64()
    logo_tag = (
        f'<img src="data:image/jpeg;base64,{logo}" alt="Godoy Povi&#241;a"'
        ' style="height:75px;border-radius:4px;background:#fff;padding:5px 8px;">'
        if logo else ''
    )
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Perkins · {html_module.escape(titulo)}</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"/>
  <style>{_CSS}</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div style="display:flex;align-items:center;gap:15px;">
        {logo_tag}
        <div>
          <h1>Godoy Povi&#241;a S.A.</h1>
          <span>Generado el {now}</span>
        </div>
      </div>
    </div>
    <div class="body">
      {body_content}
    </div>
  </div>
  <div class="footer">Godoy Povi&#241;a S.A.</div>
  <div id="mob-rotate-tip">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>
    </svg>
    Girá la pantalla para ver más información
  </div>
  <script>
    function filterTable(tblId, inpId, cntId, total) {{
      var q = document.getElementById(inpId).value.toLowerCase().trim();
      var rows = document.querySelectorAll('#' + tblId + ' tbody tr:not([id$="-empty"])');
      var visible = 0;
      rows.forEach(function(row) {{
        var match = row.textContent.toLowerCase().includes(q);
        row.style.display = match ? '' : 'none';
        if (match) visible++;
      }});
      var emptyRow = document.getElementById(tblId + '-empty');
      if (emptyRow) emptyRow.style.display = (visible === 0 && q) ? '' : 'none';
      var cnt = document.getElementById(cntId);
      if (cnt) cnt.textContent = q
        ? (visible + ' de ' + total + (total === 1 ? ' ítem' : ' ítems'))
        : (total + (total === 1 ? ' ítem' : ' ítems'));
    }}
    // Eliminar el toast del DOM al terminar la animación
    (function() {{
      var tip = document.getElementById('mob-rotate-tip');
      if (tip) setTimeout(function() {{ tip.remove(); }}, 5600);
    }})();
  </script>
</body>
</html>"""
