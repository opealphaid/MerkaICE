from odoo import models, fields, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    ice_type = fields.Selection([
        ('none', 'No es ICE'),
        ('especifico', 'ICE Específico (Bs/Litro)'),
        ('porcentual', 'ICE Porcentual (%)'),
    ], string='Tipo de ICE', default='none',
        help='Define si este impuesto representa un ICE y de qué tipo')

    ice_alicuota_especifica = fields.Float(
        string='Alícuota Específica (Bs/L)',
        digits=(12, 2),
        default=0.0,
        help='Monto en bolivianos por litro. Solo aplica si el tipo es "ICE Específico"'
    )

    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, is_refund=False,
                    handle_price_include=True, include_caba_tags=False, fixed_multiplicator=1):
        """
        Sobrescribe compute_all para calcular ICE específico según litros.
        Para ICE porcentual usa el cálculo estándar de Odoo.
        """
        # Si es ICE específico, necesitamos calcular según litros
        if self.ice_type == 'especifico' and product:
            # Obtener litros del producto
            litros_por_unidad = 0
            if hasattr(product, '_get_ice_litros_por_unidad'):
                litros_por_unidad = product._get_ice_litros_por_unidad()

            litros_totales = quantity * litros_por_unidad
            monto_ice = litros_totales * self.ice_alicuota_especifica

            # Construir el resultado en el formato esperado por Odoo
            total_excluded = price_unit * quantity
            total_included = total_excluded + monto_ice

            return {
                'base_tags': self.invoice_repartition_line_ids.filtered(
                    lambda x: x.repartition_type == 'base').tag_ids.ids,
                'taxes': [{
                    'id': self.id,
                    'name': self.name,
                    'amount': monto_ice,
                    'base': total_excluded,
                    'sequence': self.sequence,
                    'account_id': self.invoice_repartition_line_ids.filtered(
                        lambda x: x.repartition_type == 'tax').account_id.id,
                    'analytic': self.analytic,
                    'price_include': self.price_include,
                    'tax_exigibility': self.tax_exigibility,
                    'group': self,
                    'tag_ids': self.invoice_repartition_line_ids.filtered(
                        lambda x: x.repartition_type == 'tax').tag_ids.ids,
                }],
                'total_excluded': total_excluded,
                'total_included': total_included if self.include_base_amount else total_excluded,
                'total_void': total_excluded,
            }

        # Para ICE porcentual o impuestos normales, usar el método estándar
        return super().compute_all(
            price_unit, currency, quantity, product, partner,
            is_refund, handle_price_include, include_caba_tags, fixed_multiplicator
        )