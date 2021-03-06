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
		_logger.info(vals)
		if 'period_id' in vals:

			period = self.env['account.period'].browse(vals.get('period_id'))

			if period.state == 'done':

				raise Warning(_(u'El periodo que se está usando ya está cerrado'))


		if not vals.get('name'):
				
			if vals.get('doc_type')=='lcdp':
				vals['name'] = self.env['ir.sequence'].get('lcdp.sequence')
			elif vals.get('doc_type')=='lreg':
				vals['name'] = self.env['ir.sequence'].get('lcompromiso.sequence')
			elif vals.get('doc_type')=='lobl':
				vals['name'] = self.env['ir.sequence'].get('lobligacion.sequence')
			elif vals.get('doc_type')=='rec':
				vals['name'] = self.env['ir.sequence'].get('recaudo.sequence')
			elif vals.get('doc_type')=='cdp':
				vals['name'] = self.env['ir.sequence'].get('cdp.sequence')
			elif vals.get('doc_type')=='reg':
				vals['name'] = self.env['ir.sequence'].get('compromiso.sequence')
			elif vals.get('doc_type')=='obl':
				vals['name'] = self.env['ir.sequence'].get('obligacion.sequence')
			elif vals.get('doc_type')=='pago':
				vals['name'] = self.env['ir.sequence'].get('pago.sequence')
			elif vals.get('doc_type')=='ini':
				vals['name'] = self.env['ir.sequence'].get('inicial.sequence')
			elif vals.get('doc_type')=='mod':
				vals['name'] = self.env['ir.sequence'].get('modificacion.sequence')
			else :
				vals['name'] = "/"			

		
		return super(presupuesto_move_inherit, self).create(vals)



	@api.multi
	def write(self, vals):
	
		if 'period_id' in vals:

			period = self.env['account.period'].browse(vals.get('period_id'))

			if period.state == 'done':

				raise Warning(_(u'El periodo que se está usando ya está cerrado'))

		return super(presupuesto_move_inherit, self).write(vals)

	@api.multi
	def button_confirm(self):
		res = self.write({'state': 'confirm'})
		self._saldo_sin_utilizar(self.presupuesto_rel_move)
		self._saldo_sin_utilizar(self)
		return res

	@api.multi
	def button_cancel(self):
		res = self.write({'state': 'draft'}) 
		self._saldo_sin_utilizar(self.presupuesto_rel_move)
		return res


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
								('lcdp', 'Liberación CDP'),
								('lreg', 'Liberación Compromiso'),
								('lobl', 'Liberación Obligación')], 'Tipo', select=True, required=True, states={'confirm': [('readonly', True)]})
	

	hide_button_confirm= fields.Boolean(compute='_hide_button_confirm', default=False)	
	

	state = fields.Selection([
								('draft', 'Draft'),
								('confirm', 'Confirmed'),
								('close', 'Cerrado')
								], 'Status', select=True, default = 'draft')


	
	saldo_sin_utilizar= fields.Float('Saldo sin utilizar', default=0.0, store=True, readonly=True)



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
		if self.saldo_sin_utilizar <= 0:
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
			
		if self.saldo_sin_utilizar <= 0:
			self.hide_button_confirm = True
		else:
			self.hide_button_confirm = False




  
	@api.onchange('presupuesto_rel_move')
	def _onchange_rel_move_ids(self):

		if self.presupuesto_rel_move:

			rpre_moverubros = self.env['presupuesto.moverubros']
			val_rel_ids= self.presupuesto_rel_move
			lista_rubros = []
			for x in val_rel_ids:
				cdp_moverubros = rpre_moverubros.search([('move_id.id', '=', x.id)])

				sql = """
					SELECT saldo_move 
					FROM presupuesto_moverubros
					WHERE move_id = %(id)s
				"""%{'id': x.id}
				self.env.cr.execute(sql)
				saldo_move =  self.env.cr.fetchall()


				for rubro in cdp_moverubros:
					if saldo_move > 0:
						lista_rubros.append((0,0,{'move_id' : self.id , 'ammount':0 , 'rubros_id' : rubro.rubros_id.id, 'mov_type' : self.doc_type, 'date' : datetime.now().strftime('%Y-%m-%d'), 'period_id' : self.period_id.id, 'move_rel_id':x.id}))
			self.gastos_ids = lista_rubros
		else:
			self.gastos_ids=None





	@api.onchange('date', 'period_id', 'fiscal_year')
	def onchange_date(self):
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



	def _saldo_sin_utilizar(self, presupuesto_rel_move):

		presupuesto_tools = self.env['presupuesto.tools']

		if presupuesto_rel_move:

			for x in presupuesto_rel_move:
				
				presupuesto_tools.get_saldo_obligaciones(x)




	@api.model
	def actualizar_estado_documento(self):

		_logger.info("inicie")		
		presupuesto_tools = self.env['presupuesto.tools']


		sql = """ SELECT id as id from presupuesto_move"""
		self.env.cr.execute(sql)
		sql_result =  self.env.cr.fetchall()


		if sql_result:
			
			for x in sql_result:

				sql = """ 
					UPDATE presupuesto_move SET saldo_sin_utilizar = 
					CASE WHEN (select state from presupuesto_move pm2, presupuesto_moverubros pmr2 where pm2.id = pmr2.move_id AND pmr2.move_rel_id = %(id)s) = 'confirm'
					THEN
					(select pm.amount_total - CASE WHEN (select sum(pmr.ammount) from presupuesto_moverubros pmr where move_rel_id = %(id)s) > 0 
					THEN (select sum(pmr.ammount) from presupuesto_moverubros pmr where move_rel_id = %(id)s) ELSE 0 END
					from presupuesto_move pm
					where pm.id = %(id)s and state in ('confirm'))
					ELSE amount_total END
					where id = %(id)s
					and doc_type not in ('lcdp', 'lrp', 'lobl') 
				"""% {
					'id': list(x)[0],
				}

				self.env.cr.execute( sql )
				
	
			sql = """ 
				update presupuesto_move set state = 'close'
				where saldo_sin_utilizar <= 0
				and doc_type in ('cdp', 'rp', 'obl')
				and state = 'confirm'
			"""

			self.env.cr.execute( sql )
			_logger.info("Finalice")





presupuesto_move_inherit()

