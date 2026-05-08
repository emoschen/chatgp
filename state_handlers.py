# state_handlers.py
from services.bcra import consultar_historial_crediticio, consultar_cheques_rechazados, consultar_deudas
from services.arca import consultar_comprobantes_fecred_por_cuit, consultar_obligacion
from services.skf import get_sales_order
from services.protheus import get_resumen_cliente, get_estado_remitos, get_depositos, get_estado_pedido, get_movimientos_cliente, get_gestor_cliente, get_cuentas_bancarias, get_cheques_cartera, comparar_cuits_grandes_con_tamemp, get_facturas_remito_cliente
from services.deglar import find_cliente_id_by_phone
from twilio.twiml.messaging_response import MessagingResponse
from utils.utils import generate_options_msg, enviar_documento_por_mail, generate_options_msg, preparar_respuesta_larga, subir_html_largo, format_fecha, format_monto
from templates.base import envolver_en_html
import requests
import os, re
from requests.auth import HTTPBasicAuth
from urllib.parse import quote_plus
from datetime import datetime

from templates.estado_pedido import render_estado_pedido # Nuevo import
from templates.resumen_cliente import render_resumen_cliente #Nuevo import

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

MONEDAS = {
    1: "ARS",
    2: "USD"
}

_TIPO_OPCION_CBTE = {
    "a": "Factura",
    "b": "Nota de Debito",
    "c": "Nota de Credito",
}

_TIPO_OPCION_PEDIDO = {
    "a": "Pedido Protheus",
    "b": "OC Cliente",
    "c": "Cotizacion",
}


def _clean(s):
    if not s:
        return ""
    # normaliza espacios y NBSP
    return " ".join(str(s).replace("\u00A0", " ").split())



def _maps_link(address: str, label: str | None = None, prefer_geocoding: bool = True) -> str:
    """
    Devuelve un link clickeable de Google Maps.
    - Si hay API key y prefer_geocoding=True, usa Geocoding API para obtener place_id.
    - Si falla o no hay key, usa Google Maps URLs API por query (sin costo/clave).
    """
    address = _clean(address)
    label = _clean(label) or address

    if prefer_geocoding and GOOGLE_MAPS_API_KEY:
        try:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": GOOGLE_MAPS_API_KEY, "region": "ar"},
                timeout=6,
            )
            r.raise_for_status()
            data = r.json()
            results = data.get("results") or []
            if results:
                place_id = results[0].get("place_id")
                if place_id:
                    # Link por place_id (preferido)
                    return (
                        "https://www.google.com/maps/search/?api=1"
                        f"&query={quote_plus(label)}"
                        f"&query_place_id={quote_plus(place_id)}"
                    )
        except Exception:
            pass  # fallback abajo

    # Fallback: link por query de dirección (no requiere API key)
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"



