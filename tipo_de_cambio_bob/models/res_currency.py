# -*- coding: utf-8 -*-
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

BCB_API_URL = "https://api.factura.bo/ExchangeRate"
_REQUEST_TIMEOUT = 15


class ResCurrency(models.Model):
    _inherit = "res.currency"

    @api.model
    def _cron_update_bcb_rates(self):
        """Actualiza las tasas BOB/USD/UFV desde api.factura.bo.

        Odoo 16 Community almacena la tasa técnica en ``res.currency.rate.rate``.
        El campo ``inverse_company_rate`` es calculado/inverso y puede escribirse
        mediante su inversa; por eso se usa aquí para expresar directamente:

        * Empresa BOB: 1 USD = X BOB.
        * Empresa USD: 1 BOB = X USD.
        """
        try:
            request = Request(
                BCB_API_URL,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Odoo/16 SimplifyIT Exchange Rate",
                },
                method="GET",
            )
            with urlopen(request, timeout=_REQUEST_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            _logger.error(
                "BCB Exchange Rate: HTTP %s al consultar api.factura.bo: %s",
                exc.code,
                exc.reason,
            )
            return False
        except URLError as exc:
            _logger.error(
                "BCB Exchange Rate: error de conexión con api.factura.bo: %s",
                exc.reason,
            )
            return False
        except (TimeoutError, OSError) as exc:
            _logger.error(
                "BCB Exchange Rate: error de red/timeout con api.factura.bo: %s",
                exc,
            )
            return False
        except (ValueError, UnicodeDecodeError) as exc:
            _logger.error(
                "BCB Exchange Rate: respuesta JSON inválida: %s",
                exc,
            )
            return False

        if not isinstance(payload, dict):
            _logger.error("BCB Exchange Rate: la API no devolvió un objeto JSON.")
            return False

        if not payload.get("ok"):
            _logger.error(
                "BCB Exchange Rate: la API devolvió error: %s",
                payload.get("error"),
            )
            return False

        datos = payload.get("datos") or {}
        usd_bob = self._to_positive_float(datos.get("usd_bob"))
        ufv_bob = self._to_positive_float(datos.get("ufv_bob"))

        if not usd_bob:
            _logger.error(
                "BCB Exchange Rate: campo usd_bob ausente o inválido en la respuesta."
            )
            return False

        today = fields.Date.context_today(self)
        company = self.env.company
        base = company.currency_id.name

        if base == "BOB":
            self._actualizar_desde_bob(today, company, usd_bob, ufv_bob)
        elif base == "USD":
            self._actualizar_desde_usd(today, company, usd_bob, ufv_bob)
        else:
            _logger.warning(
                "BCB Exchange Rate: la moneda principal de la empresa es '%s'. "
                "Este módulo solo soporta BOB y USD como moneda base.",
                base,
            )
            return False

        return True

    @staticmethod
    def _to_positive_float(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return None
        return value if value > 0 else None

    def _get_currency(self, code):
        return self.env["res.currency"].sudo().search(
            [("name", "=", code)], limit=1
        )

    def _actualizar_desde_bob(self, today, company, usd_bob, ufv_bob):
        """Empresa con moneda principal BOB.

        1 USD = usd_bob BOB.
        1 UFV = ufv_bob BOB.
        """
        usd = self._get_currency("USD")
        if usd:
            self._actualizar_tasa(usd, company, today, usd_bob)
            _logger.info("BCB: USD actualizado -> 1 USD = %.6f BOB", usd_bob)
        else:
            _logger.warning("BCB Exchange Rate: moneda USD no encontrada en Odoo.")

        if ufv_bob:
            ufv = self._get_currency("UFV")
            if ufv:
                self._actualizar_tasa(ufv, company, today, ufv_bob)
                _logger.info("BCB: UFV actualizado -> 1 UFV = %.6f BOB", ufv_bob)
            else:
                _logger.warning("BCB Exchange Rate: moneda UFV no encontrada en Odoo.")

    def _actualizar_desde_usd(self, today, company, usd_bob, ufv_bob):
        """Empresa con moneda principal USD.

        1 BOB = 1 / usd_bob USD.
        1 UFV = ufv_bob / usd_bob USD.
        """
        bob_usd = round(1.0 / usd_bob, 6)
        bob = self._get_currency("BOB")
        if bob:
            self._actualizar_tasa(bob, company, today, bob_usd)
            _logger.info("BCB: BOB actualizado -> 1 BOB = %.6f USD", bob_usd)
        else:
            _logger.warning("BCB Exchange Rate: moneda BOB no encontrada en Odoo.")

        if ufv_bob:
            ufv_usd = round(ufv_bob / usd_bob, 6)
            ufv = self._get_currency("UFV")
            if ufv:
                self._actualizar_tasa(ufv, company, today, ufv_usd)
                _logger.info("BCB: UFV actualizado -> 1 UFV = %.6f USD", ufv_usd)
            else:
                _logger.warning("BCB Exchange Rate: moneda UFV no encontrada en Odoo.")

    def _actualizar_tasa(self, currency, company, date, inverse_company_rate):
        """Crea o actualiza la tasa de una moneda para una empresa y fecha.

        En Odoo 16, ``inverse_company_rate`` representa las unidades de moneda
        de la compañía por una unidad de la moneda extranjera.
        """
        CurrencyRate = self.env["res.currency.rate"].sudo()
        existing = CurrencyRate.search(
            [
                ("currency_id", "=", currency.id),
                ("name", "=", date),
                ("company_id", "=", company.id),
            ],
            limit=1,
        )

        vals = {
            "currency_id": currency.id,
            "name": date,
            "company_id": company.id,
            "inverse_company_rate": inverse_company_rate,
        }

        if existing:
            existing.write(vals)
        else:
            CurrencyRate.create(vals)
