from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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

    @api.depends('product_id', 'move_id.move_type', 'quantity')
    def _compute_ice_alicuotas(self):
        """Carga las alícuotas del producto automáticamente"""
        for line in self:
            # Solo para facturas de proveedor
            if line.product_id and line.move_id.move_type in ('in_invoice', 'in_refund'):
                line.ice_alicuota_especifica = line.product_id.ice_alicuota_especifica
                line.ice_alicuota_porcentual = line.product_id.ice_alicuota_porcentual
                # Calcular litros totales usando el método de conversión del producto
                litros_por_unidad = line.product_id._get_ice_litros_por_unidad()
                line.ice_litros = line.quantity * litros_por_unidad
            else:
                line.ice_alicuota_especifica = 0.0
                line.ice_alicuota_porcentual = 0.0
                line.ice_litros = 0.0

    @api.depends('quantity', 'product_id', 'move_id.move_type')
    def _compute_ice_litros(self):
        """Calcula litros totales basado en cantidad × volumen convertido a litros"""
        for line in self:
            if line.move_id.move_type in ('in_invoice', 'in_refund'):
                if line.product_id and line.product_id.ice_volumen_por_unidad > 0:
                    litros_por_unidad = line.product_id._get_ice_litros_por_unidad()
                    line.ice_litros = line.quantity * litros_por_unidad
                else:
                    line.ice_litros = 0.0
            else:
                line.ice_litros = 0.0

    @api.depends('ice_litros', 'ice_alicuota_especifica',
                 'price_unit', 'quantity', 'ice_alicuota_porcentual', 'move_id.move_type')
    def _compute_ice_montos(self):
        """Calcula los montos de ICE (específico, porcentual y total)"""
        for line in self:
            # Solo calcular para facturas de proveedor
            if line.move_id.move_type not in ('in_invoice', 'in_refund'):
                line.ice_monto_especifico = 0.0
                line.ice_monto_porcentual = 0.0
                line.ice_monto_total = 0.0
                continue

            # ICE Específico: litros × alícuota específica
            ice_especifico = line.ice_litros * line.ice_alicuota_especifica

            # ICE Porcentual: (precio unitario × cantidad) × (porcentaje / 100)
            subtotal = line.price_unit * line.quantity
            ice_porcentual = subtotal * (line.ice_alicuota_porcentual / 100)

            # Asignar valores
            line.ice_monto_especifico = ice_especifico
            line.ice_monto_porcentual = ice_porcentual
            line.ice_monto_total = ice_especifico + ice_porcentual

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id', 'ice_monto_total')
    def _compute_totals(self):
        """Sobrescribe el cálculo de totals para incluir ICE en el subtotal"""
        super()._compute_totals()

        for line in self:
            # Solo para facturas de proveedor
            if line.move_id.move_type in ('in_invoice', 'in_refund') and line.ice_monto_total > 0:
                # Sumar el ICE al price_subtotal
                line.price_subtotal += line.ice_monto_total
                line.price_total += line.ice_monto_total

    @api.constrains('ice_litros')
    def _check_ice_litros_invoice(self):
        """Valida que los litros no sean negativos"""
        for line in self:
            if line.ice_litros < 0:
                raise ValidationError(
                    'La cantidad de litros no puede ser negativa.'
                )