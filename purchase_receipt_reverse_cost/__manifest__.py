# -*- coding: utf-8 -*-

{
    'name': 'Purchase Receipt Reverse at Original Cost',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Reverse purchase receipts using the original valuation cost',
    'description': """
Purchase Receipt Reverse at Original Cost
==========================================

Allows reversing a validated purchase receipt using the original
stock valuation cost instead of the current AVCO.

The native Odoo return wizard is reused.
""",
    'author': 'Naval Alvarez',
    'license': 'LGPL-3',
    'depends': [
        'stock',
        'stock_account',
        'purchase_stock',
    ],
    'data': [
        'views/stock_picking_views.xml',
        'views/stock_return_picking_views.xml',
    ],
    'installable': True,
    'application': False,
}