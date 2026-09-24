# -*- coding: utf-8 -*-

from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    reverse_original_cost = fields.Boolean(
        string='Reversión a costo original',
        copy=False,
    )

    reverse_original_unit_cost = fields.Float(
        string='Costo original de reversión',
        digits='Product Price',
        copy=False,
    )

    def _create_out_svl(self, forced_quantity=None):
        """
        Valora las reversiones creadas por este módulo al costo
        original de la recepción. El resto de movimientos usan el
        comportamiento estándar de Odoo (AVCO / FIFO).
        """
        normal_moves = self.filtered(
            lambda move: not move.reverse_original_cost
        )
        reverse_moves = self - normal_moves

        svl = self.env['stock.valuation.layer']

        if normal_moves:
            svl |= super(
                StockMove, normal_moves
            )._create_out_svl(forced_quantity=forced_quantity)

        for move in reverse_moves:
            valued_move_lines = move._get_out_move_lines()

            valued_quantity = 0.0
            for move_line in valued_move_lines:
                valued_quantity += (
                    move_line.product_uom_id._compute_quantity(
                        move_line.qty_done,
                        move.product_id.uom_id,
                        rounding_method='HALF-UP',
                    )
                )

            # En el caso de una corrección (forced_quantity) respetamos
            # el signo/número indicado por Odoo.
            if forced_quantity is not None:
                valued_quantity = forced_quantity

            if not valued_quantity:
                continue

            unit_cost = move.reverse_original_unit_cost
            quantity = -valued_quantity
            value = move.company_id.currency_id.round(quantity * unit_cost)

            svl_vals = {
                'product_id': move.product_id.id,
                'value': value,
                'unit_cost': unit_cost,
                'quantity': quantity,
                # En AVCO las capas salientes no mantienen remanente.
                'remaining_qty': 0.0,
                'remaining_value': 0.0,
            }
            svl_vals.update(move._prepare_common_svl_vals())

            svl |= self.env['stock.valuation.layer'].sudo().create(svl_vals)

        return svl