def handle_cuit_historial_bcra(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.isdigit():
        response_msg = consultar_historial_crediticio(int(message_text))
        response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
        session_states[sender] = "esperando_cuit_historial_bcra"
    elif message_text.lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
    else:
        response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu* para volver al inicio."
    return response_msg


def handle_cuit_deudas_bcra(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.isdigit():
        # Consulta de deudas en BCRA
        response_msg = consultar_deudas(int(message_text))
        response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."

        # Forzar salida como archivo de contenido
        response_msg = preparar_respuesta_larga(response_msg, forceFile=True)

        session_states[sender] = "esperando_cuit_deudas_bcra"

    elif message_text.lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"

    else:
        response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu*."

    return response_msg


def handle_nro_orden_skf(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    if message_text.strip().isdigit():
        nro_orden = int(message_text.strip())
        response = get_sales_order(nro_orden)
        session_states[sender] = "esperando_nro_orden_skf"
        return f"{response}\n\n¿Querés consultar otra orden? Escribí el número o escribí *menu* para volver al inicio."

    return "⚠️ Enviá solo el número de orden, por ejemplo: `809677`, o escribí *menu* para volver al inicio."


# def handle_esperando_entidad_cheque(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
#     if message_text.strip().lower() == "menu":
#         response_msg, option_map = generate_options_msg(user_area)
#         session_data[sender] = {"option_map": option_map}
#         session_states[sender] = "waiting_option"
#         return response_msg

#     if message_text.strip().isdigit():
#         idx = int(message_text.strip()) - 1
#         entidades_ordenadas = session_data[sender].get("entidades_ordenadas", [])
#         if 0 <= idx < len(entidades_ordenadas):
#             codigo, nombre = entidades_ordenadas[idx]
#             session_data[sender]["codigo_entidad_cheque"] = codigo
#             session_data[sender]["nombre_entidad_cheque"] = nombre
#             session_states[sender] = "esperando_nro_cheque"
#             return f"✍️ Ingresá el *número de cheque* para consultar en {nombre}."
#         else:
#             return "❌ Opción inválida. Por favor escribí el número de la entidad del listado."
#     else:
#         return "⚠️ Por favor respondé con un número válido según el listado o escribí *menu* para volver al inicio."



# def handle_esperando_nro_cheque(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
#     if message_text.strip().lower() == "menu":
#         response_msg, option_map = generate_options_msg(user_area)
#         session_data[sender] = {"option_map": option_map}
#         session_states[sender] = "waiting_option"
#         return response_msg

#     if message_text.strip().isdigit():
#         nro_cheque = int(message_text.strip())
#         codigo = session_data[sender].get("codigo_entidad_cheque")
#         nombre = session_data[sender].get("nombre_entidad_cheque")
#         if codigo:
#             response_msg = consultar_cheques_denunciados(codigo, nro_cheque)
#             response_msg += "\n\n¿Querés consultar otro cheque? Escribí *menu* para volver al inicio o seleccioná otra entidad."
#             session_states[sender] = "esperando_entidad_cheque"
#             return response_msg
#         else:
#             session_states[sender] = "waiting_option"
#             return "❌ No pude recuperar los datos del banco. Escribí *menu* para volver a empezar."
#     else:
#         return "⚠️ Ingresá solo el número del cheque, por ejemplo: `85145621`."


def handle_esperando_cuit_obligacion_fce(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.isdigit():
        response_msg = consultar_obligacion(int(message_text))
        response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
        session_states[sender] = "esperando_cuit_obligacion_fce"
    elif message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        # menu_already_sent = True
    else:
        response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu* para volver al inicio."
    return response_msg


# def handle_esperando_cuit_info_persona(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
#     if message_text.isdigit():
#         response_msg = consultar_info_persona(int(message_text))
#         response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
#         session_states[sender] = "esperando_cuit_info_persona"
#     elif message_text.strip().lower() == "menu":
#         response_msg, option_map = generate_options_msg(user_area)
#         session_data[sender] = {"option_map": option_map}
#         session_states[sender] = "waiting_option"
#     else:
#         response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu* para volver al inicio."
#     return response_msg



def handle_esperando_cuit_fecred(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.isdigit():
        response_msg = consultar_comprobantes_fecred_por_cuit(int(message_text))
        response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
        session_states[sender] = "esperando_cuit_fecred"
    elif message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
    else:
        response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu* para volver al inicio."
    return response_msg


# def handle_esperando_cuit_cheques_denunciados_bcra(sender, message_text, session_data, session_states, user_area):
#     if message_text.isdigit():
#         response_msg = consultar_cheques_denunciados(int(message_text))
#         response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
#         session_states[sender] = "esperando_cuit_cheques_denunciados_bcra"
#     elif message_text.strip().lower() == "menu":
#         response_msg, option_map = generate_options_msg(user_area)
#         session_data[sender] = {"option_map": option_map}
#         session_states[sender] = "waiting_option"
#     else:
#         response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu*."
#     return response_msg


def handle_esperando_cuit_cheques_rechazados_bcra(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.isdigit():
        response_msg = consultar_cheques_rechazados(int(message_text))
        response_msg += "\n\n¿Deseás consultar otro CUIT? Escribí el número o escribí *menu* para volver al inicio."
        session_states[sender] = "esperando_cuit_cheques_rechazados_bcra"
    elif message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
    else:
        response_msg = "⚠️ Enviá solo el número de CUIT, por ejemplo: `20123456789` o escribí *menu*."
    
    return response_msg


def descargar_imagen_twilio(media_url: str) -> bytes:
    """Descarga una imagen desde Twilio usando autenticación básica."""
    username = os.getenv("TWILIO_USERNAME")
    password = os.getenv("TWILIO_PASSWORD")

    resp = requests.get(media_url, auth=HTTPBasicAuth(username, password)) # type: ignore
    if resp.status_code != 200:
        raise Exception(f"No se pudo descargar la imagen de Twilio (HTTP {resp.status_code})")
    return resp.content


def handle_esperando_foto_remito_conformado(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    # Volver al menú
    if message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    # Procesar imagen recibida
    if media_url and media_type and media_type.startswith("image/"):
        try:
            img_data = descargar_imagen_twilio(media_url)

            # Enviar la imagen al OCR (usar HTTP y hostname del servicio)
            files = {'file': ('remito.jpg', img_data)}
            try:
                ocr_url = os.getenv('OCR_SERVICE_URL', 'http://ocr-service:6000/ocr')
                resp = requests.post(ocr_url, files=files, timeout=60)
                ocr_result = resp.json()
            except Exception as e:
                return f"⚠️ No se pudo contactar al servicio de OCR: {e}"

            if not ocr_result.get("success"):
                error = ocr_result.get("error", "No se detectó ningún número en la imagen.")
                return f"⚠️ No se pudo leer el número del remito. Detalle: {error}"

            numero_12 = ocr_result.get("numero_12", "")
            if not numero_12 or len(numero_12) < 12:
                return "⚠️ No se pudo extraer correctamente el número del remito."

            pto_vta = numero_12[:4]
            nro_remito = numero_12[4:12]

            # Inicializar sesión si no existe o es incorrecta
            if sender not in session_data or not isinstance(session_data[sender], dict):
                session_data[sender] = {}

            # Guardar datos del remito en sesión
            session_data[sender]["remito_pto"] = pto_vta
            session_data[sender]["remito_nro"] = nro_remito
            session_data[sender]["remito_img"] = img_data
            session_states[sender] = "confirmar_envio_remito"

            return (
                f"Puedo ver que es el remito: {pto_vta} - {nro_remito}\n"
                f"¿Es correcto? Escribí *SI* para confirmar o escribí *menu* para volver."
            )

        except Exception as e:
            return f"⚠️ Error al procesar la imagen: {e}"

    return "⚠️ No se recibió una imagen. Enviá una *foto del remito* o escribí *menu* para volver al inicio."



def handle_resumen_cliente(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    from datetime import datetime

    # Acumuladores globales
    total_saldo = 0.0
    total_saldo_vencido = 0.0

    if message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg
    
    # Obtener código del vendedor desde la sesión (si está)
    cod_vendedor = session_data.get(sender, {}).get("user_codigo") or ""

    if message_text.isdigit():
        id_or_cuit = message_text.strip()
        
        try:
            # --- 1) Obtener datos del cliente ---
            resumen_data = get_resumen_cliente(id_or_cuit, cod_vendedor)
            consulta = resumen_data.get("consulta", {})
            info = resumen_data.get("data", {})
            tiendas_disponibles = consulta.get("tiendas_disponibles", [])

            # --- 2) Construir tiendas_data para el template HTML ---
            tiendas_data = []
            for tienda in tiendas_disponibles:
                codigo_tienda = tienda.get("tienda")
                try:
                    movimientos = get_movimientos_cliente(id_or_cuit, codigo_tienda)
                except Exception:
                    movimientos = []

                subtotal = 0.0
                for mov in movimientos:
                    saldo = mov.get("saldo", 0) or 0
                    tipo = mov.get("tipo", "").strip().upper()
                    if tipo in ("RA", "NCC"):
                        saldo = -abs(float(saldo))
                    else:
                        saldo = float(saldo)
                    subtotal += saldo
                    total_saldo += saldo
                    venc_str = format_fecha(mov.get("vencimiento"))
                    try:
                        if venc_str != "-" and datetime.strptime(venc_str, "%d/%m/%Y") < datetime.today():
                            total_saldo_vencido += saldo
                    except Exception:
                        pass

                tiendas_data.append({
                    "tienda": tienda,
                    "movimientos": movimientos,
                    "subtotal": subtotal,
                })

            # --- 3) Generar HTML y subir ---
            body = render_resumen_cliente(info, tiendas_data, total_saldo, total_saldo_vencido)
            html_doc = envolver_en_html(body, titulo="Resumen de Cuenta Cliente")
            response_msg = subir_html_largo(html_doc)
            response_msg += "\n\n¿Deseás consultar otro Resumen de Cuenta? Escribí el ID o escribí *menu* para volver al inicio."
            session_states[sender] = "esperando_resumen_cliente"

        except Exception as e:
            response_msg = f"⚠️ Error consultando C/C del cliente: {e}"
            response_msg += "\n\nEscribí otro ID o *menu* para volver al inicio."
            session_states[sender] = "esperando_resumen_cliente"

    else:
        response_msg = "⚠️ Enviá solo el código de cliente (por ejemplo: `5259`) o escribí *menu* para volver al inicio."

    return response_msg




def handle_confirmar_envio_remito(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    mensaje = message_text.strip().lower()

    if mensaje == "si":
        try:
            datos = session_data.get(sender, {})
            pto = datos.get("remito_pto")
            nro = datos.get("remito_nro")
            img_data = datos.get("remito_img")

            if not (pto and nro and img_data):
                session_states[sender] = "waiting_option"
                return "⚠️ No se encontró información del remito. Escribí *menu* para volver al inicio."

            # Enviar por email
            enviar_documento_por_mail(sender, img_data, "image/jpeg", f"Remito {pto}-{nro}")
            session_states[sender] = "waiting_option"

            return (
                f"✅ El remito {pto}-{nro} fue enviado por correo.\n"
                f"¿Deseás enviar otro? Escribí *menu* para volver al inicio."
            )

        except Exception as e:
            session_states[sender] = "waiting_option"
            return f"⚠️ No se pudo enviar el remito: {e}"

    elif mensaje == "menu":
        session_states[sender] = "waiting_option"
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        return "❌ Operación cancelada.\n\n" + response_msg

    return "⚠️ Escribí *SI* para confirmar o *NO* para cancelar."



def handle_datos_gestor(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    # Volver al menú
    if message_text.strip().lower() in ("menu", "menú"):
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {**session_data.get(sender, {}), "option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    # 1) Obtener cod_cli desde la sesión 
    cod_cli = session_data.get(sender, {}).get("cliente_id")

    # 3) Consultar gestor con el cod_cli correcto
    try:
        gestor = get_gestor_cliente(cod_cli)  

        nombre = gestor.get("nombre", "") or gestor.get("name", "")
        telefono = gestor.get("telefono", "") or gestor.get("phone", "")
        email = gestor.get("email", "")

        wa_link = ""
        if telefono:
            wa = re.sub(r"[^0-9]", "", telefono)
            if wa:
                wa_link = f"\n📱 WhatsApp: https://wa.me/{wa}"

        response_msg = (
            "👨‍💼 *Ud. tiene asignado a:*\n\n"
            f"{nombre}\n"
            f"Email: 📫 {email}{wa_link}\n\n"
            "Puede comunicarse de Lunes a Viernes de 8 a 12 y de 13 a 17 hs.\n"
            "Escribí *menu* para volver al inicio."
        )
        session_states[sender] = "waiting_option"

    except Exception as e:
        response_msg = (
            f"⚠️ No se pudieron obtener los datos del gestor: {e}\n\n"
            "Escribí *menu* para volver al inicio."
        )
        session_states[sender] = "waiting_option"

    return response_msg



def handle_datos_percepciones(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    # Volver al menú
    if message_text.strip().lower() in ("menu", "menú"):
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {**session_data.get(sender, {}), "option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    nombre = "Antonela Mathieu"
    telefono = "+5493482697006"
    email = "antonela.mathieu@godoypovina.com.ar"

    wa_link = ""
    if telefono:
        wa = re.sub(r"[^0-9]", "", telefono)
        if wa:
            wa_link = f"\n📱 WhatsApp: https://wa.me/{wa}"

    response_msg = (
        "👨‍💼 *Gestor Contable e Impositivo:*\n\n"
        f"{nombre}\n"
        f"Email: 📫 {email}{wa_link}\n\n"
        "Puede comunicarse de Lunes a Viernes de 8 a 12 y de 13 a 17 hs.\n"
        "Escribí *menu* para volver al inicio."
    )
    session_states[sender] = "waiting_option"
    return response_msg



def handle_cuentas_bancarias(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    mensajes = []

    if message_text.strip().lower() in ["menu", "menú"]:
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return ["📋 *Menú principal*:\n\n" + response_msg]

    try:
        cuentas = get_cuentas_bancarias()

        if not cuentas:
            return ["ℹ️ No hay cuentas bancarias disponibles en este momento."]

        for cuenta in cuentas:
            nombre = cuenta.get("nombre", "-")
            cuenta_nro = cuenta.get("cuenta", "-")
            agencia = cuenta.get("agencia", "-")
            cbu = cuenta.get("cbu", "-")
            moneda = cuenta.get("moneda", "-")

            contenido = (
                f"🏦 *{nombre}*\n"
                f"• Cuenta: `{cuenta_nro}`\n"
                f"• Agencia: `{agencia}`\n"
                f"• Moneda: `{moneda}`\n"
                f"• CBU: `{cbu}`"
            )
            mensajes.append(contenido)

        mensajes.append("Escribí *menú* para volver al inicio.")
        session_states[sender] = "waiting_option"
        return mensajes

    except Exception as e:
        return [f"⚠️ Error consultando cuentas bancarias: {e}\n\nEscribí *menú* para volver al inicio."]



def handle_cheques_en_cartera(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    # capturar la opcion
    cod_cli = (message_text or "").strip().lower()

    try:
        cheques_info = get_cheques_cartera(cod_cli)
        cheques = cheques_info.get("data", [])  # type: ignore

        if not cheques:
            session_states[sender] = "esperando_cheques_cartera"
            return "ℹ️ No se encontraron cheques en cartera del cliente."

        total = 0
        respuesta = f"📄 *Estos son los cheques en cartera:*\n"
        for ch in cheques:
            total += ch.get('valor', 0)
            respuesta += (
                f"\n• *Número:* {ch['prefijo']}-{ch['numero']}\n"
                f"  *Banco:* {ch['banco']}\n"
                f"  *Fecha Emisión:* {format_fecha(ch['emision'])}\n"
                f"  *Fecha Vencimiento:* {format_fecha(ch['vencimiento'])}\n"
                f"  *Importe:* {format_monto(ch['valor'])}\n"
            )

        respuesta += f"\n🔢 *Total en cartera:* {format_monto(total)}"
        session_states[sender] = "esperando_cheques_cartera"
        return respuesta

    except Exception as e:
        session_states[sender] = "esperando_cheques_cartera"
        return f"⚠️ Ocurrió un error al consultar los cheques: {e}"
    


def handle_customer_cheques_en_cartera(sender, message_text, session_data, session_states, user_area):
   
    if message_text.strip().lower() in ["menu", "menú"]:
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return ["📋 *Menú principal*:\n\n" + response_msg]
    
    # 1) Obtener cod_cli desde la sesión 
    cod_cli = session_data.get(sender, {}).get("cliente_id")
    try:
        cheques_info = get_cheques_cartera(cod_cli)
        cheques = cheques_info.get("data", []) # type: ignore

        if not cheques:
            session_states[sender] = "waiting_option"
            return "ℹ️ No se encontraron cheques en cartera a tu nombre."

        total = 0
        respuesta = f"📄 *Estos son tus cheques en cartera:*\n"
        for ch in cheques:
            total += ch.get('valor', 0)
            respuesta += (
                f"\n• *Número:* {ch['prefijo']}-{ch['numero']}\n"
                f"  *Banco:* {ch['banco']}\n"
                f"  *Fecha Emisión:* {format_fecha(ch['emision'])}\n"
                f"  *Fecha Vencimiento:* {format_fecha(ch['vencimiento'])}\n"
                f"  *Importe:* {format_monto(ch['valor'])}\n"
            )

        respuesta += f"\n*Total en cartera:* {format_monto(total)}.\n\n Escribí *menú* para volver al inicio."
        session_states[sender] = "waiting_option"
        return respuesta

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Ocurrió un error al consultar tus cheques: {e}. Consultá a tu gestor de cobranza escribiendo Menú y luego la opción correspondiente. "
    

def handle_facturas_remito(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    if message_text.strip().lower() == "menu":
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return response_msg

    if message_text.isdigit():
        cliente_id = message_text.strip()
        
        try:
            facturas_remito = get_facturas_remito_cliente(cliente_id)
            facturas = facturas_remito.get("data", [])

            if not facturas:
                session_states[sender] = "esperando_facturas_remito"
                return "ℹ️ No se encontraron facturas o remitos para este cliente.\n\n¿Deseás consultar otro cliente? Escribí el ID o escribí *menu* para volver al inicio."

            respuesta = f"📄 *Facturas y Remitos del Cliente {cliente_id}:*\n\n"
            total_importe = 0
            
            for f in facturas:
                tipo = f.get("tipo", "Desconocido")
                numero = f.get("numero", "N/A")
                fecha_emision = format_fecha(f.get("emision"))
                fecha_vencimiento = format_fecha(f.get("vencimiento"))
                importe = f.get("valor", 0)
                total_importe += importe
                importe_formatted = format_monto(importe)
                estado = f.get("estado", "Desconocido")

                respuesta += (
                    f"• *{tipo}* #{numero}\n"
                    f"  📅 Emisión: {fecha_emision}\n"
                    f"  ⏰ Vencimiento: {fecha_vencimiento}\n"
                    f"  💰 Importe: {importe_formatted}\n"
                    f"  📊 Estado: {estado}\n\n"
                )

            respuesta += f"💰 *Total:* {format_monto(total_importe)}\n\n¿Deseás consultar otro cliente? Escribí el ID o escribí *menu* para volver al inicio."
            session_states[sender] = "esperando_facturas_remito"
            return respuesta

        except Exception as e:
            session_states[sender] = "esperando_facturas_remito"
            return f"⚠️ Ocurrió un error al consultar las facturas/remitos: {e}\n\n¿Deseás consultar otro cliente? Escribí el ID o escribí *menu* para volver al inicio."

    return "⚠️ Enviá solo el número de cliente (por ejemplo: `12365`) o escribí *menu* para volver al inicio."
    

    
def handle_consultar_grandes_empresas(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None): # type: ignore
    import requests

    try:
        # Paso 1: Obtener CUITs grandes desde scrap-service
        scrap_url = os.getenv("SCRAP_SERVICE_URL", "http://192.168.1.7:8000/archivo")
        resp = requests.get(scrap_url, timeout=30)
        grandes = set([line.strip() for line in resp.text.splitlines() if line.strip().isdigit()])

        # Paso 2: Obtener clientes desde Protheus API
        protheus_url = os.getenv("API_PROTHEUS_URL", "http://192.168.1.249:8585/api/v1/clientes?limit=9999")
        clientes = requests.get(protheus_url, timeout=30).json().get("data", [])

        inconsistencias = []
        for cli in clientes:
            cuit = cli.get("cuit")
            tamemp = str(cli.get("tamemp", "")).strip()
            if cuit in grandes and tamemp != "3":
                inconsistencias.append(f"{cuit} → tamemp={tamemp}")

        if not inconsistencias:
            msg = "✅ Todos los CUITs de grandes empresas están correctamente marcados como `3`."
        else:
            msg = "📊 *Empresas que deberían estar marcadas como '3' (GRANDE):*\n\n"
            msg += "\n".join(inconsistencias)
            msg += f"\n\nTotal inconsistencias: {len(inconsistencias)}"

        session_states[sender] = "waiting_option"
        return preparar_respuesta_larga(msg, forceFile=True)

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Error al consultar grandes empresas: {e}"




def handle_consultar_grandes_empresas(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    try:
        inconsistencias = comparar_cuits_grandes_con_tamemp()

        if not inconsistencias:
            msg = "✅ Todos los CUITs de grandes empresas están correctamente marcados como `Gran Empresa` en PROTHEUS."
        else:
            msg = "📊 *Empresas que deberían estar marcadas como '3' (Gran Empresa):*\n\n"
            for cuit, tamemp in inconsistencias.items():
                msg += f"{cuit} → {tamemp}\n"
            msg += f"\nTotal inconsistencias: {len(inconsistencias)}"

        session_states[sender] = "waiting_option"
        return preparar_respuesta_larga(msg, forceFile=True)

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Error al verificar empresas grandes: {e}"



def handle_customer_resumen_cc(sender, message_text, session_data, session_states, user_area, media_url=None, media_type=None):
    from datetime import datetime

    # Acumuladores
    total_saldo = 0.0
    total_saldo_vencido = 0.0

    # 1) Obtener cod_cli desde la sesión 
    cod_cli = session_data.get(sender, {}).get("cliente_id")

    try:
        # 2. Obtener datos del cliente
        resumen_data = get_resumen_cliente(cod_cli) # type: ignore
        consulta = resumen_data.get("consulta", {})
        info = resumen_data.get("data", {})
        tiendas_disponibles = consulta.get("tiendas_disponibles", [])

        cc_lines = []
        if tiendas_disponibles:
            for tienda in tiendas_disponibles:
                codigo_tienda = tienda.get("tienda")
                nombre_tienda = tienda.get("nombre", f"Tienda {codigo_tienda}")

                try:
                    movimientos = get_movimientos_cliente(cod_cli, codigo_tienda)
                except Exception as e:
                    cc_lines.append(f"⚠️ No se pudo consultar la tienda {codigo_tienda} ({nombre_tienda}): {e}")
                    continue

                cc_lines.append(f"\n🏪 *Cuenta Corriente - {nombre_tienda} (Tienda {codigo_tienda}):*")
                if movimientos:
                    for mov in movimientos:
                        emision = format_fecha(mov.get("emision"))
                        venc = format_fecha(mov.get("vencimiento"))
                        saldo = mov.get("saldo", 0) or 0

                        tipo = mov.get("tipo", "").strip().upper()
                        if tipo in ("RA", "NCC"):
                            saldo = -abs(saldo)

                        # Acumular saldos
                        total_saldo += saldo

                        # Sumar al vencido si corresponde (fecha de vencimiento pasada)
                        try:
                            if venc != "-" and datetime.strptime(venc, "%d/%m/%Y") < datetime.today():
                                total_saldo_vencido += saldo
                        except Exception:
                            pass

                        saldo_str = format_monto(saldo).rjust(15)

                        cc_lines.append(
                            f"- {tipo} {mov.get('documento', '-')} "
                            f"| Emisión: {emision} | Venc.: {venc} "
                            f"| Saldo: {saldo_str}"
                        )
                else:
                    cc_lines.append(f"ℹ️ No se encontraron movimientos para esta tienda.")
        else:
            cc_lines.append("ℹ️ El cliente no tiene tiendas asociadas.")

        resumen_lines = []
        if info:
            resumen_lines = [
                f"📄 *Resumen del Cliente {info.get('nombre', '-')}:*",
                f"Ciudad: {info.get('ciudad', '-')} | Dirección: {info.get('direccion', '-')}",
                f"CUIT: {info.get('cuit', '-')} | Condición de Venta: {info.get('condicion', '-')}",
                f"Persona: {info.get('persona', '-')} | Tipo: {info.get('tipo', '-')}",
                "",
                f"Saldo Pendiente (todas las tiendas): {format_monto(total_saldo)}",
                f"Saldo Pendiente Vencido (todas las tiendas): {format_monto(total_saldo_vencido)}",
                ""
            ]
        else:
            resumen_lines = [f"ℹ️ No se encontró información general para el cliente {cod_cli}."]

        contenido = "\n".join(resumen_lines + [""] + cc_lines)
        response_msg = preparar_respuesta_larga(contenido, forceFile=True)
        response_msg += "\n\nEscribí *menu* para volver al inicio."
        session_states[sender] = "waiting_option"
        return response_msg  

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Ocurrió un error al consultar tu cuenta corriente: {e}"




def handle_customer_almacenes(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    mensajes = []

    # Volver al menú
    if message_text.strip().lower() in ["menu", "menú"]:
        response_msg, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return ["📋 *Menú principal*:\n\n" + response_msg]

    try:
        resp = get_depositos()  # puede ser list[dict] o dict con "data"
        depositos = resp.get("data", []) if isinstance(resp, dict) else (resp or [])

        if not depositos:
            return ["ℹ️ No hay depósitos disponibles en este momento."]

        for d in depositos:
            codigo    = d.get("codigo", "-")
            nombre    = d.get("nombre", "-")
            categoria = d.get("categoria", "-")
            sucursal  = d.get("sucursal_nombre") or d.get("sucursal_id", "-")
            provincia = d.get("provincia", "-")
            direccion = d.get("direccion", "-").replace("\u00A0", " ").strip()
            telefono  = d.get("telefono", "-")

            maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(direccion)}"

            contenido = (
                f"🏬 *{nombre}*\n"
                f"• Dirección: `{direccion}`\n"
                f"• Teléfono: `{telefono}`\n"
                f"🔗 {maps_url}"
            )
            mensajes.append(contenido)

        mensajes.append("Escribí *menú* para volver al inicio.")
        session_states[sender] = "waiting_option"
        return mensajes

    except Exception as e:
        return [f"⚠️ Error consultando depósitos: {e}\n\nEscribí *menú* para volver al inicio."]



def handle_consulta_estado_pedido_start(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    session_states[sender] = "esperando_consulta_estado_pedido_nro_tipo"
    return "🔍 Ingresá la opción para buscar por:\n\na) Nro Pedido Protheus \nb) Nro OC Cliente \nc) Nro Cotización"



def handle_consulta_estado_pedido_nro_tipo(sender, message_text, session_data, session_states, user_area,
                                           media_url=None, media_type=None):
    opcion = (message_text or "").strip().lower()

    if opcion in ("menu", "menú"):
        resp, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return resp

    if opcion in _TIPO_OPCION_PEDIDO:
        tipo_texto = _TIPO_OPCION_PEDIDO[opcion]
        session_data.setdefault(sender, {})["pedido_nro_tipo"] = tipo_texto
        session_states[sender] = "esperando_consulta_estado_pedido_nro"
        return f"🧾 Ingresá el *número* de {tipo_texto}."

    return "⚠️ Opción inválida. Ingresá: \n\na) Nro Pedido Protheus \nb) Nro OC Cliente \nc) Nro Cotización \n\nSino escribí *menu* para volver al inicio."



def handle_consulta_estado_pedido_nro(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    nro = (message_text or "").strip().lower()

    if nro in ("menu", "menú"):
        resp, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return resp

    try:
        cod_vendedor = session_data.get(sender, {}).get("user_codigo", "")
        tipo = session_data.get(sender, {}).get("pedido_nro_tipo", "")
        pedido_data = get_estado_pedido(nro, tipo, cod_vendedor)
        info = pedido_data.get("data", [])

        if not info:
            session_states[sender] = "esperando_consulta_estado_pedido_nro"
            return f"ℹ️ No se encontraron datos con el valor buscado. Es posible que aún no haya sido ingresado el pedido en PROTHEUS. \n\n🧾 Intentá con otro *número* de {tipo} ó escribí *menu* para volver al inicio."

        html_doc = envolver_en_html(render_estado_pedido(info), titulo="Estado del Pedido")
        response_msg = subir_html_largo(html_doc)
        session_states[sender] = "esperando_consulta_estado_pedido_nro"
        response_msg += f"\n\nIngresá otro *número* de {tipo} ó escribí *menu* para volver al inicio."
        return response_msg

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Ocurrió un error al consultar número de pedido: {e}"




def handle_customer_descargar_comprobante_start(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    session_states[sender] = "esperando_customer_descargar_comprobante_elegir_tipo"
    return "🔍 Ingresá el tipo de comprobante:\na) Factura \nb) Nota de Débito \nc) Nota de Crédito"



def handle_customer_descargar_comprobante_elegir_tipo(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    # capturar la opcion
    opcion = (message_text or "").strip().lower()

    if opcion in ("menu", "menú"):
        resp, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return resp

    if opcion in _TIPO_OPCION_CBTE:
        tipo = _TIPO_OPCION_CBTE[opcion]
        sd = session_data.setdefault(sender, {})
        sd["cbte_tipo"] = tipo
        session_states[sender] = "esperando_customer_descargar_comprobante_ingresar_datos"
        return "🧾 Ingresá *punto de venta* y *número* separados por un espacio. Ej.: `0103 00987711`"
    
    return "⚠️ Opción inválida.\n\n🔍 Ingresá el tipo de comprobante:\na) Factura \nb) Nota de Débito \nc) Nota de Crédito"



def handle_customer_descargar_comprobante_ingresar_datos(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    
    # capturar la opcion
    msg = (message_text or "").strip().lower()

    if msg in ("menu", "menú"):
        resp, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return resp
    
    # leer punto de venta y numero
    # llamar al servicio
    # subir el archivo a S3
    # retornar el resultado
    
    return f"⚠️ Falta implementar"


def handle_customer_estado_remitos(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    """
    Devuelve los estados de remitos de los últimos 60 días para el cliente actual,
    agrupados por orden de compra.
    """
    try:
        cliente_id = session_data.get(sender, {}).get("cliente_id", "")
        cod_vendedor = session_data.get(sender, {}).get("user_codigo", "")

        if not cliente_id:
            session_states[sender] = "waiting_option"
            return "⚠️ No se encontró un cliente asociado a tu usuario. Volvé al menú principal."

        remitos_data = get_estado_remitos(cliente_id, cod_vendedor)
        info = remitos_data.get("data", [])

        if not info:
            session_states[sender] = "waiting_option"
            return "ℹ️ No se encontraron remitos en los últimos 60 días."

        contenido = [f"📦 *Estado de Remitos (últimos 60 días)*"]
        # contenido.append(f"Cliente ID: {cliente_id}\n")

        for oc in info:
            contenido.append(f"🧾 *Orden de Compra: {oc['orden_compra']}*")
            for r in oc.get("remitos", []):
                factura = (
                    f"{r['factura']} - {format_fecha(r.get('fecha_factura', ''))}"
                    if r.get("factura")
                    else "Pendiente"
                )
                contenido += [
                    f"Remito: {r['remito']} - {format_fecha(r.get('fecha_remito', ''))}",
                    f"Factura: {factura}",
                    "-" * 30
                ]
            contenido.append("")  # línea en blanco entre OCs

        response_msg = preparar_respuesta_larga("\n".join(contenido), forceFile=True)
        session_states[sender] = "waiting_option"
        response_msg += "\n\n✉️ Escribí *menu* para volver al inicio."
        return response_msg

    except Exception as e:
        session_states[sender] = "waiting_option"
        return f"⚠️ Ocurrió un error al consultar el estado de remitos: {e}"




def handle_customer_facturas_remito(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):

    return "🧾 Ingresá *punto de venta* y *número* separados por un espacio. Ej.: `0103 00987711`"



def handle_customer_facturas_remito_ingresar_datos(sender, message_text, session_data, session_states, user_area,
                                 media_url=None, media_type=None):
    # capturar la opcion
    msg = (message_text or "").strip().lower()

    if msg in ("menu", "menú"):
        resp, option_map = generate_options_msg(user_area)
        session_data[sender] = {"option_map": option_map}
        session_states[sender] = "waiting_option"
        return resp

    # recuperar numero y punto de venta del remito
    # llamar al servicio
    # subir los archivos al S3
    # retornar resultados

    return f"⚠️ Falta implementar"


