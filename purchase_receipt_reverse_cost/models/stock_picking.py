# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_reverse_purchase_receipt(self):
        self.ensure_one()

        if self.state != 'done':
            raise UserError(_('La recepción debe estar validada.'))

        if self.picking_type_code != 'incoming':
            raise UserError(_('Esta operación no es una recepción.'))

        purchase_moves = self.move_ids.filtered(
            lambda move: move.purchase_line_id
        )

        if not purchase_moves:
            raise UserError(_(
                'Esta recepción no contiene movimientos '
                'relacionados con una orden de compra.'
            ))

        view = self.env.ref(
            'purchase_receipt_reverse_cost.'
            'view_stock_return_picking_reverse_cost_form'
        )

        context = dict(self.env.context)
        context.update({
            'active_id': self.id,
            'active_ids': [self.id],
            'active_model': 'stock.picking',
            'reverse_receipt_original_cost': True,
        })

        return {
            'name': _('Revertir recepción'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.return.picking',
            'view_mode': 'form',
            'view_id': view.id,
            'views': [(view.id, 'form')],
            'target': 'new',
            'context': context,
        }