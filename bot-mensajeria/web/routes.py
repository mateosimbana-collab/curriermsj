import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, request, send_from_directory

import config
from bot.courier_bot import CourierBot
from domain.models import IncomingMessage


logger = logging.getLogger(__name__)

try:
    BUSINESS_TZ = ZoneInfo("America/Guayaquil")
except Exception:
    BUSINESS_TZ = timezone.utc


class WhatsAppWebhookParser:
    @staticmethod
    def parse(payload: dict[str, Any]) -> list[IncomingMessage]:
        events: list[IncomingMessage] = []

        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    event = WhatsAppWebhookParser._parse_message(message)
                    if event:
                        events.append(event)

        return events

    @staticmethod
    def _parse_message(message: dict[str, Any]) -> IncomingMessage | None:
        phone_number = message.get("from")
        if not phone_number:
            return None

        message_type = message.get("type", "text")
        if message_type == "text":
            return IncomingMessage(
                phone_number=phone_number,
                text=message.get("text", {}).get("body", ""),
                message_type="text",
                raw=message,
            )

        if message_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                reply = interactive.get("button_reply", {})
                return IncomingMessage(
                    phone_number=phone_number,
                    text=reply.get("id") or reply.get("title", ""),
                    message_type="interactive_button",
                    raw=message,
                )
            if interactive.get("type") == "list_reply":
                reply = interactive.get("list_reply", {})
                return IncomingMessage(
                    phone_number=phone_number,
                    text=reply.get("id") or reply.get("title", ""),
                    message_type="interactive_list",
                    raw=message,
                )

        if message_type == "location":
            location = message.get("location", {})
            return IncomingMessage(
                phone_number=phone_number,
                text="ubicacion_recibida",
                message_type="location",
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                raw=message,
            )

        if message_type == "reaction":
            reaction = message.get("reaction", {})
            return IncomingMessage(
                phone_number=phone_number,
                text=f"Reacción: {reaction.get('emoji', '')}",
                message_type="reaction",
                raw=message,
            )

        return IncomingMessage(
            phone_number=phone_number,
            text="",
            message_type=message_type,
            raw=message,
        )


def _safe_table_get(bot: CourierBot, table_name: str, query: str) -> list[dict[str, Any]]:
    try:
        data = bot.repository._request("GET", f"{bot.repository._table(table_name)}?{query}")
        return data if isinstance(data, list) else []
    except Exception as exc:
        logger.warning("No se pudo leer tabla opcional %s: %s", table_name, exc)
        return []


def _parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(BUSINESS_TZ)
    except (TypeError, ValueError):
        return None


