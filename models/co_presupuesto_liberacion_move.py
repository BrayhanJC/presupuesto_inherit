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
from openerp import models, fields
import re
import codecs
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import math
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import time
from datetime import date, datetime, timedelta
from openerp.osv.orm import setup_modifiers
from lxml import etree
_logger = logging.getLogger(__name__)



class presupuesto_liberacion_rel(models.Model):

	_inherit = 'presupuesto.move'


	id = fields.Integer('id')
	llenar_campo_gastaos_liberaciones = fields.Boolean(compute='_compute_liberaciones', string = "Liberaciones")


	gastos_ids = fields.One2many('presupuesto.moverubros', 'move_id', string=u'Rubros', states={'confirm': [('readonly', True)]},
									domain=[('rubros_id.rubro_tipo', '=', 'G'), ('mov_type', 'in', ['obl', 'cdp', 'reg', 'pago', 'lib', 'ini', 'mod', 'rec'])])
		

	gastos_liberacion_ids = fields.One2many('presupuesto.moverubros', 'move_id', string=u'Rubros', states={'confirm': [('readonly', True)]},
									domain=[('rubros_id.rubro_tipo', '=', 'G'), ('mov_type', 'in', ['lobl', 'lcdp', 'lreg'])])
		


	"""
		metodo que nos permite llenar el campo gastos_liberaciones_ids de acuerdo
		al tipo de movimiento donde este sea llamado
	"""

	@api.one
	def _compute_liberaciones(self):
		self.gastos_liberacion_ids = self.env['presupuesto.moverubros'].search([('move_id', '=', self.id), ('mov_type', '=', self.get_mov_type(self.env.context.get('move_type')))])
		self.llenar_campo_gastaos_liberaciones = False




	""" 
	boton que nos permite llamar a la ventana para haer las liberaciones
	no permite saber si no hay nada para liberar, y tamben nos permite
	cargar los datos a mostrar de manera correcta. 
	"""	

	@api.multi
	def button_liberar_presupuesto(self):
		
		presupuesto_move_tool = self.env['presupuesto.tools']
		presupuesto_move_tool.uptdate_old_values_account_invoice()
		presupuesto_move_tool.uptdate_old_values_account_voucher()
		presupuesto_move_tool.uptdate_old_values_contact()
		presupuesto_move_tool.uptdate_old_values_payslip()
		presupuesto_move_tool.update_old_values()



	@api.multi
	def button_liberar_presupuesto_liberacion(self):
		
		_logger.info(self.gastos_liberacion_ids)

		for data in self.gastos_liberacion_ids:

			if data.ammount > 0:

				_logger.info(data)




		pass




	"""
	este metodo de acuerdo al doc_type nos permite ssaber de donde nos llaman
	y saber que si es una obligacion el mov_type seria una lobl y asi para las
	demas se usa para filtrar.
	"""	
	def get_mov_type(self, doc_type):
		
		mov_type = None

		if doc_type == 'obl':
			return 'lobl'
		elif doc_type == 'reg':
			return 'lreg'
		elif doc_type == 'cdp':
			return 'lcdp'



	"""
	metodo que es llamado en el boton liberar presupuesto con el cual sabemos por cada rubro si hay dinero para
	liberar o por el contrario no tenemos nada.
	"""		

	def get_gastos_ids(self, gastos_ids):
		
		if gastos_ids:

			result = ()

			if len(gastos_ids) == 1:
				if self._get_diff_money(gastos_ids) > 0:
					result =(gastos_ids.id,)
			else:

				for data in gastos_ids:
					if self._get_diff_money(data) > 0:
						result += (data.id,)

			return result


presupuesto_liberacion_rel()

