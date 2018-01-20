# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#    
#    Autor: Brayhan Andres Jaramillo Castaño
#           Juan Camilo Zuluaga Serna
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Presupuesto_inherit',
    'version': '8.0',
    'category': 'Application for the public sector',
    'description': """
    Create a module for managing the budget in public entities
    """,
    'author': 'Brayhan Jaramillo / Juan Zuluaga',
    'website': 'http://www.openerp.com/',
    'license': 'AGPL-3',
    'depends': [
        'presupuesto',
    ],
    'data': [
        'views/co_presupuesto_view_inherit.xml',
        'views/co_account_invoice_inherit_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'images': [],
    'css': [],
}
