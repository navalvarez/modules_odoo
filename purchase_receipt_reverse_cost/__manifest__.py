# -*- coding: utf-8 -*-
{
    'name': 'Purchase Return at Cost',
    'version': '16.0.1.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Reverse purchase receipts using the original valuation cost.',
    'description': """
Purchase Return at Original Cost
================================

This module allows you to reverse a validated purchase receipt using the
original stock valuation cost at which the products were received.

Unlike the standard Odoo reversal, which uses the current Average Cost (AVCO)
at the time of the return, this module ensures the stock valuation layer (SVL)
is created with the historical unit cost from the original receipt.

This is particularly useful in AVCO configurations to maintain accurate
inventory valuation and avoid discrepancies in the accounting entries.
    """,
    'author': 'Naval Alvarez',  # O tu nombre de empresa
    'website': 'https://www.tu-web.com',  # Opcional
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
    'images': [
        'static/description/main_screenshot.png',
        'static/description/img/screenshot_button.png',
        'static/description/img/screenshot_wizard.png',
        'static/description/img/screenshot_return.png',
        'static/description/img/screenshot_slv_in.png',
        'static/description/img/screenshot_slv_out.png',
    ],
    'installable': True,
    'application': False,
    # 'price': 0.0,  # Dejar vacío o 0 para gratuito
    # 'currency': 'EUR',
}