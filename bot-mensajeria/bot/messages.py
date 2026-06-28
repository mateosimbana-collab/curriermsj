from datetime import datetime
from typing import Any

import config
from domain.constants import REPORT_CATEGORIES, SHIPPING_SERVICES, STATUS_STEPS


LINE = "━━━━━━━━━━━━━━━━━━"
BUSINESS = config.BUSINESS_NAME.upper()


class Buttons:
    MENU_PRIMARY = [
        {"id": "rastrear", "title": "Rastrear"},
        {"id": "cotizar", "title": "Cotizar"},
        {"id": "mis_envios", "title": "Mis envios"},
    ]
    MENU_SECONDARY = [
        {"id": "reportar", "title": "Reportar"},
        {"id": "agente", "title": "Agente"},
        {"id": "volver_menu", "title": "Menu"},
    ]
    BACK = [{"id": "volver_menu", "title": "Menu"}]
    ORIGIN = [
        {"id": "ubicacion_origen", "title": "Ubicacion"},
        {"id": "escribir_origen", "title": "Escribir"},
        {"id": "volver_menu", "title": "Menu"},
    ]
    DESTINATION = [
        {"id": "ubicacion_destino", "title": "Ubicacion"},
        {"id": "escribir_destino", "title": "Escribir"},
        {"id": "volver_menu", "title": "Menu"},
    ]
    WEIGHTS = [
        {"id": "peso_ligero", "title": "Menos 1kg"},
        {"id": "peso_medio", "title": "1 - 5 kg"},
        {"id": "peso_pesado", "title": "Mas de 5kg"},
    ]
    SERVICES = [
        {"id": "servicio_express", "title": "Express"},
        {"id": "servicio_estandar", "title": "Estandar"},
        {"id": "servicio_economico", "title": "Economico"},
    ]
    CONFIRM_QUOTE = [
        {"id": "confirmar_envio", "title": "Confirmar"},
        {"id": "volver_menu", "title": "Menu"},
    ]
    CONFIRM_SHIPMENT = [
        {"id": "si_confirmar", "title": "Confirmar"},
        {"id": "no_cancelar", "title": "Cancelar"},
    ]
    INSTRUCTIONS = [
        {"id": "inst_fragil", "title": "Fragil"},
        {"id": "inst_urgente", "title": "Urgente"},
        {"id": "inst_ninguna", "title": "Ninguna"},
    ]
    REPORT_TYPES = [
        {"id": "rep_danado", "title": "Danado"},
        {"id": "rep_no_llego", "title": "No llego"},
        {"id": "rep_incompleto", "title": "Incompleto"},
    ]
    AFTER_TRACKING = [
        {"id": "mis_envios", "title": "Mis envios"},
        {"id": "agente", "title": "Agente"},
        {"id": "volver_menu", "title": "Menu"},
    ]
    AFTER_REPORT = [
        {"id": "agente", "title": "Agente"},
        {"id": "volver_menu", "title": "Menu"},
    ]


