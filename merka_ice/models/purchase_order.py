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

    @api.depends('order_line.ice_monto_especifico',
                 'order_line.ice_monto_porcentual',
                 'order_line.ice_monto_total')
    def _compute_ice_totals(self):
        """Calcula los totales de ICE de la orden de compra"""
        for order in self:
            ice_especifico = sum(order.order_line.mapped('ice_monto_especifico'))
            ice_porcentual = sum(order.order_line.mapped('ice_monto_porcentual'))
            ice_total = ice_especifico + ice_porcentual

            order.ice_total_especifico = ice_especifico
            order.ice_total_porcentual = ice_porcentual
            order.ice_total = ice_total

    @api.depends('order_line.price_total', 'ice_total')
    def _compute_amount(self):
        # Primero ejecutamos el cálculo original de Odoo
        super()._compute_amount()

        # Luego sumamos el ICE al total
        for order in self:
            # amount_untaxed y amount_tax ya fueron calculados por super()
            # Solo sumamos ICE al total
            order.amount_total = order.amount_untaxed + order.amount_tax + order.ice_total