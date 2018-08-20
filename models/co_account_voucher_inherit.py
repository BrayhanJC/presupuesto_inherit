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
_logger = logging.getLogger(__name__)

class presupuesto_account_voucher_inherit(models.Model):
	_inherit = 'account.voucher'
	_description = 'Voucher'

	#obl_move_rel = fields.Many2many('presupuesto.move', 'account_voucher_presupuesto_rel', 'account_voucher_id', 'presupuesto_move_id')

	obl_move_rel = fields.Many2many(comodel_name='presupuesto.move', string="OBL",
						relation='presupuesto_origen_destino_voucher',
						column1='origen_ids',
						column2='destino_ids', 
						domain=[('doc_type', '=' , 'obl')])
	def action_move_line_create(self, cr, uid, ids, context=None):
		'''
		Generar movimientos automáticos en presupuesto al validar recibos de caja o comprobantes de egreso
		'''
		if context is None:
			context = {}
		presupuesto_move_pool = self.pool.get('presupuesto.move')
		period_pool = self.pool.get('account.period')
		presupuesto_moverubros_obj = self.pool.get('presupuesto.moverubros')

		for voucher in self.browse(cr, uid, ids, context=context):

			date = voucher.date
			partner_id = voucher.partner_id.id
			reference = voucher.reference
			documento = voucher.id
			rubro_id = False
			obl_id = []
			rec = voucher.rec.id

			if (voucher.type == 'sale' or voucher.type == 'receipt'):
				ingresos_ids = []
				rubros_sum = 0.0

				if voucher.rec_aut and not rec:
					if voucher.rubro_pres:
						rubro_id = voucher.rubro_pres.rubros_id.id
					else:
						raise osv.except_osv(_('¡Advertencia!'),_("Por favor ingrese un concepto presupuestal o desmarque la casilla Presupuesto Automático"))

					presupuesto_move = {
						'doc_type': 'rec',
						'date': date,
						'partner_id': partner_id,
						'description': reference,
						'voucher_id':documento,
						'state': 'confirm',
					}

					period_pool = self.pool.get('account.period')
					ctx = dict(context or {}, account_period_prefer_normal=True)
					search_periods = period_pool.find(cr, uid, voucher.date, context=ctx)
					period = search_periods[0]
					periodyear = period_pool.browse(cr, uid, period, context=context)
					year = periodyear.fiscalyear_id.id
					presupuesto_move['period_id'] = period

					presupuesto_move['fiscal_year'] = year

					for line in voucher.line_cr_ids:
						amt = line.move_line_id.invoice.amount_untaxed

						if rubro_id:

							rec_line = (0,0, {
							'rubros_id' : rubro_id,
							'mov_type': 'rec',
							'period_id': period,
							'date': date,
							'ammount': amt or 0.0,
							})
							ingresos_ids.append(rec_line)
							rubros_sum += rec_line[2]['ammount']

					presupuesto_move.update({'ingresos_ids': ingresos_ids})
					rec_id = presupuesto_move_pool.create(cr, uid, presupuesto_move, context=context)
					self.write(cr, uid, [voucher.id], {'rec':rec_id}, context=context)

			if (voucher.type == 'purchase' or voucher.type == 'payment'):


				gastos_ids = []
				rubros_sum = 0.0
				narration = voucher.narration
				rubros_ids = []
				pago = voucher.pago.id
				
				if voucher.rec_aut and not pago:
					if voucher.obl_move_rel:
						for x in voucher.obl_move_rel:
							obl_id.append(x.id)
					else:
						raise osv.except_osv(_('¡Advertencia!'),_("Por favor seleccione una obligación presupuestal o desmarque la casilla Presupuesto Automático"))

					move_arreglos=[]

					for x in voucher.obl_move_rel:
						move_arreglos.append(x.id)
					presupuesto_move = {
						'doc_type': 'pago',
						'date': date,
						'partner_id': partner_id,
						'description': narration,
						'voucher_id':documento,
						'presupuesto_rel_move': [(6, 0,[move_arreglos])],
						'state': 'confirm',
					}

					period_pool = self.pool.get('account.period')
					ctx = dict(context or {}, account_period_prefer_normal=True)
					search_periods = period_pool.find(cr, uid, voucher.date, context=ctx)
					period = search_periods[0]
					periodyear = period_pool.browse(cr, uid, period, context=context)
					year = periodyear.fiscalyear_id.id
					presupuesto_move['period_id'] = period

					presupuesto_move['fiscal_year'] = year

					
					for x in voucher.obl_move_rel:
						
						for line in x.gastos_ids:
							if line: rubros_ids.append(line)


					pago_id = presupuesto_move_pool.create(cr, uid, presupuesto_move, context=context)

					for rubros in rubros_ids:
						presupuesto_move_line = {
							'move_id': pago_id,
							'rubros_id': rubros.rubros_id.id,
							'mov_type': 'pago',
							'period_id': period,
							'date': date,
							'ammount': rubros.ammount,
							'move_rel_id': rubros.move_id.id

						}
						presupuesto_moverubros_obj.create(cr, uid, presupuesto_move_line, context=context)
						gastos_ids.append(rubros.id)

					presupuesto_move.update({'gastos_ids': gastos_ids})
					self.write(cr, uid, [voucher.id], {'pago':pago_id}, context=context)

		return super(presupuesto_account_voucher_inherit, self).action_move_line_create(cr, uid, ids, context=context)

	def create_pago(self, cr, uid, voucher, rubros_ids, context={}):

		if not voucher.narration:
			raise Warning(_('El campo Notas Internas debe estar diligenciado'))

		presupuesto_move_obj = self.pool.get('presupuesto.move')
		presupuesto_moverubros_obj = self.pool.get('presupuesto.moverubros')
		obl_id = []

		if voucher.obl_move_rel:
			for x in voucher.obl_move_rel:
				obl_id.append(x.id)

		pago = voucher.pago.id

		move_arreglos=[]

		for x in voucher.obl_move_rel:
			move_arreglos.append(x.id)


		presupuesto_move = {
			'date': voucher.date,
			'doc_type': "pago",
			'partner_id': self.pool.get('res.partner')._find_accounting_partner(voucher.partner_id).id,
			'presupuesto_rel_move': [(6, 0,[move_arreglos])],
			'voucher_id': voucher.id,
			'description': voucher.narration,
			'period_id':voucher.period_id.id,
			'fiscal_year':voucher.period_id.fiscalyear_id.id,
		}
		if not pago:
			presupuesto_move_id = presupuesto_move_obj.create(cr, uid, presupuesto_move, context=context)

		gastos_ids = []
		for rubros in rubros_ids:
			presupuesto_move_line = {
				'move_id': presupuesto_move_id,
				'rubros_id': rubros.rubros_id.id,
				'mov_type': 'pago',
				'period_id': voucher.period_id.id,
				'date': voucher.date,
				'ammount': 0 if len(voucher.obl_move_rel) > 1 else rubros.ammount,
				'move_rel_id':rubros.move_id.id
			}

			presupuesto_moverubros_obj.create(cr, uid, presupuesto_move_line, context=context)
			gastos_ids.append(rubros.id)

		voucher_pago = {
			'pago': presupuesto_move_id,
		}
		self.pool.get('account.voucher').write(cr, uid, [voucher.id], voucher_pago, context=context)

		return presupuesto_move_id


	def generate_pago(self, cr, uid, ids, context={}):

		voucher = self.browse(cr, uid, ids, context=context)[0]

		rubros_ids = []

		if voucher.obl_move_rel == False:
			raise osv.except_osv(_('¡Advertencia!'),_("Por favor seleccione una obligación presupuestal"))
		else:

			for x in voucher.obl_move_rel:
				for line in x.gastos_ids:
					if line: rubros_ids.append(line)

			pago = self.create_pago(cr, uid, voucher, rubros_ids, context=context)
			data_obj = self.pool.get('ir.model.data')
			result = data_obj._get_id(cr, uid, 'presupuesto', 'view_presupuesto_pago_move_form')
			view_id = data_obj.browse(cr, uid, result).res_id

			return {
				'domain': "[('id','=', " + str(pago) + ")]",
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'presupuesto.move',
				'context': context,
				'res_id': pago,
				'view_id': [view_id],
				'type': 'ir.actions.act_window',
				'nodestroy': True,
				'target': 'new',
			}
	
presupuesto_account_voucher_inherit()