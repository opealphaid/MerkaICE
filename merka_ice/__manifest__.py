{
    'name': 'ICE - Alícuotas V2',
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
        'data/ice_tax_data.xml',
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/account_tax_views.xml',
    ],
    "installable": True,
    "application": False,
}
