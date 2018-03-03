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
									domain=[('rubros_id.rubro_tipo', '=', 'G'), ('mov_type', 'not in', ['lobl', 'lcdp', 'lreg'])])
		

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
		
		view_ref = self.env['ir.model.data'].get_object_reference('presupuesto_inherit', 'view_presupuesto_liberacion_form')
		view_id = view_ref[ 1 ] if view_ref else False


		gastos_ids = list(set(self.get_gastos_ids(self.gastos_ids)))

		if not gastos_ids:
			raise osv.except_osv(u'Información', "No hay nada para liberar")


		move_type = self.get_mov_type(self.doc_type)


		sql = """ 
			delete from presupuesto_moverubros
			where move_id = %(mov_id)s
			and ammount = 0
			and mov_type = '%(mov_type)s';
		"""% {
			'mov_id': self.id,
			'mov_type': move_type,
		}

		self.env.cr.execute( sql )
		
		for data in self.gastos_ids:	
			result = {}
			result['rubros_id'] = data.rubros_id.id
			result['saldo_move_'] = self._get_diff_money(data)
			result['move_id'] = self.id
			result['ammount'] = 0
			result['mov_type'] = move_type
			result['move_rel_id'] = data.move_rel_id.id
	
			if not self.env['presupuesto.moverubros'].search([('move_id', '=', self.id), ('mov_type', '=', move_type), ('rubros_id', '=', data.rubros_id.id)]): 
				self.env['presupuesto.moverubros'].create(result)	


		return {
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'presupuesto.move',
			'type': 'ir.actions.act_window',
			'view_id': view_id,
			'res_id': self.id,
			'context': {'move_id': self.id, 'move_type': move_type},
			'nodestroy': True,
			'target': 'new',
		}




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


class presupuesto_liberacion_move_rubro(models.Model):


	_inherit = 'presupuesto.moverubros'

	saldo_move_ = fields.Float(string='Saldo')	




	@api.one
	@api.constrains('ammount')
	def _check_saldo(self):

		saldo_move = self._saldo_move()[ 0 ] if self.mov_type not in ['lobl', 'lreg', 'lcdp'] else self.saldo_move_

		if self.mov_type == 'ini' or self.mov_type == 'rec' or self.mov_type == 'adi' or self.mov_type == 'cre':
			return True
		elif self.ammount > saldo_move:
			raise Warning(_('El valor del movimiento no puede ser superior al saldo. asasaskaj'))
		return True





	@api.one
	@api.constrains('mov_type')
	def _check_mov_type(self):
		record = self
		if record.move_id.doc_type == 'ini':
			if not (record.mov_type == 'ini'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'mod':
			if not (record.mov_type == 'adi' or record.mov_type =='red' or record.mov_type =='cre' or record.mov_type =='cont'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'rec':
			if not (record.mov_type == 'rec'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'cdp':
			if not (record.mov_type == 'cdp') and (record.mov_type <> 'lcdp'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'reg':
			if not (record.mov_type == 'reg') and (record.mov_type <> 'lreg'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'obl':
			if not (record.mov_type == 'obl') and (record.mov_type <> 'lobl'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'pago':
			if not (record.mov_type == 'pago'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		




presupuesto_liberacion_move_rubro()