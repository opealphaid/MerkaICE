from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Campos ICE
    ice_litros = fields.Float(
        string='Litros Totales',
        digits=(12, 3),
        compute='_compute_ice_litros',
        store=True,
        readonly=False,
        help='Litros totales (cantidad × litros por unidad del producto)'
    )

    ice_alicuota_especifica = fields.Float(
        string='Alíc. Específica (Bs/L)',
        digits=(12, 2),
        compute='_compute_ice_alicuotas',
        store=True,
        readonly=False,
        help='Alícuota específica del producto'
    )

    ice_alicuota_porcentual = fields.Float(
        string='Alíc. Porcentual (%)',
        digits=(12, 2),
        compute='_compute_ice_alicuotas',
        store=True,
        readonly=False,
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

    @api.depends('product_id', 'product_qty')
    def _compute_ice_alicuotas(self):
        """Carga las alícuotas del producto automáticamente"""
        for line in self:
            if line.product_id:
                line.ice_alicuota_especifica = line.product_id.ice_alicuota_especifica
                line.ice_alicuota_porcentual = line.product_id.ice_alicuota_porcentual
                # Calcular litros totales usando el método de conversión del producto
                litros_por_unidad = line.product_id._get_ice_litros_por_unidad()
                line.ice_litros = line.product_qty * litros_por_unidad
            else:
                line.ice_alicuota_especifica = 0.0
                line.ice_alicuota_porcentual = 0.0
                line.ice_litros = 0.0

    @api.depends('product_qty', 'product_id')
    def _compute_ice_litros(self):
        """Calcula litros totales basado en cantidad × volumen convertido a litros"""
        for line in self:
            if line.product_id and line.product_id.ice_volumen_por_unidad > 0:
                litros_por_unidad = line.product_id._get_ice_litros_por_unidad()
                line.ice_litros = line.product_qty * litros_por_unidad
            else:
                line.ice_litros = 0.0

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

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'ice_monto_total', 'discount')
    def _compute_amount(self):
        """Sobrescribe completamente el cálculo para incluir ICE en price_subtotal"""
        for line in self:
            # Calcular el precio unitario efectivo (incluyendo ICE distribuido)
            price_unit_con_ice = line.price_unit
            if line.product_qty and line.ice_monto_total:
                price_unit_con_ice = line.price_unit + (line.ice_monto_total / line.product_qty)

            # Calcular impuestos con el precio que incluye ICE
            taxes = line.taxes_id.compute_all(
                price_unit_con_ice,
                line.order_id.currency_id,
                line.product_qty,
                product=line.product_id,
                partner=line.order_id.partner_id
            )

            # Actualizar los campos con los valores que incluyen ICE
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.constrains('ice_litros')
    def _check_ice_litros(self):
        """Valida que los litros no sean negativos"""
        for line in self:
            if line.ice_litros < 0:
                raise ValidationError(
                    'La cantidad de litros no puede ser negativa.'
                )

    def _prepare_account_move_line(self, move=False):
        """Preparar datos de línea de factura incluyendo campos ICE"""
        res = super()._prepare_account_move_line(move=move)
        res.update({
            'ice_litros': self.ice_litros,
            'ice_alicuota_especifica': self.ice_alicuota_especifica,
            'ice_alicuota_porcentual': self.ice_alicuota_porcentual,
        })
        return res