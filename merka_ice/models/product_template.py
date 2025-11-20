from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos para alícuotas ICE
    ice_volumen_por_unidad = fields.Float(
        string='Volumen por Unidad',
        digits=(12, 3),
        default=0.0,
        help='Volumen que contiene una unidad del producto (en la UdM configurada)'
    )

    ice_uom_volumen = fields.Selection([
        ('l', 'Litros (L)'),
        ('ml', 'Mililitros (mL)'),
        ('cl', 'Centilitros (cL)'),
        ('dl', 'Decilitros (dL)'),
    ], string='Unidad de Volumen', default='l',
        help='Unidad en la que está expresado el volumen')

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

    @api.constrains('ice_volumen_por_unidad', 'ice_alicuota_especifica', 'ice_alicuota_porcentual')
    def _check_ice_alicuotas(self):
        """Valida que las alícuotas no sean negativas"""
        for product in self:
            if product.ice_volumen_por_unidad < 0:
                raise ValidationError(
                    'El volumen por unidad no puede ser negativo.'
                )
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

    def _get_ice_litros_por_unidad(self):
        """Convierte el volumen a litros según la unidad de medida"""
        self.ensure_one()
        conversion_factors = {
            'l': 1.0,  # Litros
            'ml': 0.001,  # Mililitros a Litros
            'cl': 0.01,  # Centilitros a Litros
            'dl': 0.1,  # Decilitros a Litros
        }
        factor = conversion_factors.get(self.ice_uom_volumen, 1.0)
        return self.ice_volumen_por_unidad * factor


# IMPORTANTE: Esta clase es necesaria para que product.product también tenga el método
class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_ice_litros_por_unidad(self):
        """Convierte el volumen a litros según la unidad de medida"""
        self.ensure_one()
        conversion_factors = {
            'l': 1.0,  # Litros
            'ml': 0.001,  # Mililitros a Litros
            'cl': 0.01,  # Centilitros a Litros
            'dl': 0.1,  # Decilitros a Litros
        }
        factor = conversion_factors.get(self.ice_uom_volumen, 1.0)
        return self.ice_volumen_por_unidad * factor