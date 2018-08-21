#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    d$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
_logger = logging.getLogger(__name__)



class hr_payslip_co(models.Model):
	_inherit = 'hr.payslip'
	_description = 'Pay Slip'

	obl_move_rel = fields.Many2many(comodel_name='presupuesto.move', string="OBL",
						relation='presupuesto_origen_destino_parslip',
						column1='origen_ids',
						column2='destino_ids', 
						domain=[('doc_type', '=' , 'obl')])
	@api.multi
	def process_sheet(self):


		if not self.o_note:
			raise osv.except_osv(_('Error!'),_(u'El Campo Información del pago debe de ser diligenciado'))

		contrato_modificaciones = self.env['contract.modification']
		presupuesto_tools = self.env['presupuesto.tools']
		move_pool = self.env['account.move']
		presupuesto_move_pool = self.env['presupuesto.move']
		presupuesto_moverubros_pool = self.env['presupuesto.moverubros']
		period_pool = self.env['account.period']
		precision = self.env['decimal.precision'].precision_get('Payroll')
		timenow = time.strftime('%Y-%m-%d')




		#nos permite llevar la cuenta de cuantos de los rp que hay en modificaciones 
		#tiene saldo mayor a cero
		count = 0
		for slip in self:

			#con esto buscamos las modificaciones asociadas al contrato, si hay modificaciones miramos que los RP que estan
			#asociados a la modifcacion tengan saldo, agregamos los valores a la lista de contrato_modificaciones_rp_id
			#y aumentamos el count, es importante lo del count, porque si mas de una modificacion tiene saldo entonces esto
			#nos determina que no debemos de crea la obligacion
			contrato_modificaciones_rp = contrato_modificaciones.search([('contract_move_rel_id', '=', slip.contract_id.id)])
			contrato_modificaciones_rp_id = []
			if contrato_modificaciones_rp:
				
				for x in contrato_modificaciones_rp:
					saldo_move = presupuesto_tools.get_saldo(x.rp)
					if saldo_move > 0:
						contrato_modificaciones_rp_id.append(x.rp.id)
						count = count + 1

			line_ids = []
			debit_sum = 0.0
			credit_sum = 0.0

			gastos_ids = []
			rubros_sum = 0.0

			if not slip.period_id:
				ctx = dict(self.env.context or {}, account_period_prefer_normal=True)
				search_periods = period_pool.find(slip.date_to, context=ctx)
				period_id = search_periods[0].id

			else:
				period_id = slip.period_id.id

			partner_eps_id = slip.employee_id.eps_id.id
			partner_fp_id = slip.employee_id.fp_id.id
			partner_fc_id = slip.employee_id.fc_id.id
			date_move = slip.date_payment

			rp_contract = slip.contract_id.rp
			obl = slip.obl_move_rel
			obl_description = slip.name
			fiscalyear_id = slip.period_id.fiscalyear_id.id if slip.period_id else period_pool.browse(period_id)[0].fiscalyear_id.id

			#creamos esta variable para saber que valor se le pasa el momento de crear la obligacion automatica, algo para tener
			#en cuenta es que se tienen algunas condiciones. 
			move_rel_id = 0
			#se validan las condiciones para saber si creamos la obligacion o no
			#las condiciones son que el RP principal tenga saldo y las modificaciones no.
			#la otra condicion es que el RP principal no tenga saldo, y solo una de las modificaciones
			#si lo tenga


			rp_rubros = []

			if presupuesto_tools.get_saldo(rp_contract) > 0 and not count:
				move_rel_id = rp_contract.id
			elif presupuesto_tools.get_saldo(rp_contract) <= 0 and count == 1:
				move_rel_id = contrato_modificaciones_rp_id[0]


			if move_rel_id:
			
				rubros_ids = presupuesto_moverubros_pool.search([('move_id', '=', move_rel_id)])	

				if rubros_ids:

					rp_rubros = [x.rubros_id.id for x in rubros_ids]

			_logger.info(rp_rubros)

			default_partner_id = slip.employee_id.address_home_id.id
			name = _('Payslip of %s') % (slip.employee_id.name)
			move = {
				'narration': name,
				'date': date_move,
				'ref': slip.number,
				'journal_id': slip.journal_id.id,
				'period_id': period_id,
			}

			move_arreglos = []
			for x in rp_contract:
				move_arreglos.append(x.id)

			presupuesto_move = {
				'doc_type': 'obl',
				'date': date_move,
				'partner_id': default_partner_id,
				'presupuesto_rel_move': [(6, 0,move_arreglos)],
				'description': obl_description,
				'fiscal_year': fiscalyear_id,
				'period_id': period_id,
				'payslip_id': slip.id,
				'state': 'confirm',
			}

			for line in slip.details_by_salary_rule_category:
				amt = slip.credit_note and -line.total or line.total
				partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
				debit_account_id = line.salary_rule_id.account_debit.id
				credit_account_id = line.salary_rule_id.account_credit.id
				rubro_category_code = line.salary_rule_id.category_id.code
				rubro_id = line.salary_rule_id.rubro_id.id

				if line.salary_rule_id.origin_partner == 'employee':
					partner_id = default_partner_id
				elif line.salary_rule_id.origin_partner == 'eps':
					partner_id = partner_eps_id
				elif line.salary_rule_id.origin_partner == 'fp':
					partner_id = partner_fp_id
				elif line.salary_rule_id.origin_partner == 'fc':
					partner_id = partner_fc_id
				elif line.salary_rule_id.origin_partner == 'rule':
					partner_id = line.salary_rule_id.partner_id.id
				else:
					partner_id = default_partner_id

				if debit_account_id:

					debit_line = (0, 0, {
					'name': line.name,
					'date': date_move,
					#~ 'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_debit.type in ('receivable', 'payable')) and partner_id or False,
					'partner_id': partner_id,
					'account_id': debit_account_id,
					'journal_id': slip.journal_id.id,
					'period_id': period_id,
					'debit': amt > 0.0 and amt or 0.0,
					'credit': amt < 0.0 and -amt or 0.0,
					'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
					'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
					'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
				})
					line_ids.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

				if credit_account_id:

					credit_line = (0, 0, {
					'name': line.name,
					'date': date_move,
					#~ 'partner_id': (line.salary_rule_id.register_id.partner_id or line.salary_rule_id.account_credit.type in ('receivable', 'payable')) and partner_id or False,
					'partner_id': partner_id,
					'account_id': credit_account_id,
					'journal_id': slip.journal_id.id,
					'period_id': period_id,
					'debit': amt < 0.0 and -amt or 0.0,
					'credit': amt > 0.0 and amt or 0.0,
					'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
					'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
					'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
				})
					line_ids.append(credit_line)
					credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

				if rubro_id and (rubro_category_code == "BASIC" or rubro_category_code == "ALW"):
					obl_line = (0,0, {
						'rubros_id' : rubro_id,
						'mov_type': 'obl',
						'period_id': period_id,
						'date': date_move,
						'ammount': amt or 0.0,
						'move_rel_id': move_rel_id
					})
					gastos_ids.append(obl_line)
					rubros_sum += obl_line[2]['ammount']
					
			if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_credit_account_id.id
				if not acc_id:
					raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Credit Account!')%(slip.journal_id.name))
				adjust_credit = (0, 0, {
					'name': _('Adjustment Entry'),
					'date': date_move,
					'partner_id': False,
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'period_id': period_id,
					'debit': 0.0,
					'credit': debit_sum - credit_sum,
				})
				line_ids.append(adjust_credit)

			elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_debit_account_id.id
				if not acc_id:
					raise osv.except_osv(_('Configuration Error!'),_('The Expense Journal "%s" has not properly configured the Debit Account!')%(slip.journal_id.name))
				adjust_debit = (0, 0, {
					'name': _('Adjustment Entry'),
					'date': date_move,
					'partner_id': False,
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'period_id': period_id,
					'debit': credit_sum - debit_sum,
					'credit': 0.0,
				})
				line_ids.append(adjust_debit)
			move.update({'line_id': line_ids})
			move_id = move_pool.create(move)

			presupuesto_move.update({'gastos_ids': gastos_ids})
			_logger.info(presupuesto_move)
