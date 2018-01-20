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

class presupuesto_account_invoice_inherit(models.Model):
	_inherit = 'account.invoice'
	_description = 'Account'

	rp_move_rel = fields.One2many('presupuesto.move', 'rp_move_rel_id', domain=[('doc_type', '=' , 'reg')], states={'confirm': [('readonly', True)]})

	def create_obl(self, cr, uid, invoice, rubros_ids, context={}):

		presupuesto_move_obj = self.pool.get('presupuesto.move')
		presupuesto_moverubros_obj = self.pool.get('presupuesto.moverubros')

		move_arreglos=[]
		for x in invoice.rp_move_rel:
			move_arreglos.append(x.id)

		presupuesto_move = {
			'date': invoice.date_invoice,
			'doc_type': "obl",
			'partner_id': self.pool.get('res.partner')._find_accounting_partner(invoice.partner_id).id,
			'move_rel': invoice.rp.id,
			'presupuesto_rel_move': [(6, 0,[move_arreglos])],
			'invoice_id': invoice.id,
			'description': invoice.comment,
		}

		period_pool = self.pool.get('account.period')
		ctx = dict(context or {}, account_period_prefer_normal=True)
		search_periods = period_pool.find(cr, uid, invoice.date_invoice, context=ctx)
		period = search_periods[0]
		presupuesto_move['period_id'] = period

		presupuesto_move['fiscal_year'] = invoice.rp.fiscal_year.id

		presupuesto_move_id = presupuesto_move_obj.create(cr, uid, presupuesto_move, context=context)

		gastos_ids = []
		for rubros in rubros_ids:
			presupuesto_move_line = {
				'move_id': presupuesto_move_id,
				'rubros_id': rubros.rubros_id.id,
				'period_id': period,
				'date': invoice.date_invoice,
				'mov_type': 'obl',
				'saldo_move': 0,
				'ammount': invoice.amount_untaxed,
			}
			presupuesto_moverubros_obj.create(cr, uid, presupuesto_move_line, context=context)
			gastos_ids.append(rubros.id)

		invoice_reg = {
			'obl': presupuesto_move_id,
		}
		self.pool.get('account.invoice').write(cr, uid, [invoice.id], invoice_reg, context=context)

		return presupuesto_move_id



	def generate_obl(self, cr, uid, ids, context={}):

		invoice = self.browse(cr, uid, ids, context=context)[0]

		rubros_ids = []
		# Add only active lines
		for x in invoice.rp_move_rel:
			for line in x.gastos_ids:
				if line: rubros_ids.append(line)

		obl = self.create_obl(cr, uid, invoice, rubros_ids, context=context)
		data_obj = self.pool.get('ir.model.data')
		result = data_obj._get_id(cr, uid, 'presupuesto', 'view_presupuesto_obligacion_move_form')
		view_id = data_obj.browse(cr, uid, result).res_id

		return {
			'domain': "[('id','=', " + str(obl) + ")]",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'presupuesto.move',
			'context': context,
			'res_id': obl,
			'view_id': [view_id],
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}

presupuesto_account_invoice_inherit()