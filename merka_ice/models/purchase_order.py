from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

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
        help='Monto total de la orden incluyendo ICE'
    )

    @api.depends('order_line.ice_monto_especifico',
                 'order_line.ice_monto_porcentual',
                 'order_line.ice_monto_total',
                 'amount_total')
    def _compute_ice_totals(self):
        """Calcula los totales de ICE de la orden de compra"""
        for order in self:
            ice_especifico = sum(order.order_line.mapped('ice_monto_especifico'))
            ice_porcentual = sum(order.order_line.mapped('ice_monto_porcentual'))
            ice_total = sum(order.order_line.mapped('ice_monto_total'))

            order.ice_total_especifico = ice_especifico
            order.ice_total_porcentual = ice_porcentual
            order.ice_total = ice_total
            order.amount_total_con_ice = order.amount_total + ice_total