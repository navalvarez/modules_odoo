{
    'name': 'Tipo de Cambio BOB - Bolivia',
    'version': '16.0.1.0.0',
    'summary': 'Actualiza USD, BOB y UFV desde el Banco Central de Bolivia vía api.factura.bo.',
    'author': 'Naval Alvarez',
    'category': 'Accounting/Localizations',
    'website': '',
    'depends': ['base', 'account'],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'images': [
        'static/description/icon.png',
    ],
    
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
