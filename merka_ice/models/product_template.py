from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos para alícuotas ICE
    ice_alicuota_especifica = fields.Float(
        string='Alícuota Específica (Bs/Litro)',
        digits=(12, 2),
        default=0.0,
        help='Monto fijo en bolivianos por cada litro. Ejemplo: 0.51 Bs/litro'
    )

    ice_alicuota_porcentual = fields.Float(
        string='Alícuota Porcentual (%)',
        digits=(12, 2),
        default=0.0,
        help='Porcentaje aplicado sobre el precio de venta. Ejemplo: 1%'
    )

    ice_aplica_alicuota = fields.Boolean(
        string='Aplica ICE',
        compute='_compute_ice_aplica_alicuota',
        store=True,
        help='Indica si el producto tiene al menos una alícuota configurada'
    )

    @api.depends('ice_alicuota_especifica', 'ice_alicuota_porcentual')
    def _compute_ice_aplica_alicuota(self):
        """Calcula si el producto tiene alícuotas ICE configuradas"""
        for product in self:
            product.ice_aplica_alicuota = (
                    product.ice_alicuota_especifica > 0 or
                    product.ice_alicuota_porcentual > 0
            )

    @api.constrains('ice_alicuota_especifica', 'ice_alicuota_porcentual')
    def _check_ice_alicuotas(self):
        """Valida que las alícuotas no sean negativas"""
        for product in self:
            if product.ice_alicuota_especifica < 0:
                raise ValidationError(
                    'La alícuota específica no puede ser negativa.'
                )
            if product.ice_alicuota_porcentual < 0:
                raise ValidationError(
                    'La alícuota porcentual no puede ser negativa.'
                )
            if product.ice_alicuota_porcentual > 100:
                raise ValidationError(
                    'La alícuota porcentual no puede ser mayor a 100%.'
                )