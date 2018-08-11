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

	cdp_move_rel = fields.One2many('presupuesto.move', 'rp_move_rel_id', domain=[('doc_type', '=' , 'cdp')])
	modification_move_rel = fields.One2many('contract.modification', 'contract_move_rel_id', 'Modificaciones')
	additions = fields.Float('Adiciones',compute='_compute_additions', readonly=True)
	valor_ejecutar= fields.Float('Valor Por Ejecutar',compute='_amount_ejecutarr',readonly=True)

	@api.one
	@api.depends('modification_move_rel') 
	def _compute_additions(self):
		additions=0.0
		if self.modification_move_rel:

			for record in self.modification_move_rel:
				additions+=record.additional_value

		self.additions=additions


	@api.one
	def _amount_ejecutarr(self):
		res = {}
		amount_ejecutar = 0.0
		for move in self:
			contract_v_tto = move.contract_v_tto
			contract_av_eje = move.contract_av_eje
			valor_liquidaciones = move.valor_liquidaciones
			amount_ejecutar = contract_v_tto-contract_av_eje-valor_liquidaciones
			res[move.id] = amount_ejecutar + self.additions
		
		self.valor_ejecutar=amount_ejecutar+ self.additions
		return res
	

	def create_reg(self, cr, uid, contract, rubros_ids, context={}):

		presupuesto_move_obj = self.pool.get('presupuesto.move')
		presupuesto_moverubros_obj = self.pool.get('presupuesto.moverubros')

		move_arreglos=[]
		for x in contract.cdp_move_rel:
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
		_logger.info(len(contract.cdp_move_rel))
		_logger.info(contract.contract_v_tto)
		gastos_ids = []
		for rubros in rubros_ids:
			presupuesto_move_line = {
				'move_id': presupuesto_move_id,
				'rubros_id': rubros.rubros_id.id,
				'mov_type': 'reg',
				'ammount': 0 if len(contract.cdp_move_rel) > 1 else contract.contract_v_tto,
				'move_rel_id':rubros.move_id.id
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

	@api.onchange('modification_move_rel')
	def _onchange_modification(self):
	
		if self.modification_move_rel:

			date_old="1000-01-01"
			date_old = datetime.strptime(date_old, "%Y-%m-%d").date()
			for x in self.modification_move_rel:
				if x.date_end:
					date_end= datetime.strptime(x.date_end, "%Y-%m-%d").date()
					if x.date_end < self.date_end:
						raise Warning(_('El campo Duración Hasta debe ser mayor a la fecha final del contrato, este campo se encuentra en el menú <Información>.'))
					
					if date_end > date_old:
						date_old=date_end

			self.date_end=date_old



	@api.onchange('cdp_move_rel')
	def domain_rp(self):

		
		if self.cdp_move_rel:
			if self.notes:

				cdp_ids = [x.id for x in self.cdp_move_rel]
				destino_ids = []
				obj_presupuesto_origen_destino = self.env['presupuesto.moverubros']

				presupuesto_origen_destino_ids = obj_presupuesto_origen_destino.search([('move_rel_id', 'in', cdp_ids)])

				if presupuesto_origen_destino_ids:
					for x in presupuesto_origen_destino_ids:
						destino_ids.append(x.move_id.id)

				if destino_ids:
					return {'domain': {'rp': [('id', 'in', (destino_ids))]}}
			else:
				raise Warning(_('Debe diligenciar el campo notas, que se encuentra en el menú <Información>.'))




hr_contract_inherit()