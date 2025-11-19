{
    'name': 'ICE - Alícuotas',
    'version': '18.0.1.0.0',
    'author': 'Alpha Systems S.R.L',
    'website': 'https://www.alphasystems.com.bo',
    "depends": [
        'base',
        'product',
        'purchase',
        'account',
    ],
    "data": [
        "security/ir.model.access.csv",
        'views/product_template_views.xml',
        'views/purchase_order_views.xml',
        'views/account_move_views.xml',
        'report/purchase_order_report.xml',
    ],
    "installable": True,
    "application": False,
}
