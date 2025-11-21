from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Campos para volumen (necesarios para ICE específico)
    ice_volumen_por_unidad = fields.Float(
        string='Volumen por Unidad',
        digits=(12, 3),
        default=0.0,
        help='Volumen que contiene una unidad del producto'
    )

    ice_uom_volumen = fields.Selection([
        ('l', 'Litros (L)'),
        ('ml', 'Mililitros (mL)'),
        ('cl', 'Centilitros (cL)'),
        ('dl', 'Decilitros (dL)'),
    ], string='Unidad de Volumen', default='l',
        help='Unidad en la que está expresado el volumen')

    # Campo para mostrar si tiene ICE configurado
    ice_aplica = fields.Boolean(
        string='Aplica ICE',
        compute='_compute_ice_aplica',
        store=True,
        help='Indica si el producto tiene impuestos ICE configurados'
    )

    @api.depends('supplier_taxes_id')
    def _compute_ice_aplica(self):
        """Verifica si el producto tiene impuestos de tipo ICE"""
        for product in self:
            ice_taxes = product.supplier_taxes_id.filtered(
                lambda t: t.ice_type in ('especifico', 'porcentual')
            )
            product.ice_aplica = bool(ice_taxes)

    @api.constrains('ice_volumen_por_unidad')
    def _check_ice_volumen(self):
        """Valida que el volumen no sea negativo"""
        for product in self:
            if product.ice_volumen_por_unidad < 0:
                raise ValidationError(
                    'El volumen por unidad no puede ser negativo.'
                )

    def _get_ice_litros_por_unidad(self):
        """Convierte el volumen a litros según la unidad de medida"""
        self.ensure_one()
        conversion_factors = {
            'l': 1.0,      # Litros
            'ml': 0.001,   # Mililitros a Litros
            'cl': 0.01,    # Centilitros a Litros
            'dl': 0.1,     # Decilitros a Litros
        }
        factor = conversion_factors.get(self.ice_uom_volumen, 1.0)
        return self.ice_volumen_por_unidad * factor


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _get_ice_litros_por_unidad(self):
        """Convierte el volumen a litros según la unidad de medida"""
        self.ensure_one()
        conversion_factors = {
            'l': 1.0,      # Litros
            'ml': 0.001,   # Mililitros a Litros
            'cl': 0.01,    # Centilitros a Litros
            'dl': 0.1,     # Decilitros a Litros
        }
        factor = conversion_factors.get(self.ice_uom_volumen, 1.0)
        return self.ice_volumen_por_unidad * factor