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


class presupuesto_moverubros_inherit(models.Model):
	_inherit = 'presupuesto.moverubros'

	@api.one
	@api.depends('ammount', 'saldo_move')
	def _saldo_move(self):
		res = {}
		move_saldo = 0
		obj_tc = self.env['presupuesto.moverubros']
		record = self
		tipo = record.mov_type
		rubro = record.rubros_id.id
		moverel = record.move_id.move_rel.id
		year = record.move_id.fiscal_year.id
		tipo_doc = record.move_id.doc_type

		conditions = [('rubros_id', '=', rubro),
			('move_id.state', '=', 'confirm'),
			('move_id.fiscal_year', '=', year)
		]
		if type( self.id ) == int:
			conditions.append( ('id', '<', self.id) )

		ids = obj_tc.search(conditions)

		if tipo == "reg" or tipo == "obl" or tipo == "pago":
			move_saldo = move_val = saldo_rel = 0.0
			for move in ids:
				if move.move_id.id == moverel:
					saldo_rel += move.ammount
				if move.move_id.move_rel.id == moverel:
					move_val += move.ammount
				move_saldo = saldo_rel - move_val
			self.saldo_move = move_saldo

		if tipo == "cdp" or tipo == "rec" or tipo_doc == 'mod':
			move_saldo = saldo_resta = saldo_suma = 0.0
			for move in ids:
				if move.mov_type == 'ini' or move.mov_type == 'adi' or move.mov_type == 'cre':
					saldo_suma += move.ammount
				if move.mov_type == 'red' or move.mov_type == 'cont' or move.mov_type == 'cdp' or move.mov_type == 'rec':
					saldo_resta += move.ammount
				move_saldo = saldo_suma - saldo_resta
			self.saldo_move = move_saldo
		else:
			self.saldo_move = move_saldo
		self.saldo_move = move_saldo

		return move_saldo

	_columns = {
		'presupuesto_move_name': fields.char('Documento', readonly=True),
		}

presupuesto_moverubros_inherit()