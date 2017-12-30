# -*- coding: utf-8 -*-
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
import time
from datetime import date, datetime, timedelta
import logging
import difflib
from openerp import models, fields, api, _
from openerp.osv import fields, osv
import re
import codecs
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import math
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import time
from datetime import date, datetime, timedelta
_logger = logging.getLogger(__name__)

class presupuesto_move_compromiso_inherit(osv.osv):
	_inherit = 'presupuesto.move'
	_order = 'date desc'

	_columns = {
		'presupuesto_rel_move': fields.many2many('presupuesto.move', 
												'presupuesto_cdp_compromiso',
												'cdp_ids', 'compromiso_ids', 
												'CDP', required=False, ondelete='restrict'),
		}

	@api.onchange('presupuesto_rel_move')
	def _onchange_cdp_ids(self):
		
		val_rel_ids= self.presupuesto_rel_move
		lista_rubros = []
		for x in val_rel_ids:
			rpre_moverubros = self.env['presupuesto.moverubros']
			cdp_moverubros = rpre_moverubros.search([('move_id.id', '=', x.id)])
			
			for rubro in cdp_moverubros:
				lista_rubros.append((0,0,{'move_id' : self.id , 'rubros_id' : rubro.rubros_id.id, 'mov_type' : self.doc_type, 'date' : datetime.now().strftime('%Y-%m-%d'), 'period_id' : self.period_id.id}))
		#cargando gastos
		self.gastos_ids = lista_rubros


presupuesto_move_compromiso_inherit()