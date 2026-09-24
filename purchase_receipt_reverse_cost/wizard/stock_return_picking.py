# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import (
    float_compare,
    float_is_zero,
    float_round,
)


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'

    quantity_received = fields.Float(
        string='Cantidad recibida',
        digits='Product Unit of Measure',
        compute='_compute_reverse_information',
    )

    quantity_reverted = fields.Float(
        string='Cantidad ya revertida',
        digits='Product Unit of Measure',
        compute='_compute_reverse_information',
    )

    quantity_available = fields.Float(
        string='Cantidad disponible',
        digits='Product Unit of Measure',
        compute='_compute_reverse_information',
    )

    original_unit_cost = fields.Float(
        string='Costo original',
        digits='Product Price',
        compute='_compute_reverse_information',
    )

    original_total_value = fields.Float(
        string='Valor original',
        digits='Product Price',
        compute='_compute_reverse_information',
    )

    @api.depends(
        'move_id',
        'move_id.product_qty',
        'move_id.returned_move_ids',
        'move_id.returned_move_ids.state',
        'move_id.returned_move_ids.product_qty',
        'move_id.stock_valuation_layer_ids',
    )
    def _compute_reverse_information(self):
        for line in self:
            move = line.move_id

            line.quantity_received = 0.0
            line.quantity_reverted = 0.0
            line.quantity_available = 0.0
            line.original_unit_cost = 0.0
            line.original_total_value = 0.0

            if not move:
                continue

            # CANTIDAD RECIBIDA
            quantity_received = move.product_qty

            # CANTIDAD YA REVERTIDA
            quantity_reverted = 0.0
            for returned_move in move.returned_move_ids:
                if returned_move.state == 'done':
                    qty = returned_move.product_uom._compute_quantity(
                        returned_move.product_qty,
                        move.product_uom,
                        rounding_method='HALF-UP',
                    )
                    quantity_reverted += qty

            # CANTIDAD DISPONIBLE
            quantity_available = quantity_received
            for returned_move in move.returned_move_ids:
                if returned_move.state in ('partially_available', 'assigned'):
                    reserved_qty = sum(
                        returned_move.move_line_ids.mapped('reserved_qty')
                    )
                    reserved_qty = move.product_id.uom_id._compute_quantity(
                        reserved_qty,
                        move.product_uom,
                        rounding_method='HALF-UP',
                    )
                    quantity_available -= reserved_qty
                elif returned_move.state == 'done':
                    qty = returned_move.product_uom._compute_quantity(
                        returned_move.product_qty,
                        move.product_uom,
                        rounding_method='HALF-UP',
                    )
                    quantity_available -= qty

            quantity_available = float_round(
                quantity_available,
                precision_rounding=move.product_uom.rounding,
            )

            if quantity_available < 0 and float_is_zero(
                quantity_available,
                precision_rounding=move.product_uom.rounding,
            ):
                quantity_available = 0.0

            # COSTO ORIGINAL (a partir de las SVL del movimiento original)
            layers = move.sudo().stock_valuation_layer_ids
            original_quantity = sum(layers.mapped('quantity'))
            original_value = sum(layers.mapped('value'))

            original_unit_cost = 0.0
            if not float_is_zero(
                original_quantity,
                precision_rounding=move.product_id.uom_id.rounding,
            ):
                original_unit_cost = abs(original_value / original_quantity)

            line.quantity_received = quantity_received
            line.quantity_reverted = quantity_reverted
            line.quantity_available = quantity_available
            line.original_unit_cost = original_unit_cost
            line.original_total_value = original_unit_cost * quantity_received


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def create_returns(self):
        if not self.env.context.get('reverse_receipt_original_cost'):
            return super().create_returns()

        for wizard in self:
            picking = wizard.picking_id

            if not picking:
                raise UserError(_('No se encontró la recepción.'))

            if picking.state != 'done':
                raise UserError(_('La recepción debe estar validada.'))

            if picking.picking_type_code != 'incoming':
                raise UserError(_('La operación debe ser una recepción.'))

            # VALIDAR CANTIDADES
            for line in wizard.product_return_moves:
                if not line.move_id:
                    raise UserError(_(
                        'Todas las líneas deben corresponder '
                        'a un movimiento original.'
                    ))

                quantity = line.quantity

                if float_is_zero(
                    quantity,
                    precision_rounding=line.product_id.uom_id.rounding,
                ):
                    continue

                if float_compare(
                    quantity,
                    line.quantity_available,
                    precision_rounding=line.product_id.uom_id.rounding,
                ) > 0:
                    raise UserError(_(
                        'La cantidad a revertir de "%s" '
                        'no puede ser mayor que la cantidad disponible.\n\n'
                        'Recibida: %s\n'
                        'Ya revertida: %s\n'
                        'Disponible: %s\n'
                        'Solicitada: %s'
                    ) % (
                        line.product_id.display_name,
                        line.quantity_received,
                        line.quantity_reverted,
                        line.quantity_available,
                        quantity,
                    ))

            # CREAR DEVOLUCIÓN NATIVA (UNA SOLA VEZ)
            new_picking_id, picking_type_id = wizard._create_returns()
            new_picking = self.env['stock.picking'].browse(new_picking_id)

            # GUARDAR COSTO HISTÓRICO EN EL NUEVO MOVIMIENTO
            for line in wizard.product_return_moves:
                if float_is_zero(
                    line.quantity,
                    precision_rounding=line.product_id.uom_id.rounding,
                ):
                    continue

                original_move = line.move_id
                original_unit_cost = line.original_unit_cost

                new_moves = new_picking.move_ids.filtered(
                    lambda m: m.origin_returned_move_id == original_move
                )

                if not new_moves:
                    raise UserError(_(
                        'No se encontró el movimiento de reversión '
                        'correspondiente a "%s".'
                    ) % line.product_id.display_name)

                new_moves.write({
                    'reverse_original_cost': True,
                    'reverse_original_unit_cost': original_unit_cost,
                })

            # NO volver a llamar _create_returns()
            # ---------------------------------------------------------

            # RESERVAR
            new_picking.action_assign()

            not_available_moves = new_picking.move_ids.filtered(
                lambda move: move.state != 'assigned'
            )

            if not_available_moves:
                products = ', '.join(
                    not_available_moves.mapped('product_id.display_name')
                )
                raise UserError(_(
                    'No existe suficiente stock disponible '
                    'para revertir completamente la recepción.\n\n'
                    'Productos: %s'
                ) % products)

            new_picking.action_set_quantities_to_reservation()

            incomplete_moves = new_picking.move_ids.filtered(
                lambda move: float_compare(
                    move.quantity_done,
                    move.product_uom_qty,
                    precision_rounding=move.product_uom.rounding,
                ) < 0
            )

            if incomplete_moves:
                products = ', '.join(
                    incomplete_moves.mapped('product_id.display_name')
                )
                raise UserError(_(
                    'No se pudo establecer la cantidad completa '
                    'para los productos: %s'
                ) % products)

            # VALIDAR
            new_picking.with_context(
                skip_immediate=True,
                skip_backorder=True,
            ).button_validate()

            # MENSAJES
            picking.message_post(body=_(
                'Se creó y validó la reversión '
                '<b>%s</b> utilizando el costo original '
                'de la recepción.'
            ) % new_picking.name)

            new_picking.message_post(body=_(
                'Reversión automática de la recepción '
                '<b>%s</b> utilizando costo histórico original.'
            ) % picking.name)

            return {
                'name': _('Reversión de recepción'),
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'res_id': new_picking.id,
                'context': {
                    'default_picking_type_id': picking_type_id,
                },
            }

        return True