# utils.py
from collections import OrderedDict
from menu_loader import menu  # debe ser cargado globalmente
import uuid
import smtplib
import re
import html as html_module
import base64
from datetime import datetime
import requests
from email.message import EmailMessage
import os
import boto3
from dotenv import load_dotenv
load_dotenv()

# aws data
AWS_BUCKET = os.getenv("AWS_S3_BUCKET","godoy")
AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")
AWS_BASE_URL = os.getenv("AWS_S3_URL", f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
    region_name=AWS_REGION,
)

def generate_options_msg(user_area, nombre_whatsapp="Usuario"):
    grouped_options = OrderedDict()
    option_map = {}
    index = 1

    for key in menu:
        meta = menu[key]
        allowed_areas = meta.get("allowed_areas", [])
        group = meta.get("group", "default")
        label = meta.get("label", key.replace("_", " ").capitalize())

        if user_area and user_area.lower() not in [a.lower() for a in allowed_areas]:
            continue

        if group not in grouped_options:
            grouped_options[group] = []

        grouped_options[group].append((index, label, key))
        option_map[str(index)] = key
        index += 1

    group_headers = {
        "arca": "*Consultas ARCA*",
        "bcra": "*Consultas BCRA*",
        "skf": "*Consultas SKF*",
        "customer": "*Consultas Clientes*",
        "logistica": "*Logística*",
        "conectividad": "*Reclamos de Internet*",
        "info": "*Info*"
    }
    
    lines = [
        f"Hola *{nombre_whatsapp}*. 🤖 Soy _Perkins_, el Asistente Virtual de *Godoy Poviña Distribuidor Mayorista*",
        f"Te presento las opciones para el *Área {user_area.capitalize()}*:\n"
    ]

    for group_key, items in grouped_options.items():
        group_name = group_headers.get(group_key, group_key.capitalize())
        lines.append(f"{group_name}:")
        for idx, label, _ in items:
            lines.append(f"{idx}. {label}")
        lines.append("")

    lines.append("✍️ Escribí el número de la opción que querés consultar.")
    return "\n".join(lines), option_map


def split_message(text, max_len=1600):
    """
    Divide un mensaje largo en partes para cumplir con la restricción de WhatsApp (1600 caracteres)
    """
    parts = []
    while len(text) > max_len:
        split_index = text.rfind('\n', 0, max_len)
        if split_index == -1:
            split_index = max_len
        parts.append(text[:split_index])
        text = text[split_index:].lstrip()
    parts.append(text)
    return parts


def enviar_documento_por_mail(sender, img_data, media_type, asunto="Remito", descripcion="Remito enviado"):
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = "no-responder@godoypovina.com.ar"
    msg["To"] = "javier.comin@godoypovina.com.ar"
    msg.set_content(descripcion)

    extension = media_type.split("/")[-1]
    filename = f"remito_{sender}.{extension}"

    msg.add_attachment(img_data, maintype="image", subtype=extension, filename=filename)

    with smtplib.SMTP("smtp.office365.com", 587) as smtp:
        smtp.starttls()
        smtp.login("no-responder@godoypovina.com.ar", "P!assword#1044**")
        smtp.send_message(msg)


def consultar_ocr_service(image_path: str) -> dict:
    """
    Envía una imagen al microservicio OCR y devuelve el resultado JSON.
    Retorna un dict con:
      { "success": bool, "numero_completo": str, "numero_12": str, "error": str }
    """
    try:
        with open(image_path, "rb") as f:
            files = {'file': f}
            resp = requests.post(os.getenv('OCR_SERVICE_URL', 'https://ocr-service:6000/ocr'), files=files, timeout=10)
            return resp.json()
    except Exception as e:
        return {"success": False, "error": f"No se pudo contactar al OCR: {e}"}
    




def _md(line):
    escaped = __import__('html').escape(line)
    import re as _re
    escaped = _re.sub(r'\*([^*]+)\*', r'<strong></strong>', escaped)
    escaped = _re.sub(r'_([^_]+)_', r'<em></em>', escaped)
    escaped = _re.sub(r'`([^`]+)`', r'<code></code>', escaped)
    return escaped