#			if not obl:

#				if (presupuesto_tools.get_saldo(rp_contract) > 0 and not count) or (presupuesto_tools.get_saldo(rp_contract) <= 0 and count == 1):
#					obl_id = presupuesto_move_pool.create(presupuesto_move)

#					self.write({'move_id': move_id.id, 'period_id' : period_id, 'obl_move_rel':[(6, 0, [obl_id.id])]})
				
			
			self.write({'move_id': move_id.id, 'period_id' : period_id})



			if slip.journal_id.entry_posted:
				move_pool.post([move_id.id])
		return True

	@api.multi
	def create_voucher_slip(self, slip, details_ids):

		account_voucher_obj = self.env['account.voucher']
		account_voucher_line_obj = self.env['account.voucher.line']

		account_move_line_obj = self.env['account.move.line']

		amt = 0

		for line in details_ids:
			category_code = line.salary_rule_id.category_id.code
			if category_code == "NET":
				amt = slip.credit_note and -line.total or line.total


		move_arreglos = []
		for x in slip.obl_move_rel:
			move_arreglos.append(x.id)

		_logger.info(move_arreglos)		

		account_voucher = {
			'date': slip.date_payment,
			'partner_id': self.env['res.partner']._find_accounting_partner(slip.employee_id.address_home_id).id,
			'amount': amt or 0.0,
			'obl_move_rel': [(6, 0, move_arreglos)],
			'narration': slip.o_note,
			'type': 'payment',
			'journal_id': 27,
			'account_id': 831,
			'pre_line': True,
		}

		period_pool = self.env['account.period']
		ctx = dict(self.env.context or {}, account_period_prefer_normal=True)
		search_periods = period_pool.find(slip.date_payment)
		period = search_periods[0]
		account_voucher['period_id'] = period.id
		account_voucher_id = account_voucher_obj.create(account_voucher)

		move_ids =[]
		move_ids = account_move_line_obj.search([('move_id', '=', slip.move_id.id)])

		name_voucher_line = slip.move_id.name

		line_dr_ids = []
		for record in move_ids:
			if record.partner_id.id == slip.employee_id.address_home_id.id and record.account_id.user_type.code == 'payable':
				move_line = record.id
				account = record.account_id.id

				voucher_line = {
					'voucher_id': account_voucher_id.id,
					'move_line_id': move_line,
					'account_id': account,
					'reconcile': True,
					'name': name_voucher_line,
					'type': 'dr',
					'amount': amt or 0.0,
				}
				account_voucher_line_obj.create(voucher_line)
				line_dr_ids.append(record.id)

		self.write({'ce': account_voucher_id.id, 'state': 'done' })


		return account_voucher_id.id


	@api.multi
	def generate_voucher(self):


		slip = self

		details_ids = []
		# Add only active lines
		for line in slip.details_by_salary_rule_category:
			if line: details_ids.append(line)


		voucher = self.create_voucher_slip(slip, details_ids)
		data_obj = self.env['ir.model.data']
		result = data_obj._get_id('presupuesto', 'presupuesto_payment_voucher_form')
		view_id = data_obj.browse(result).res_id

		return {
			'domain': "[('id','=', " + str(voucher) + ")]",
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.voucher',
			'context': self.env.context,
			'res_id': voucher,
			'view_id': [view_id],
			'type': 'ir.actions.act_window',
			'nodestroy': True,
			'target': 'new',
		}


