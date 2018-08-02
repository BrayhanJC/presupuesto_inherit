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


class hr_contract_inherit(models.Model):
	_inherit = 'hr.contract'
	_description = 'Contract'

	cdp_move_rel = fields.One2many('presupuesto.move', 'rp_move_rel_id', domain=[('doc_type', '=' , 'cdp')], states={'confirm': [('readonly', True)]})

	def create_reg(self, cr, uid, contract, rubros_ids, context={}):

		presupuesto_move_obj = self.pool.get('presupuesto.move')
		presupuesto_moverubros_obj = self.pool.get('presupuesto.moverubros')

		move_arreglos=[]
		for x in invoice.cdp_move_rel:
			move_arreglos.append(x.id)

		presupuesto_move = {
			'date': contract.date_start,
			'doc_type': "reg",
			'partner_id': self.pool.get('res.partner')._find_accounting_partner(contract.employee_id.address_home_id).id,
			#'move_rel': contract.cdp.id,
			'presupuesto_rel_move': [(6, 0,[move_arreglos])],
			'contract_id': contract.id,
			'description': contract.name,
		}

		period_pool = self.pool.get('account.period')
		ctx = dict(context or {}, account_period_prefer_normal=True)
		search_periods = period_pool.find(cr, uid, contract.date_start, context=ctx)
		
		period = search_periods[0]
		presupuesto_move['period_id'] = period

		fiscal_year_id = period_pool.browse(cr, uid, period, context=ctx)
		presupuesto_move['fiscal_year'] = fiscal_year_id.fiscalyear_id.id

		presupuesto_move_id = presupuesto_move_obj.create(cr, uid, presupuesto_move, context=context)

		gastos_ids = []
		for rubros in rubros_ids:
			presupuesto_move_line = {
				'move_id': presupuesto_move_id,
				'rubros_id': rubros.rubros_id.id,
				'mov_type': 'reg',
				'ammount': contract.contract_v_tto,
			}
			presupuesto_moverubros_obj.create(cr, uid, presupuesto_move_line, context=context)
			gastos_ids.append(rubros.id)

		contract_reg = {
			'rp': presupuesto_move_id,
		}
		self.pool.get('hr.contract').write(cr, uid, [contract.id], contract_reg, context=context)

		return presupuesto_move_id

	def generate_reg(self, cr, uid, ids, context={}):

		contract = self.browse(cr, uid, ids, context=context)[0]

		rubros_ids = []
		# Add only active lines
		for x in contract.cdp_move_rel:
			for line in x.gastos_ids:
				if line: rubros_ids.append(line)

		rp = self.create_reg(cr, uid, contract, rubros_ids, context=context)
		data_obj = self.pool.get('ir.model.data')
		result = data_obj._get_id(cr, uid, 'presupuesto', 'view_presupuesto_compromiso_move_form')
		view_id = data_obj.browse(cr, uid, result).res_id

		return {
			'domain': "[('id','=', " + str(rp) + ")]",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'presupuesto.move',
			'context': context,
			'res_id': rp,
			'view_id': [view_id],
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}

hr_contract_inherit()