def _money(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _empty_cashflow(today_start: datetime) -> dict[str, dict[str, float | str]]:
    start = today_start - timedelta(days=13)
    rows: dict[str, dict[str, float | str]] = {}
    for offset in range(14):
        key = (start + timedelta(days=offset)).date().isoformat()
        rows[key] = {"date": key, "ingresos": 0.0, "egresos": 0.0}
    return rows


def create_app(bot: CourierBot) -> Flask:
    app = Flask(__name__)

    @app.get("/webhook")
    def verify_webhook():
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == config.WEBHOOK_VERIFY_TOKEN:
            logger.info("Webhook verificado correctamente")
            return challenge or "", 200

        logger.warning("Intento de verificación fallido")
        return "Forbidden", 403

    @app.post("/webhook")
    def receive_message():
        payload = request.get_json(silent=True) or {}
        if payload.get("object") != "whatsapp_business_account":
            return "Not Found", 404

        if payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("statuses"):
            return "OK", 200

        try:
            events = WhatsAppWebhookParser.parse(payload)
            logger.info("Webhook recibido: %d mensajes", len(events))
            for event in events:
                logger.info("Procesando mensaje de %s: %s", event.phone_number, event.text[:50])
                try:
                    bot.process(event)
                except Exception as exc:
                    logger.exception("Error procesando mensaje de %s: %s", event.phone_number, exc)
        except Exception as exc:
            logger.exception("Error parseando webhook: %s", exc)

        return "OK", 200

    @app.get("/api/dashboard")
    def api_dashboard():
        stats = bot.repository.get_dashboard_stats()

        try:
            import requests as _r
            wa_resp = _r.get(
                f"{config.WHATSAPP_API_URL}/{config.PHONE_NUMBER_ID}",
                headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
                timeout=5,
            )
            whatsapp_ok = 200 <= wa_resp.status_code < 300
        except Exception:
            whatsapp_ok = False

        try:
            import httpx as _hx
            su_resp = _hx.get(
                f"{config.SUPABASE_URL}/rest/v1/envios?select=id&limit=1",
                headers={
                    "apikey": config.SUPABASE_KEY,
                    "Authorization": f"Bearer {config.SUPABASE_KEY}",
                },
                timeout=5,
            )
            supabase_ok = su_resp.status_code < 300
        except Exception:
            supabase_ok = False

        return jsonify({
            "status": "ok",
            "service": "currier_bot",
            "time": datetime.now().isoformat(),
            "total_shipments": stats["total_shipments"],
            "shipments_today": stats["shipments_today"],
            "active_users": stats["active_users"],
            "total_reports": stats["total_reports"],
            "open_reports": stats["open_reports"],
            "recent_shipments": stats["recent_shipments"],
            "active_sessions": stats["active_sessions"],
            "shipments_by_day": stats["shipments_by_day"],
            "services": {
                "bot": True,
                "whatsapp": whatsapp_ok,
                "supabase": supabase_ok,
            },
        }), 200

    @app.get("/dashboard")
    def dashboard():
        dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard")
        return send_from_directory(dashboard_dir, "owner.html")

    @app.get("/dashboard/soporte")
    def dashboard_soporte():
        dashboard_dir = os.path.join(os.path.dirname(__file__), "..", "..", "dashboard")
        return send_from_directory(dashboard_dir, "support.html")

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "service": "currier_bot",
                "time": datetime.now().isoformat(),
            }
        ), 200

    @app.get("/api/envios")
    def get_all_envios():
        try:
            url = f"{bot.repository._table(bot.repository.table_envios)}?select=*&order=creado_en.desc"
            data = bot.repository._request("GET", url)
            return jsonify(data), 200
        except Exception as e:
            logger.exception("Error al obtener envíos: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/system-stats")
    def get_system_stats():
        try:
            clientes_url = f"{bot.repository._table(bot.repository.table_clientes)}?select=*"
            estados_url = f"{bot.repository._table(bot.repository.table_estado)}?select=*"
            reportes_url = f"{bot.repository._table(bot.repository.table_reportes)}?select=*&order=creado_en.desc"
            
            clientes = bot.repository._request("GET", clientes_url)
            estados = bot.repository._request("GET", estados_url)
            reportes = bot.repository._request("GET", reportes_url)
            
            return jsonify({
                "clientes": clientes,
                "estados": estados,
                "reportes": reportes
            }), 200
        except Exception as e:
            logger.exception("Error al obtener estadísticas del sistema: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/earnings")
    def get_earnings():
        try:
            url = f"{bot.repository._table(bot.repository.table_envios)}?select=valor_cotizado,creado_en,servicio_envio&order=creado_en.desc"
            data = bot.repository._request("GET", url)
            total = 0
            today = 0
            week = 0
            month = 0
            now = datetime.now(BUSINESS_TZ)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)
            by_month = {}
            for s in data:
                val = float(s.get("valor_cotizado") or 0)
                total += val
                created = s.get("creado_en", "")
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        dt = dt.astimezone(BUSINESS_TZ)
                        if dt >= today_start: today += val
                        if dt >= week_start: week += val
                        if dt >= month_start: month += val
                        key = dt.strftime("%Y-%m")
                        by_month[key] = by_month.get(key, 0) + val
                    except (TypeError, ValueError) as exc:
                        logger.warning("No se pudo procesar fecha de ganancia '%s': %s", created, exc)
            return jsonify({"total": round(total,2), "today": round(today,2), "week": round(week,2), "month": round(month,2), "by_month": by_month}), 200
        except Exception as e:
            logger.exception("Error al obtener ganancias: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/finance-summary")
    def get_finance_summary():
        try:
            now = datetime.now(BUSINESS_TZ)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            month_start = today_start.replace(day=1)

            envios = _safe_table_get(
                bot,
                "envios",
                "select=valor_cotizado,costo_producto,servicio_envio,tipo_paquete,creado_en&order=creado_en.desc",
            )
            if not envios:
                envios = _safe_table_get(
                    bot,
                    "envios",
                    "select=valor_cotizado,servicio_envio,tipo_paquete,creado_en&order=creado_en.desc",
                )
            movimientos = _safe_table_get(
                bot,
                "movimientos_financieros",
                "select=tipo,categoria,descripcion,monto,tipo_gasto,fecha,creado_en&order=fecha.desc",
            )
            planilla = _safe_table_get(
                bot,
                "planilla_personal",
                "select=nombre,cargo,sueldo,fecha_pago,descuentos,estado_pago,creado_en&order=fecha_pago.desc",
            )
            productos = _safe_table_get(
                bot,
                "margenes_producto",
                "select=producto,categoria,precio_venta,costo_producto,unidades,creado_en&order=creado_en.desc",
            )

            shipment_income_month = 0.0
            shipment_income_today = 0.0
            shipment_cost_month = 0.0
            category_totals: dict[str, dict[str, float]] = {}
            for envio in envios:
                created = _parse_dt(envio.get("creado_en"))
                amount = _money(envio.get("valor_cotizado"))
                cost = _money(envio.get("costo_producto"))
                category = envio.get("servicio_envio") or envio.get("tipo_paquete") or "Sin categoria"
                bucket = category_totals.setdefault(category, {"revenue": 0.0, "cost": 0.0})
                bucket["revenue"] += amount
                bucket["cost"] += cost
                if created and created >= month_start:
                    shipment_income_month += amount
                    shipment_cost_month += cost
                    if created >= today_start:
                        shipment_income_today += amount

            cash_income_month = shipment_income_month
            cash_income_today = shipment_income_today
            fixed_expenses = 0.0
            variable_expenses = 0.0
            operating_expenses = 0.0
            expense_rows = []
            cashflow_by_day = _empty_cashflow(today_start)
            for mov in movimientos:
                date = _parse_dt(mov.get("fecha") or mov.get("creado_en"))
                amount = _money(mov.get("monto"))
                if not date or date < month_start:
                    continue
                tipo = (mov.get("tipo") or "").lower()
                gasto_tipo = (mov.get("tipo_gasto") or "").lower()
                day_key = date.date().isoformat()
                if tipo == "ingreso":
                    cash_income_month += amount
                    cashflow_by_day.setdefault(day_key, {"date": day_key, "ingresos": 0.0, "egresos": 0.0})
                    cashflow_by_day[day_key]["ingresos"] += amount
                    if date >= today_start:
                        cash_income_today += amount
                else:
                    operating_expenses += amount
                    if gasto_tipo == "fijo":
                        fixed_expenses += amount
                    else:
                        variable_expenses += amount
                    cashflow_by_day.setdefault(day_key, {"date": day_key, "ingresos": 0.0, "egresos": 0.0})
                    cashflow_by_day[day_key]["egresos"] += amount
                    expense_rows.append({
                        "categoria": mov.get("categoria") or "Sin categoria",
                        "descripcion": mov.get("descripcion") or "",
                        "tipo_gasto": mov.get("tipo_gasto") or "variable",
                        "monto": round(amount, 2),
                        "fecha": date.date().isoformat(),
                    })

            payroll_month = 0.0
            payroll_rows = []
            for item in planilla:
                pay_date = _parse_dt(item.get("fecha_pago") or item.get("creado_en"))
                salary = _money(item.get("sueldo"))
                discount = _money(item.get("descuentos"))
                net_salary = max(salary - discount, 0)
                if pay_date and pay_date >= month_start:
                    payroll_month += net_salary
                payroll_rows.append({
                    "nombre": item.get("nombre") or "",
                    "cargo": item.get("cargo") or "",
                    "sueldo": round(salary, 2),
                    "descuentos": round(discount, 2),
                    "neto": round(net_salary, 2),
                    "fecha_pago": pay_date.date().isoformat() if pay_date else "",
                    "estado_pago": item.get("estado_pago") or "pendiente",
                })

            product_margin_rows = []
            for item in productos:
                revenue = _money(item.get("precio_venta")) * max(int(item.get("unidades") or 1), 1)
                cost = _money(item.get("costo_producto")) * max(int(item.get("unidades") or 1), 1)
                margin = ((revenue - cost) / revenue * 100) if revenue else 0.0
                product_margin_rows.append({
                    "producto": item.get("producto") or "",
                    "categoria": item.get("categoria") or "Sin categoria",
                    "ingresos": round(revenue, 2),
                    "costo": round(cost, 2),
                    "margen": round(margin, 2),
                })

            category_margins = []
            for category, totals in category_totals.items():
                revenue = totals["revenue"]
                cost = totals["cost"]
                margin = ((revenue - cost) / revenue * 100) if revenue else 0.0
                category_margins.append({
                    "categoria": category,
                    "ingresos": round(revenue, 2),
                    "costo": round(cost, 2),
                    "margen": round(margin, 2),
                })

            total_expenses_month = operating_expenses + payroll_month + shipment_cost_month
            net_profit_month = cash_income_month - total_expenses_month
            margin_month = (net_profit_month / cash_income_month * 100) if cash_income_month else 0.0
            variable_rate = (variable_expenses + shipment_cost_month) / cash_income_month if cash_income_month else 0.0
            contribution_rate = max(1 - variable_rate, 0.01)
            break_even_month = (fixed_expenses + payroll_month) / contribution_rate

            return jsonify({
                "income_today": round(cash_income_today, 2),
                "income_month": round(cash_income_month, 2),
                "expenses_month": round(total_expenses_month, 2),
                "fixed_expenses": round(fixed_expenses, 2),
                "variable_expenses": round(variable_expenses + shipment_cost_month, 2),
                "payroll_month": round(payroll_month, 2),
                "cost_of_goods_sold": round(shipment_cost_month, 2),
                "net_profit_month": round(net_profit_month, 2),
                "margin_month": round(margin_month, 2),
                "break_even_month": round(break_even_month, 2),
                "cashflow_by_day": list(cashflow_by_day.values()),
                "expense_rows": expense_rows[:20],
                "payroll_rows": payroll_rows[:20],
                "category_margins": category_margins[:20],
                "product_margins": product_margin_rows[:20],
            }), 200
        except Exception as e:
            logger.exception("Error al obtener resumen financiero: %s", e)
            return jsonify({"error": str(e)}), 500

    @app.get("/api/logs")
    def get_logs():
        try:
            log_path = os.path.join(os.path.dirname(__file__), "..", "app.err")
            logs = []
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                for line in lines[-200:]:
                    logs.append(line.rstrip())
            return jsonify(logs[-100:]), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.get("/api/test-results")
    def get_test_results():
        try:
            results_path = os.path.join(os.path.dirname(__file__), "..", "test_results.json")
            if os.path.exists(results_path):
                with open(results_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return jsonify(data), 200
            tests_path = os.path.join(os.path.dirname(__file__), "..", "tests", "unit")
            py_files = [f for f in os.listdir(tests_path) if f.endswith(".py") and f.startswith("test_")]
            return jsonify({
                "status": "no_results",
                "summary": {
                    "total": 0, "passed": 0, "failed": 0, "errors": 0,
                },
                "test_files": [f.replace(".py", "") for f in sorted(py_files)],
                "message": "Ejecuta run_tests.bat para generar resultados",
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.after_request
    def add_cors_headers(response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        return response

    return app
