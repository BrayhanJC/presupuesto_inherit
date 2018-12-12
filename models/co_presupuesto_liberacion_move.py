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
									domain=[('rubros_id.rubro_tipo', '=', 'G'), 
											('mov_type', 'in', ['obl', 'cdp', 'reg', 'pago', 'lib', 'ini', 'mod', 'rec', 'adi', 'cre','cont', 'red'])])
	
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
		presupuesto_tools = self.env['presupuesto.tools']
		view_ref = self.env['ir.model.data'].get_object_reference('presupuesto_inherit', 'view_presupuesto_liberacion_form_wizard')
		view_id = view_ref[ 1 ] if view_ref else False
		move_type = self.get_mov_type(self.doc_type)
		
		result = {}
		result['partner_id'] = self.partner_id.id
		result['date'] = date.today().strftime('%d-%m-%Y')
		result['period_id'] = self.period_id.id
		result['description'] = "Liberacion de presupuesto"
		result['doc_type'] = move_type
		result['fiscal_year'] = self.fiscal_year.id
		
		presupuesto_libreacion_id = self.env['presupuesto.move'].create(result)

		gastos_ids = list(set(self.get_gastos_ids(self.gastos_ids)))

		if not gastos_ids:
			raise osv.except_osv(u'Información', "No hay nada para liberar")

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
				
			presupuesto = presupuesto_tools._get_diff_money(data) 
			if presupuesto > 0:
				result = {}
				result['rubros_id'] = data.rubros_id.id
				result['saldo_move_'] = self.saldo_sin_utilizar
				result['move_id'] = presupuesto_libreacion_id.id
				result['ammount'] = 0
				result['mov_type'] = move_type
				result['move_rel_id'] = self.id
		
				if not self.env['presupuesto.moverubros'].search([('move_id', '=', presupuesto_libreacion_id.id), ('mov_type', '=', move_type), ('rubros_id', '=', data.rubros_id.id)]): 
					self.env['presupuesto.moverubros'].create(result)	


		return {
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'presupuesto.move',
			'type': 'ir.actions.act_window',
			'view_id': view_id,
			'res_id': presupuesto_libreacion_id.id,
			'context': {'move_id': self.id, 'move_type': move_type},
			'nodestroy': True,
			'target': 'new',
		}


	@api.multi
	def button_liberar_presupuesto_liberacion_(self):
		pass


	@api.multi
	def button_liberar_presupuesto_liberacion(self):

		presupuesto_move_rubros_obj = self.env['presupuesto.moverubros']			

		for x in self.gastos_liberacion_ids:
			#el primer documento es el al cual se le va hacer la liberacion
			primer_documento = presupuesto_move_rubros_obj.search([('move_id', '=', x.move_rel_id.id)], limit=1)

			if primer_documento:
				if 	primer_documento.move_id.saldo_sin_utilizar > 0:
					saldo_primer_documento =  primer_documento.move_id.saldo_sin_utilizar - x.ammount
					primer_documento.move_id.write({'saldo_sin_utilizar': saldo_primer_documento})
					#segundo documento es el documento padre del documento al cual se le va hacer la liberacion
					#ejemplo si queremos hacer la liberacion de una obligacion entonces el segundo documento
					# es un compromiso. 
					segundo_documento = presupuesto_move_rubros_obj.search([('move_id', '=', primer_documento.move_rel_id.id)], limit=1)
					if segundo_documento:
						saldo_segundo_documento = segundo_documento.move_id.saldo_sin_utilizar + x.ammount
						segundo_documento.move_id.write({'saldo_sin_utilizar': saldo_segundo_documento})
				else:
    				
					raise Warning(_(u'No hay nada para liberar'))
			
		
		self.write({'state': 'confirm'})

		


		



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
		presupuesto_tools = self.env['presupuesto.tools']
		if gastos_ids:

			result = ()

			if len(gastos_ids) == 1:
				if presupuesto_tools._get_diff_money(gastos_ids) > 0:
					result =(gastos_ids.id,)
			else:

				for data in gastos_ids:
					if presupuesto_tools._get_diff_money(data) > 0:
						result += (data.id,)

			return result


presupuesto_liberacion_rel()