def _texto_a_html_body(text):
    """Convierte texto plano con emojis/markdown a HTML body. Usado por handlers no migrados a templates/."""
    import re as _re
    lines = text.split('
')
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if _re.match(r'^[\-─]{5,}$', stripped):
            parts.append('<hr>')
            i += 1
            continue

        if not stripped:
            parts.append('<div class="gap"></div>')
            i += 1
            continue

        content = _md(line)
        if stripped.startswith('📦'):
            parts.append(f'<p class="hdr-main">{content}</p>')
        elif stripped.startswith(('📄', '📊')):
            clean = _re.sub(r'^[📄📊]\s*', '', stripped)
            parts.append(f'<p class="hdr-sub">{_md(clean)}</p>')
        elif stripped.startswith('🧾'):
            clean = _re.sub(r'^🧾\s*', '', stripped)
            parts.append(f'<p class="hdr-sub">{_md(clean)}</p>')
        elif stripped.startswith('🏪'):
            parts.append(f'<p class="hdr-store">{content}</p>')
        elif stripped.startswith(('💰', '🔢')):
            parts.append(f'<p class="total-line">{content}</p>')
        else:
            parts.append(f'<p>{content}</p>')
        i += 1

    return '
      '.join(parts)



def _logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'logo.jpg')
    try:
        with open(logo_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ''


def _envolver_en_html(body_content):
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
  <title>Perkins · Consulta</title>
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap"/>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Roboto', 'Helvetica', 'Arial', sans-serif;
      background-color: #eee;
      color: rgba(0,0,0,0.87);
      min-height: 100vh;
      padding: 30px 30px;
      font-size: 0.875rem;
      line-height: 1.25;
    }}
    .container {{ max-width: 1440px; margin: 0 auto; }}
    .header {{
      background-color: #004ba1;
      color: #fff;
      padding: 16px 24px;
      border-radius: 4px 4px 0 0;
      border-bottom: 3px solid #e74a0f;
    }}
    .header h1 {{ font-size: 1.15rem; font-weight: 700; letter-spacing: 0.01em; }}
    .header span {{ font-size: 0.75rem; opacity: 0.8; display: block; margin-top: 4px; font-weight: 300; }}
    .body {{
      background: #fff;
      padding: 24px;
      border-radius: 0 0 4px 4px;
      box-shadow: 0px 2px 4px -1px rgba(0,0,0,0.2), 0px 4px 5px 0px rgba(0,0,0,0.14), 0px 1px 10px 0px rgba(0,0,0,0.12);
    }}
    p {{ font-size: 0.875rem; line-height: 1.75; color: rgba(0,0,0,0.87); margin: 2px 0; }}
    strong {{ color: #004ba1; font-weight: 500; }}
    em {{ color: rgba(0,0,0,0.6); font-style: italic; }}
    code {{
      font-family: 'Courier New', Consolas, monospace;
      font-size: 0.8125rem;
      background: rgba(0,75,161,0.06);
      color: #e74a0f;
      padding: 1px 5px;
      border-radius: 4px;
    }}
    hr {{ border: none; border-top: 1px solid rgba(0,0,0,0.12); margin: 6px 0; }}
    .gap {{ height: 8px; }}
    .muted {{ color: rgba(0,0,0,0.38); }}
    .hdr-main {{
      background-color: #004ba1;
      color: #fff !important;
      padding: 8px 16px;
      margin: 16px -24px 8px;
      font-weight: 500;
    }}
    .hdr-main strong {{ color: #fff !important; }}
    .hdr-sub {{
      background-color: rgba(0,75,161,0.1);
      color: #004ba1 !important;
      padding: 6px 16px;
      margin: 10px -24px 4px;
      border-left: 4px solid #004ba1;
      font-weight: 500;
    }}
    .hdr-sub strong {{ color: #004ba1 !important; }}
    .hdr-store {{
      background-color: rgba(231,74,15,0.08);
      color: #b83500 !important;
      padding: 6px 16px;
      margin: 10px -24px 4px;
      border-left: 4px solid #e74a0f;
      font-weight: 500;
    }}
    .hdr-store strong {{ color: #b83500 !important; }}
    .total-line {{
      font-weight: 500;
      color: #004ba1 !important;
      padding: 4px 0;
      border-top: 1px solid rgba(0,75,161,0.2);
      margin-top: 4px;
    }}
    .total-line strong {{ color: #004ba1 !important; }}
    .tbl-wrap {{ overflow-x: auto; margin: 4px 0 16px; border-radius: 2px; border: 1px solid #bdbdbd; }}
    .items-tbl {{ width: 100%; border-collapse: collapse; font-size: 0.72rem; line-height: 1.3; }}
    .items-tbl thead {{ position: sticky; top: 0; z-index: 1; }}
    .items-tbl thead tr {{ background-color: #004ba1; color: #fff; }}
    .items-tbl th {{
      padding: 6px 8px;
      text-align: left;
      font-weight: 500;
      white-space: nowrap;
      font-size: 0.72rem;
      letter-spacing: 0.02em;
      border-right: 1px solid rgba(255,255,255,0.2);
    }}
    .items-tbl td {{
      padding: 4px 7px;
      vertical-align: top;
      border: 1px solid rgba(0,0,0,0.09);
      font-size: 0.72rem;
    }}
    .items-tbl tr.r-even {{ background: #fff; }}
    .items-tbl tr.r-odd {{ background: #f5f7ff; }}
    .items-tbl tr:hover td {{ background: rgba(0,75,161,0.08) !important; }}
    .prod-code {{ font-weight: 500; color: rgba(0,0,0,0.87); }}
    .prod-name {{ font-size: 0.68rem; color: rgba(0,0,0,0.54); }}
    .footer {{
      text-align: center;
      font-size: 0.75rem;
      color: rgba(0,0,0,0.54);
      margin-top: 12px;
      padding-bottom: 8px;
    }}
  </style>
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
</body>
</html>"""



def subir_html_largo(html_doc):
    """Sube un HTML doc completo a S3 y devuelve el link público. Usado por handlers con templates dedicados."""
    filename = f"respuesta_{__import__('uuid').uuid4().hex}.html"
    key = f"respuestas/{filename}"
    s3.put_object(
        Bucket=AWS_BUCKET,
        Key=key,
        Body=html_doc.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
        ACL="public-read",
    )
    download_url = f"{AWS_BASE_URL}/{key}"
    return f"📄 Consulta disponible en:
{download_url}"


def preparar_respuesta_larga(response_msg, forceFile=False):
    """
    Si el mensaje supera 1600 caracteres, lo convierte a HTML, lo sube a S3 y devuelve un link público.
    Si no, devuelve el mensaje tal cual.
    """
    if not response_msg:
        response_msg = "⚠️ Respuesta vacía. Intentá nuevamente o contactá a tu gestor."

    if len(response_msg) > 1600 or forceFile:
        filename = f"respuesta_{uuid.uuid4().hex}.html"
        key = f"respuestas/{filename}"

        html_doc = _envolver_en_html(_texto_a_html_body(response_msg))

        s3.put_object(
            Bucket=AWS_BUCKET,
            Key=key,
            Body=html_doc.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
            ACL="public-read"
        )
        download_url = f"{AWS_BASE_URL}/{key}"
        return f"📄 La respuesta puede ser muy larga.\nTe generé este archivo:\n{download_url}"

    return response_msg



# --- Funciones de formato ---
def format_fecha(fecha):
    if not fecha or not isinstance(fecha, str) or fecha.strip().startswith("-"):
        return "-"
    try:
        # Soporta ISO con o sin 'T'
        dt = datetime.fromisoformat(fecha.split("T")[0])
        return dt.strftime("%d/%m/%Y")
    except Exception as e:
        print(f"[ERROR] Falló format_fecha({fecha}): {e}")
        return fecha
    

def format_monto(monto):
    try:
        return f"$ {monto:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"$ {monto}"