class MessageTemplates:
    @staticmethod
    def menu() -> str:
        return (
            f"🟢 *{BUSINESS}* • Asistente Virtual\n"
            f"{LINE}\n"
            f"👋 ¡Hola! Soy *{config.BOT_NAME}*, tu asistente.\n"
            f"Ruta principal: *{config.ROUTE_LABEL}*.\n"
            "¿Qué necesitas hoy?\n"
            f"{LINE}\n"
            "📦 *1.* Rastrear mi paquete\n"
            "🧾 *2.* Cotizar un envío\n"
            "📋 *3.* Ver mis envíos activos\n"
            "❌ *4.* Reportar un problema\n"
            "🧑‍💼 *5.* Hablar con un agente\n"
            f"{LINE}\n"
            "_Usa los botones o responde con el número_ 👇"
        )

    @staticmethod
    def ask_tracking() -> str:
        return (
            f"📦 *RASTREAR PAQUETE*\n"
            f"{LINE}\n"
            "Envíame tu código de seguimiento.\n\n"
            "Ejemplo: *CUR-00001*\n"
            f"{LINE}\n"
            "_También puedes escribir solo el número._"
        )

    @staticmethod
    def tracking_card(shipment: dict[str, Any], tracking_code: str) -> str:
        status = (shipment.get("estado") or "pendiente").lower()
        return (
            f"╔══════════════════════╗\n"
            f"   🚀 *{BUSINESS}*\n"
            f"   _Entregas rápidas y seguras_\n"
            f"╚══════════════════════╝\n"
            f"📦 *PAQUETE #{tracking_code}*\n"
            f"{LINE}\n"
            f"👤 Para: *{_value(shipment.get('destinatario'))}*\n"
            f"📍 Destino: *{_value(shipment.get('direccion_destino'))}*\n"
            f"⚖️ Peso: *{_value(shipment.get('peso'))}*\n"
            f"🚚 Servicio: *{_value(shipment.get('servicio_envio'), 'Pendiente')}*\n"
            f"{LINE}\n"
            "🗺️ *ESTADO DEL ENVÍO:*\n"
            f"{_status_lines(status)}\n"
            f"{LINE}\n"
            f"🕐 Estimado: *{_value(shipment.get('entrega_estimada'), 'Por confirmar')}*\n"
            f"{LINE}\n"
            "_Elige una opción_ 👇"
        )

    @staticmethod
    def tracking_not_found(code: str) -> str:
        return (
            f"❌ *NO ENCONTRÉ EL PAQUETE*\n"
            f"{LINE}\n"
            f"Código consultado: *{code}*\n\n"
            "Revisa que tenga este formato:\n"
            "*CUR-00001*"
        )

    @staticmethod
    def ask_quote_origin() -> str:
        return (
            f"💰 *COTIZA TU ENVÍO*\n"
            f"{LINE}\n"
            "📤 Primero necesito el origen en *Estados Unidos*.\n\n"
            "Puedes enviar ubicación o escribir la dirección."
        )

    @staticmethod
    def ask_quote_destination() -> str:
        return (
            f"📥 *DESTINO EN ECUADOR*\n"
            f"{LINE}\n"
            "Ahora dime a qué ciudad o dirección de Ecuador llegará el paquete."
        )

    @staticmethod
    def ask_package_type() -> str:
        return (
            f"📦 *TIPO DE PAQUETE*\n"
            f"{LINE}\n"
            "Elige la opción que más se parezca a tu envío."
        )

    @staticmethod
    def package_type_sections() -> list[dict[str, Any]]:
        return [
            {
                "title": "Tipos de paquete",
                "rows": [
                    {
                        "id": "tipo_documento",
                        "title": "Documentos",
                        "description": "Sobres, papeles o trámites",
                    },
                    {
                        "id": "tipo_pequeno",
                        "title": "Paquete pequeño",
                        "description": "Accesorios o artículos pequeños",
                    },
                    {
                        "id": "tipo_mediano",
                        "title": "Paquete mediano",
                        "description": "Ropa, zapatos o caja mediana",
                    },
                    {
                        "id": "tipo_grande",
                        "title": "Paquete grande",
                        "description": "Caja grande o volumen alto",
                    },
                ],
            }
        ]

    @staticmethod
    def ask_weight() -> str:
        return (
            f"⚖️ *PESO APROXIMADO*\n"
            f"{LINE}\n"
            "Selecciona un rango de peso para calcular la cotización."
        )

    @staticmethod
    def quote_options(data: dict[str, Any], options: dict[str, dict[str, Any]]) -> str:
        lines = [
            f"💰 *TU COTIZACIÓN*",
            LINE,
            f"📤 Origen: *{_value(data.get('origen'))}*",
            f"📥 Destino: *{_value(data.get('destino'))}*",
            f"📦 Paquete: *{_value(data.get('tipo_paquete'))}*",
            f"⚖️ Peso: *{_value(data.get('peso'))}*",
            LINE,
            "📋 *OPCIONES DE ENVÍO:*",
        ]
        for service_id, option in options.items():
            service = SHIPPING_SERVICES[service_id]
            lines.append(
                f"{service['icon']} *{service['label']}* › ${option['price']:.2f} USD"
            )
        lines.extend([LINE, "_¿Con cuál te quedamos?_ 👇"])
        return "\n".join(lines)

    @staticmethod
    def quote_summary(data: dict[str, Any]) -> str:
        return (
            f"✅ *CONFIRMAR COTIZACIÓN*\n"
            f"{LINE}\n"
            f"📤 Origen: *{_value(data.get('origen'))}*\n"
            f"📥 Destino: *{_value(data.get('destino'))}*\n"
            f"📦 Paquete: *{_value(data.get('tipo_paquete'))}*\n"
            f"⚖️ Peso: *{_value(data.get('peso'))}*\n"
            f"🚚 Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"🕐 Tiempo estimado: *{_value(data.get('entrega_estimada'))}*\n"
            f"{LINE}\n"
            f"💵 *Total: ${float(data.get('cotizacion', 0)):.2f} USD*\n"
            f"{LINE}\n"
            "_Confirma para registrar tus datos._"
        )

    @staticmethod
    def ask_sender_name() -> str:
        return (
            f"👤 *DATOS DEL ENVÍO*\n"
            f"{LINE}\n"
            "Perfecto. ¿Cuál es tu nombre completo?"
        )

    @staticmethod
    def ask_sender_phone() -> str:
        return "📱 ¿Cuál es tu número de teléfono?"

    @staticmethod
    def ask_recipient_name() -> str:
        return "👤 ¿Cuál es el nombre completo del destinatario?"

    @staticmethod
    def ask_recipient_phone() -> str:
        return "📱 ¿Cuál es el teléfono del destinatario?"

    @staticmethod
    def ask_exact_destination() -> str:
        return (
            f"📍 *DIRECCIÓN FINAL*\n"
            f"{LINE}\n"
            "Escribe la dirección exacta en Ecuador para la entrega."
        )

    @staticmethod
    def ask_instructions() -> str:
        return (
            f"📝 *INSTRUCCIONES ESPECIALES*\n"
            f"{LINE}\n"
            "¿Tu paquete necesita algún cuidado?"
        )

    @staticmethod
    def shipment_summary(data: dict[str, Any]) -> str:
        return (
            f"📋 *RESUMEN DEL ENVÍO*\n"
            f"{LINE}\n"
            f"👤 Remitente: *{_value(data.get('remitente'))}*\n"
            f"📱 Teléfono: *{_value(data.get('telefono_remitente'))}*\n"
            f"👤 Destinatario: *{_value(data.get('destinatario'))}*\n"
            f"📱 Teléfono dest.: *{_value(data.get('telefono_destinatario'))}*\n"
            f"📤 Origen: *{_value(data.get('origen'))}*\n"
            f"📥 Destino: *{_value(data.get('direccion_destino') or data.get('destino'))}*\n"
            f"📦 Paquete: *{_value(data.get('tipo_paquete'))}*\n"
            f"⚖️ Peso: *{_value(data.get('peso'))}*\n"
            f"🚚 Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"📝 Instrucciones: *{_value(data.get('instrucciones'))}*\n"
            f"{LINE}\n"
            f"💵 *Total: ${float(data.get('cotizacion', 0)):.2f} USD*\n"
            f"{LINE}\n"
            "¿Confirmas este envío?"
        )

    @staticmethod
    def shipment_created(tracking_code: str, data: dict[str, Any]) -> str:
        return (
            f"✅ *ENVÍO REGISTRADO*\n"
            f"{LINE}\n"
            f"📦 Código: *{tracking_code}*\n"
            f"👤 Para: *{_value(data.get('destinatario'))}*\n"
            f"📍 Destino: *{_value(data.get('direccion_destino') or data.get('destino'))}*\n"
            f"🚚 Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"💵 Total: *${float(data.get('cotizacion', 0)):.2f} USD*\n"
            f"{LINE}\n"
            "Nuestro equipo se pondrá en contacto contigo."
        )

    @staticmethod
    def shipments_list(shipments: list[dict[str, Any]]) -> str:
        if not shipments:
            return (
                f"📋 *MIS ENVÍOS*\n"
                f"{LINE}\n"
                "No tienes envíos registrados con este número todavía."
            )

        lines = [f"📋 *MIS ENVÍOS ACTIVOS*", LINE]
        for shipment in shipments:
            code = shipment.get("tracking_code") or f"CUR-{int(shipment['id']):05d}"
            lines.extend(
                [
                    f"📦 *{code}*",
                    f"👤 { _value(shipment.get('destinatario')) }",
                    f"📍 { _value(shipment.get('direccion_destino')) }",
                    f"🚚 { _value(shipment.get('estado'), 'pendiente') }",
                    "",
                ]
            )
        lines.extend([LINE, "_Puedes rastrear uno con su código._"])
        return "\n".join(lines)

    @staticmethod
    def report_categories() -> str:
        return (
            f"⚠️ *REPORTAR PROBLEMA*\n"
            f"{LINE}\n"
            "Lamentamos el inconveniente.\n"
            "Elige el tipo de problema para ayudarte más rápido."
        )

    @staticmethod
    def ask_report_description(category: str) -> str:
        return (
            f"⚠️ *{category.upper()}*\n"
            f"{LINE}\n"
            "Cuéntame qué pasó.\n\n"
            "Si tienes código de paquete, inclúyelo.\n"
            "Ejemplo: *CUR-00012 no llegó en fecha*"
        )

    @staticmethod
    def report_created(report_id: int, category: str, tracking_code: str | None = None) -> str:
        code_line = f"📦 Paquete: *{tracking_code}*\n" if tracking_code else ""
        return (
            f"⚠️ *REPORTE #INC-{report_id:04d}*\n"
            f"{LINE}\n"
            "Tu caso ya fue registrado.\n"
            f"{code_line}"
            f"📌 Tipo: *{category}*\n"
            f"🕐 Reportado: *{datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"
            "👨‍💻 Agente asignado: *Equipo soporte*\n"
            f"{LINE}\n"
            "Un agente revisará el caso y te contactará."
        )

    @staticmethod
    def agent() -> str:
        return (
            f"🧑‍💼 *HABLAR CON UN AGENTE*\n"
            f"{LINE}\n"
            "Ya avisamos al equipo de soporte.\n"
            f"Horario: *{config.SUPPORT_HOURS}*"
        )

    @staticmethod
    def location_help() -> str:
        return (
            f"📍 *ENVIAR UBICACIÓN*\n"
            f"{LINE}\n"
            "Toca el clip o botón de adjuntar en WhatsApp y elige *Ubicación*."
        )

    @staticmethod
    def unknown() -> str:
        return (
            "No entendí tu mensaje todavía.\n"
            "Te dejo el menú para que elijas una opción."
        )


def build_quote_options(package_type: str, weight: str) -> dict[str, dict[str, Any]]:
    from domain.constants import BASE_QUOTES_USD

    base_price = BASE_QUOTES_USD.get((package_type, weight), 10.00)
    options: dict[str, dict[str, Any]] = {}
    for service_id, service in SHIPPING_SERVICES.items():
        options[service_id] = {
            "label": service["label"],
            "eta": service["eta"],
            "price": round(base_price * float(service["multiplier"]), 2),
        }
    return options


def _status_lines(current_status: str) -> str:
    status_index = _status_index(current_status)
    lines = []
    for index, (_, label) in enumerate(STATUS_STEPS):
        if index < status_index:
            marker = "✅"
        elif index == status_index:
            marker = "⏳"
        else:
            marker = "⬜"
        lines.append(f"{marker} {label}")
    return "\n".join(lines)


def _status_index(status: str) -> int:
    for index, (value, _) in enumerate(STATUS_STEPS):
        if value == status:
            return index
    return 0


def _value(value: Any, fallback: str = "N/A") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback
