from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos de totales ICE
    ice_total_especifico = fields.Monetary(
        string='Total ICE Específico',
        compute='_compute_ice_totals',
        store=True,
        help='Suma total de ICE por alícuotas específicas'
    )

    ice_total_porcentual = fields.Monetary(
        string='Total ICE Porcentual',
        compute='_compute_ice_totals',
        store=True,
        help='Suma total de ICE por alícuotas porcentuales'
    )

    ice_total = fields.Monetary(
        string='Total ICE',
        compute='_compute_ice_totals',
        store=True,
        help='Suma total de todos los ICE (específico + porcentual)'
    )

    amount_total_con_ice = fields.Monetary(
        string='Total con ICE',
        compute='_compute_ice_totals',
        store=True,
        help='Monto total de la factura incluyendo ICE'
    )

    @api.depends('invoice_line_ids.ice_monto_especifico',
                 'invoice_line_ids.ice_monto_porcentual',
                 'invoice_line_ids.ice_monto_total',
                 'amount_total',
                 'move_type')
    def _compute_ice_totals(self):
        """Calcula los totales de ICE de la factura de compra"""
        for move in self:
            # Solo calcular ICE para facturas de compra
            if move.move_type not in ['in_invoice', 'in_refund']:
                move.ice_total_especifico = 0.0
                move.ice_total_porcentual = 0.0
                move.ice_total = 0.0
                move.amount_total_con_ice = move.amount_total
                continue

            # Calcular totales de ICE
            ice_especifico = sum(move.invoice_line_ids.mapped('ice_monto_especifico'))
            ice_porcentual = sum(move.invoice_line_ids.mapped('ice_monto_porcentual'))
            ice_total = sum(move.invoice_line_ids.mapped('ice_monto_total'))

            move.ice_total_especifico = ice_especifico
            move.ice_total_porcentual = ice_porcentual
            move.ice_total = ice_total
            move.amount_total_con_ice = move.amount_total + ice_total