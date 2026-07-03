from datetime import datetime
from typing import Any

import config
from domain.constants import REPORT_CATEGORIES, SHIPPING_SERVICES, STATUS_STEPS


LINE = "--------------------"
BUSINESS = config.BUSINESS_NAME.upper()


class Buttons:
    WELCOME = [
        {"id": "quiero_info", "title": "Info"},
        {"id": "iniciar_pedido", "title": "Iniciar pedido"},
    ]
    MENU_PRIMARY = [
        {"id": "rastrear", "title": "Rastrear"},
        {"id": "cotizar", "title": "Consultar envio"},
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
        {"id": "peso_ligero", "title": "Menos 1 kg"},
        {"id": "peso_medio", "title": "1 - 5 kg"},
        {"id": "peso_pesado", "title": "Mas 5 kg"},
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
    def welcome() -> str:
        return (
            f"*{BUSINESS}* - Asistente Virtual\n"
            f"{LINE}\n"
            f"Hola, soy *{config.BOT_NAME}*.\n"
            f"Ruta disponible: *{config.ROUTE_LABEL}*.\n\n"
            "Elige una opcion para empezar:\n"
            f"{LINE}\n"
            "_Toca un boton_"
        )

    @staticmethod
    def welcome_info() -> str:
        return (
            "*INFORMACION DEL SERVICIO*\n"
            f"{LINE}\n"
            "Ruta: *Estados Unidos -> Ecuador*\n\n"
            "*SERVICIOS DISPONIBLES*\n"
            "- Express 24-48h\n"
            "- Estandar 3-5 dias\n"
            "- Economico 5-8 dias\n\n"
            "*TAMANOS ACEPTADOS*\n"
            "Documentos, paquetes pequenos, medianos y grandes.\n"
            "Volumenes especiales se revisan con un agente.\n\n"
            "*VALOR DEL ENVIO*\n"
            "Un agente confirma el valor final segun peso, ciudad, volumen y aduana.\n\n"
            "*RASTREO*\n"
            "Todos los envios incluyen codigo de seguimiento.\n"
            "Ejemplo: *CUR-00001*\n"
            f"{LINE}\n"
            "Listo para comenzar."
        )

    @staticmethod
    def ask_welcome_name() -> str:
        return (
            "*REGISTRO RAPIDO*\n"
            f"{LINE}\n"
            "Para empezar, dime tu nombre completo:"
        )

    @staticmethod
    def ask_welcome_apellido() -> str:
        return "Gracias. Ahora dime tu apellido:"

    @staticmethod
    def ask_welcome_ciudad() -> str:
        return "Perfecto. De que ciudad eres?"

    @staticmethod
    def ask_welcome_phone() -> str:
        return "Perfecto. Ahora dime tu numero de telefono de contacto:"

    @staticmethod
    def welcome_complete(name: str, apellido: str = "") -> str:
        full = f"{name} {apellido}".strip()
        return (
            "*REGISTRO COMPLETADO*\n"
            f"{LINE}\n"
            f"Gracias *{full}*. Ya estas registrado.\n\n"
            "Ahora puedes rastrear paquetes, consultar envios, reportar problemas o hablar con un agente."
        )

    @staticmethod
    def menu() -> str:
        return (
            f"*{BUSINESS}* - Asistente Virtual\n"
            f"{LINE}\n"
            f"Hola, soy *{config.BOT_NAME}*.\n"
            f"Ruta principal: *{config.ROUTE_LABEL}*.\n"
            "Que necesitas hoy?\n"
            f"{LINE}\n"
            "*1.* Rastrear mi paquete\n"
            "*2.* Consultar un envio\n"
            "*3.* Ver mis envios activos\n"
            "*4.* Reportar un problema\n"
            "*5.* Hablar con un agente\n"
            f"{LINE}\n"
            "_Usa los botones o responde con el numero_"
        )

    @staticmethod
    def ask_tracking() -> str:
        return (
            "*RASTREAR PAQUETE*\n"
            f"{LINE}\n"
            "Enviame tu codigo de seguimiento.\n\n"
            "Ejemplo: *CUR-00001*"
        )

    @staticmethod
    def tracking_card(shipment: dict[str, Any], tracking_code: str) -> str:
        status = (shipment.get("estado") or "pendiente").lower()
        return (
            f"== *{BUSINESS}* ==\n"
            "_Entregas rapidas y seguras_\n"
            f"{LINE}\n"
            f"*PAQUETE #{tracking_code}*\n"
            f"{LINE}\n"
            f"Para: *{_value(shipment.get('destinatario'))}*\n"
            f"Destino: *{_value(shipment.get('direccion_destino'))}*\n"
            f"Peso: *{_value(shipment.get('peso'))}*\n"
            f"Servicio: *{_value(shipment.get('servicio_envio'), 'Pendiente')}*\n"
            f"{LINE}\n"
            "*ESTADO DEL ENVIO:*\n"
            f"{_status_lines(status)}\n"
            f"{LINE}\n"
            f"Estimado: *{_value(shipment.get('entrega_estimada'), 'Por confirmar')}*"
        )

    @staticmethod
    def tracking_not_found(code: str) -> str:
        return (
            "*NO ENCONTRE EL PAQUETE*\n"
            f"{LINE}\n"
            f"Codigo consultado: *{code}*\n\n"
            "Revisa que tenga este formato: *CUR-00001*"
        )

    @staticmethod
    def ask_quote_origin() -> str:
        return (
            "*CONSULTAR ENVIO*\n"
            f"{LINE}\n"
            "Primero necesito el origen en *Estados Unidos*.\n"
            "Puedes enviar ubicacion o escribir la direccion."
        )

    @staticmethod
    def ask_quote_destination() -> str:
        return (
            "*DESTINO EN ECUADOR*\n"
            f"{LINE}\n"
            "Ahora dime a que ciudad o direccion de Ecuador llegara el paquete."
        )

    @staticmethod
    def ask_package_type() -> str:
        return (
            "*TIPO DE PAQUETE*\n"
            f"{LINE}\n"
            "Elige la opcion que mas se parezca a tu envio."
        )

    @staticmethod
    def package_type_sections() -> list[dict[str, Any]]:
        return [
            {
                "title": "Tipos de paquete",
                "rows": [
                    {"id": "tipo_documento", "title": "Documentos", "description": "Sobres o papeles"},
                    {"id": "tipo_pequeno", "title": "Paquete pequeno", "description": "Articulos pequenos"},
                    {"id": "tipo_mediano", "title": "Paquete mediano", "description": "Ropa, zapatos o caja"},
                    {"id": "tipo_grande", "title": "Paquete grande", "description": "Caja grande o volumen alto"},
                ],
            }
        ]

    @staticmethod
    def ask_weight() -> str:
        return (
            "*PESO APROXIMADO*\n"
            f"{LINE}\n"
            "Selecciona un rango. El valor final lo confirma un agente."
        )

    @staticmethod
    def quote_options(data: dict[str, Any], options: dict[str, dict[str, Any]]) -> str:
        lines = [
            "*OPCIONES DE ENVIO*",
            LINE,
            f"Origen: *{_value(data.get('origen'))}*",
            f"Destino: *{_value(data.get('destino'))}*",
            f"Paquete: *{_value(data.get('tipo_paquete'))}*",
            f"Peso: *{_value(data.get('peso'))}*",
            LINE,
            "Elige el tipo de servicio:",
        ]
        for service_id in options:
            service = SHIPPING_SERVICES[service_id]
            lines.append(f"- *{service['label']}* ({service['eta']})")
        lines.extend([LINE, "_El valor final lo confirma un agente._"])
        return "\n".join(lines)

    @staticmethod
    def quote_summary(data: dict[str, Any]) -> str:
        return (
            "*CONFIRMAR CONSULTA*\n"
            f"{LINE}\n"
            f"Origen: *{_value(data.get('origen'))}*\n"
            f"Destino: *{_value(data.get('destino'))}*\n"
            f"Paquete: *{_value(data.get('tipo_paquete'))}*\n"
            f"Peso: *{_value(data.get('peso'))}*\n"
            f"Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"Tiempo estimado: *{_value(data.get('entrega_estimada'))}*\n"
            f"{LINE}\n"
            "*Valor:* por confirmar con un agente.\n"
            "_Confirma para registrar tus datos._"
        )

    @staticmethod
    def ask_sender_name() -> str:
        return "*DATOS DEL ENVIO*\n" f"{LINE}\n" "Cual es tu nombre completo?"

    @staticmethod
    def ask_sender_phone() -> str:
        return "Cual es tu numero de telefono?"

    @staticmethod
    def ask_recipient_name() -> str:
        return "Cual es el nombre completo del destinatario?"

    @staticmethod
    def ask_recipient_phone() -> str:
        return "Cual es el telefono del destinatario?"

    @staticmethod
    def ask_exact_destination() -> str:
        return "*DIRECCION FINAL*\n" f"{LINE}\n" "Escribe la direccion exacta en Ecuador."

    @staticmethod
    def ask_instructions() -> str:
        return "*INSTRUCCIONES ESPECIALES*\n" f"{LINE}\n" "Tu paquete necesita algun cuidado?"

    @staticmethod
    def shipment_summary(data: dict[str, Any]) -> str:
        return (
            "*RESUMEN DEL ENVIO*\n"
            f"{LINE}\n"
            f"Remitente: *{_value(data.get('remitente'))}*\n"
            f"Telefono: *{_value(data.get('telefono_remitente'))}*\n"
            f"Destinatario: *{_value(data.get('destinatario'))}*\n"
            f"Telefono dest.: *{_value(data.get('telefono_destinatario'))}*\n"
            f"Origen: *{_value(data.get('origen'))}*\n"
            f"Destino: *{_value(data.get('direccion_destino') or data.get('destino'))}*\n"
            f"Paquete: *{_value(data.get('tipo_paquete'))}*\n"
            f"Peso: *{_value(data.get('peso'))}*\n"
            f"Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"Instrucciones: *{_value(data.get('instrucciones'))}*\n"
            f"{LINE}\n"
            "*Valor:* por confirmar con un agente.\n"
            "Confirmas este envio?"
        )

    @staticmethod
    def shipment_created(tracking_code: str, data: dict[str, Any]) -> str:
        return (
            "*ENVIO REGISTRADO*\n"
            f"{LINE}\n"
            f"Codigo: *{tracking_code}*\n"
            f"Para: *{_value(data.get('destinatario'))}*\n"
            f"Destino: *{_value(data.get('direccion_destino') or data.get('destino'))}*\n"
            f"Servicio: *{_value(data.get('servicio_envio'))}*\n"
            f"{LINE}\n"
            "Un agente confirmara el valor final y se pondra en contacto contigo."
        )

    @staticmethod
    def shipments_list(shipments: list[dict[str, Any]]) -> str:
        if not shipments:
            return "*MIS ENVIOS*\n" f"{LINE}\n" "No tienes envios registrados con este numero todavia."

        lines = ["*MIS ENVIOS ACTIVOS*", LINE]
        for shipment in shipments:
            code = shipment.get("tracking_code") or f"CUR-{int(shipment['id']):05d}"
            lines.extend(
                [
                    f"*{code}*",
                    f"Para: {_value(shipment.get('destinatario'))}",
                    f"Destino: {_value(shipment.get('direccion_destino'))}",
                    f"Estado: {_value(shipment.get('estado'), 'pendiente')}",
                    "",
                ]
            )
        lines.extend([LINE, "_Puedes rastrear uno con su codigo._"])
        return "\n".join(lines)

    @staticmethod
    def report_categories() -> str:
        return "*REPORTAR PROBLEMA*\n" f"{LINE}\n" "Elige el tipo de problema para ayudarte mas rapido."

    @staticmethod
    def ask_report_description(category: str) -> str:
        return (
            f"*{category.upper()}*\n"
            f"{LINE}\n"
            "Cuentame que paso.\n\n"
            "Si tienes codigo de paquete, incluyelo.\n"
            "Ejemplo: *CUR-00012 no llego en fecha*"
        )

    @staticmethod
    def report_created(report_id: int, category: str, tracking_code: str | None = None) -> str:
        code_line = f"Paquete: *{tracking_code}*\n" if tracking_code else ""
        return (
            f"*REPORTE #INC-{report_id:04d}*\n"
            f"{LINE}\n"
            "Tu caso ya fue registrado.\n"
            f"{code_line}"
            f"Tipo: *{category}*\n"
            f"Reportado: *{datetime.now().strftime('%d/%m/%Y %H:%M')}*\n"
            "Agente asignado: *Equipo soporte*\n"
            f"{LINE}\n"
            "Un agente revisara el caso y te contactara."
        )

    @staticmethod
    def agent() -> str:
        return (
            "*HABLAR CON UN AGENTE*\n"
            f"{LINE}\n"
            "Ya avisamos al equipo de soporte.\n"
            f"Horario: *{config.SUPPORT_HOURS}*"
        )

    @staticmethod
    def location_help() -> str:
        return "*ENVIAR UBICACION*\n" f"{LINE}\n" "Toca adjuntar en WhatsApp y elige Ubicacion."

    @staticmethod
    def unknown() -> str:
        return "No entendi tu mensaje. Te dejo el menu para que elijas una opcion."


def build_quote_options(package_type: str, weight: str) -> dict[str, dict[str, Any]]:
    del package_type, weight
    return {
        service_id: {"label": service["label"], "eta": service["eta"]}
        for service_id, service in SHIPPING_SERVICES.items()
    }


def _status_lines(current_status: str) -> str:
    status_index = _status_index(current_status)
    lines = []
    for index, (_, label) in enumerate(STATUS_STEPS):
        if index < status_index:
            marker = "[OK]"
        elif index == status_index:
            marker = "[...]"
        else:
            marker = "[ ]"
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
