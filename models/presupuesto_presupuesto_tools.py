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


		return saldo_total - (saldo_rel - move_val) if saldo_rel else (saldo_total - move_val)