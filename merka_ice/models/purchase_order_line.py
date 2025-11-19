from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Campos ICE
    ice_litros = fields.Float(
        string='Litros',
        digits=(12, 3),
        default=0.0,
        help='Cantidad en litros para calcular alícuota específica'
    )

    ice_alicuota_especifica = fields.Float(
        string='Alíc. Específica (Bs/L)',
        digits=(12, 2),
        readonly=True,
        help='Alícuota específica del producto'
    )

    ice_alicuota_porcentual = fields.Float(
        string='Alíc. Porcentual (%)',
        digits=(12, 2),
        readonly=True,
        help='Alícuota porcentual del producto'
    )

    ice_monto_especifico = fields.Monetary(
        string='ICE Específico',
        compute='_compute_ice_montos',
        store=True,
        help='Monto ICE por alícuota específica'
    )

    ice_monto_porcentual = fields.Monetary(
        string='ICE Porcentual',
        compute='_compute_ice_montos',
        store=True,
        help='Monto ICE por alícuota porcentual'
    )

    ice_monto_total = fields.Monetary(
        string='ICE Total',
        compute='_compute_ice_montos',
        store=True,
        help='Suma de ICE específico + ICE porcentual'
    )

    price_subtotal_con_ice = fields.Monetary(
        string='Subtotal + ICE',
        compute='_compute_price_subtotal_con_ice',
        store=True,
        help='Subtotal de la línea más el ICE total'
    )

    @api.onchange('product_id')
    def _onchange_product_ice(self):
        """Carga las alícuotas del producto al seleccionarlo"""
        if self.product_id:
            self.ice_alicuota_especifica = self.product_id.ice_alicuota_especifica
            self.ice_alicuota_porcentual = self.product_id.ice_alicuota_porcentual
            # Si tiene alícuota específica, inicializar litros con la cantidad
            if self.ice_alicuota_especifica > 0 and self.ice_litros == 0:
                self.ice_litros = self.product_qty

    @api.onchange('product_qty')
    def _onchange_product_qty_ice(self):
        """Sincroniza litros con cantidad si hay alícuota específica"""
        if self.ice_alicuota_especifica > 0 and self.ice_litros == 0:
            self.ice_litros = self.product_qty

    @api.depends('ice_litros', 'ice_alicuota_especifica',
                 'price_unit', 'product_qty', 'ice_alicuota_porcentual')
    def _compute_ice_montos(self):
        """Calcula los montos de ICE (específico, porcentual y total)"""
        for line in self:
            # ICE Específico: litros × alícuota específica
            ice_especifico = line.ice_litros * line.ice_alicuota_especifica

            # ICE Porcentual: (precio unitario × cantidad) × (porcentaje / 100)
            subtotal = line.price_unit * line.product_qty
            ice_porcentual = subtotal * (line.ice_alicuota_porcentual / 100)

            # Asignar valores
            line.ice_monto_especifico = ice_especifico
            line.ice_monto_porcentual = ice_porcentual
            line.ice_monto_total = ice_especifico + ice_porcentual

    @api.depends('price_subtotal', 'ice_monto_total')
    def _compute_price_subtotal_con_ice(self):
        """Calcula el subtotal incluyendo el ICE"""
        for line in self:
            line.price_subtotal_con_ice = line.price_subtotal + line.ice_monto_total

    @api.constrains('ice_litros')
    def _check_ice_litros(self):
        """Valida que los litros no sean negativos"""
        for line in self:
            if line.ice_litros < 0:
                raise ValidationError(
                    'La cantidad de litros no puede ser negativa.'
                )