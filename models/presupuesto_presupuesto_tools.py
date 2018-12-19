# -*- coding: utf-8 -*-

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




class Presupuesto(models.Model):
	_name = 'presupuesto.tools'
	_description = 'Reusable Methods'
	

	def get_saldo(self, presupuesto_move_id):

		saldo_total = 0 
		move_val = 0
		saldo_rel = 0

		if presupuesto_move_id:

			saldo_total = presupuesto_move_id.amount_total

			presupuesto_moverubros_pool = self.env['presupuesto.moverubros']

			presupuesto_moverubros_ids = presupuesto_moverubros_pool.search([('move_id', '=', presupuesto_move_id.id), 
										('move_id.state', '=', 'confirm'), 
										('move_id.fiscal_year', '=', presupuesto_move_id.fiscal_year.id),
										])


			presupuesto_moverubros_relacionados_ids = presupuesto_moverubros_pool.search([('move_rel_id', '=', presupuesto_move_id.id), 
							('move_id.state', '=', 'confirm'), 
							('move_id.fiscal_year', '=', presupuesto_move_id.fiscal_year.id)])

			if presupuesto_moverubros_relacionados_ids:

				for x in presupuesto_moverubros_relacionados_ids:
					move_val = move_val + x.ammount

			if presupuesto_moverubros_ids:

				for x in presupuesto_moverubros_ids:
					saldo_rel = saldo_rel + x.ammount

		return (saldo_rel - move_val) if saldo_rel else move_val



	
	def get_saldo_obligaciones(self, presupuesto_move_id):

		saldo_total = 0 
		move_val = 0
		total = 0

		if presupuesto_move_id:

			presupuesto_moverubros_pool = self.env['presupuesto.moverubros']

			presupuesto_move_ids = presupuesto_moverubros_pool.search([('move_rel_id', '=', presupuesto_move_id.id), 
							('move_id.state', '=', 'confirm'), 
							('move_id.fiscal_year', '=', presupuesto_move_id.fiscal_year.id)])


			saldo_total = presupuesto_move_id.amount_total
			total = saldo_total
			if presupuesto_move_ids:

				for x in presupuesto_move_ids:

					move_val = move_val + x.ammount

				total = saldo_total - move_val if move_val else saldo_total 	


			presupuesto_move_id.write({'saldo_sin_utilizar': total})
			_logger.info(total)
			return total
			



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
			_logger.info(saldo_move)
			_logger.info(ammount)
			return saldo_move - ammount




	def update_old_values(self):


		presupuesto_move_pool = self.env['presupuesto.move']
		presupuesto_moverel_pool = self.env['presupuesto.moverubros']
		presupuesto_move_pool_ids = []

		sql = """ 
			SELECT id AS id
			FROM presupuesto_move
			WHERE move_rel IS NOT NULL
		"""

		self.env.cr.execute( sql )
		res = self.env.cr.dictfetchall(  )

		if res:

			for x in res:

				move_id = presupuesto_move_pool.browse(x.get('id'))

				if move_id:

					values = {

						'presupuesto_rel_move': [(6, 0, [move_id.move_rel.id])]

					}

					move_id.write(values)

					presupuesto_moverel_id = presupuesto_moverel_pool.search([('move_id', '=', x.get('id'))])
					
					if presupuesto_moverel_id:

						for z in presupuesto_moverel_id:

							z.write({'move_rel_id': move_id.move_rel.id})



	def uptdate_old_values_account_invoice(self):

		sql = """ 
			SELECT id AS id
			FROM account_invoice
			WHERE rp IS NOT NULL
		"""

		self.env.cr.execute( sql )
		res = self.env.cr.dictfetchall(  )

		account_invoice_pool = self.env['account.invoice']

		if res:

			for x in res:

				account_invoice_id = account_invoice_pool.browse(x.get('id'))

				if account_invoice_id:

					values = {

						'rp_move_rel': [(6, 0, [account_invoice_id.rp.id])]

					}

					account_invoice_id.write(values)


	def uptdate_old_values_account_voucher(self):

		sql = """ 
			SELECT id AS id
			FROM account_voucher
			WHERE obl IS NOT NULL
		"""

		self.env.cr.execute( sql )
		res = self.env.cr.dictfetchall(  )

		account_voucher_pool = self.env['account.voucher']

		if res:

			for x in res:

				account_voucher_id = account_voucher_pool.browse(x.get('id'))

				if account_voucher_id:

					values = {

						'obl_move_rel': [(6, 0, [account_voucher_id.obl.id])]

					}

					account_voucher_id.write(values)



	def uptdate_old_values_contact(self):

		sql = """ 
			SELECT id AS id
			FROM hr_contract
			WHERE cdp IS NOT NULL
		"""

		self.env.cr.execute( sql )
		res = self.env.cr.dictfetchall(  )

		hr_contract_pool = self.env['hr.contract']

		if res:

			for x in res:

				hr_contract_id = hr_contract_pool.browse(x.get('id'))

				if hr_contract_id:

					values = {

						'cdp_move_rel': [(6, 0, [hr_contract_id.cdp.id])]

					}

					hr_contract_id.write(values)


	def uptdate_old_values_payslip(self):

		sql = """ 
			SELECT id AS id
			FROM hr_payslip
			WHERE obl IS NOT NULL
		"""

		self.env.cr.execute( sql )
		res = self.env.cr.dictfetchall(  )

		hr_payslip_pool = self.env['hr.payslip']

		if res:

			for x in res:

				hr_payslip_id = hr_payslip_pool.browse(x.get('id'))

				if hr_payslip_id:


					values = {

						'obl_move_rel': [(6, 0, [hr_payslip_id.obl.id])]

					}


					hr_payslip_id.write(values)

