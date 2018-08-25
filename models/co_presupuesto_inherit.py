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
from openerp import api
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

class presupuesto_move_inherit(models.Model):
	_inherit = 'presupuesto.move'
	_order = 'date desc'



	@api.model
	def create(self, vals):

		if 'period_id' in vals:

			period = self.env['account.period'].browse(vals.get('period_id'))

			if period == 'done':

				raise Warning(_(u'El periodo que se está usando ya está cerrado'))



		return super(presupuesto_move_inherit, self).create(vals)



	@api.multi
	def write(self, vals):
	
		if 'period_id' in vals:

			period = self.env['account.period'].browse(vals.get('period_id'))

			if period == 'done':

				raise Warning(_(u'El periodo que se está usando ya está cerrado'))

		return super(presupuesto_move_inherit, self).write(vals)




	presupuesto_rel_move = fields.Many2many(comodel_name='presupuesto.move',
						relation='presupuesto_origen_destino',
						column1='origen_ids',
						column2='destino_ids',
						states={'confirm': [('readonly', True)]})

	doc_type = fields.Selection([
								('ini', 'Inicial'),
								('mod', 'Modificacón'),
								('rec', 'Recaudo'),
								('cdp', 'CDP'),
								('reg', 'Compromiso'),
								('obl', 'Obligación'),
								('pago', 'Pago'),
								('lib', 'Liberación')], 'Tipo', select=True, required=True, states={'confirm': [('readonly', True)]})
	hide_button_confirm= fields.Boolean(compute='_hide_button_confirm', default=False)	
	
	


	@api.model
	def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):

		res = super(presupuesto_move_inherit, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
		
		partner_invisible =self.env.context.get('partner_invisible')
		contract_invisible =self.env.context.get('contract_invisible')

		if view_type== 'form':
			
			doc = etree.XML(res['arch'])

			if partner_invisible:
				_logger.info('es invisible')
				for node in doc.xpath("//field[@name='partner_id']"):
					node.set('readonly', '1')
					setup_modifiers(node, res['fields']['partner_id'])

			if contract_invisible:
				_logger.info('es invisible')
				for node in doc.xpath("//field[@name='contract_id']"):
					node.set('readonly', '1')
					setup_modifiers(node, res['fields']['contract_id'])

			res['arch']= etree.tostring(doc)

		return res

	@api.one
	@api.onchange('gastos_ids')
	def hide_button_change(self):
		if self.gastos_ids:
			diff = self._get_diff_money(self.gastos_ids)
			if diff <= 0:
				self.hide_button_confirm = True
			else:
				self.hide_button_confirm = False
	

	""" 
		metodo computado que nos ayuda a cambiar el estado a la variable hide_button_confirm
		para saber si el boton lo ocultamos, cambia el estado de la variable a verdadero si 
		la diferencia es <= 0. 

	"""
	@api.one
	def _hide_button_confirm(self):
		if self.gastos_ids:
			diff = self._get_diff_money(self.gastos_ids)
			if diff <= 0:
				self.hide_button_confirm = True
			else:
				self.hide_button_confirm = False

	""" 
		metodo que nos sirve para saber si en los rubros que tiene el cdp, compromiso
		o obligacion el monto de los gastos es igual.

		recibe los ids de los rubros.
		
		retorna la diferencia entre el presupuesto y los gastos
	"""

	def _get_diff_money(self, ids):

		if ids:
			saldo_move = 0
			ammount = 0
			for data in ids:
				saldo_move += data.saldo_move
				ammount += data.ammount
			return saldo_move - ammount

	""" 
		boton que nos sirve para liberar el presupuesto es usado en la vista
		de cdp, compromiso y obligacion

	"""         


	@api.onchange('presupuesto_rel_move')
	def _onchange_rel_move_ids(self):

		if self.presupuesto_rel_move:

			rpre_moverubros = self.env['presupuesto.moverubros']
			val_rel_ids= self.presupuesto_rel_move
			lista_rubros = []
			for x in val_rel_ids:
				cdp_moverubros = rpre_moverubros.search([('move_id.id', '=', x.id)])
				for rubro in cdp_moverubros:
					if rubro.saldo_move > 0:
						lista_rubros.append((0,0,{'move_id' : self.id , 'ammount':0 , 'rubros_id' : rubro.rubros_id.id, 'mov_type' : self.doc_type, 'date' : datetime.now().strftime('%Y-%m-%d'), 'period_id' : self.period_id.id, 'move_rel_id':x.id}))
			self.gastos_ids = lista_rubros
		else:
			self.gastos_ids=None





	@api.onchange('date')
	def onchange_date(self):

		doc_type = {'reg' : 'cdp', 'obl': 'reg', 'pago': 'obl'}

		presupuesto_tools = self.env['presupuesto.tools']
		presupuesto_rel_move = []

		if self.date:
			period = self.env['account.period'].find(self.date)
			self.period_id = period.id
			self.fiscal_year = period.fiscalyear_id.id
		if not self.date and self.fiscal_year:
			period = self.env['account.period'].find(self.date)
			self.period_id = period.id
			self.date = self.fiscal_year.date_start
			self.date_start = self.fiscal_year.date_start
			self.date_stop = self.fiscal_year.date_stop


	@api.one
	def button_update(self):

		presupuesto_tools = self.env['presupuesto.tools']
		presupuesto_tools.uptdate_old_values_account_invoice()
		presupuesto_tools.uptdate_old_values_account_voucher()
		presupuesto_tools.uptdate_old_values_contact()
		presupuesto_tools.uptdate_old_values_payslip()
		presupuesto_tools.update_old_values()

presupuesto_move_inherit()
