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



	@api.multi
	def unlink(self):
		res = super(presupuesto_moverubros_inherit, self).unlink()
		_logger.info(res)
		return res

	@api.one
	@api.constrains('ammount')
	def _check_saldo(self):

		saldo_move = self._saldo_move()[ 0 ] if self.mov_type not in ['lobl', 'lreg', 'lcdp'] else self.saldo_move_

		_logger.info(self.ammount)
		_logger.info(saldo_move)
		_logger.info(self._saldo_move())
		if self.mov_type == 'ini' or self.mov_type == 'rec' or self.mov_type == 'adi' or self.mov_type == 'cre':
			return True
		elif self.ammount > saldo_move:
			raise Warning(_('El valor del movimiento no puede ser superior al saldo.'))
		return True





	@api.one
	@api.constrains('mov_type')
	def _check_mov_type(self):
		record = self
		if record.move_id.doc_type == 'ini':
			if not (record.mov_type == 'ini'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'mod':
			if not (record.mov_type == 'adi' or record.mov_type =='red' or record.mov_type =='cre' or record.mov_type =='cont'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'rec':
			if not (record.mov_type == 'rec'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'cdp':
			if not (record.mov_type == 'cdp') and (record.mov_type <> 'lcdp'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'reg':
			if not (record.mov_type == 'reg') and (record.mov_type <> 'lreg'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'obl':
			if not (record.mov_type == 'obl') and (record.mov_type <> 'lobl'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		elif record.move_id.doc_type == 'pago':
			if not (record.mov_type == 'pago'):
				raise ValueError("¡Error! Verifique que el campo Tipo, enseguida de Rubros, corresponda a la operación que desea realizar.")
		
	move_rel_id= fields.Many2one('presupuesto.move', string=u'Documento', size=25)
	saldo_move_ = fields.Float(string='Saldo')
	ammount = fields.Float(string=u'Valor', required=True, default=0)
	mov_type = fields.Selection([
								('ini', 'Inicial'),
								('adi', 'Adición'),
								('red', 'Reducción'),
								('cre', 'Crédito'),
								('cont', 'Contracrédito'),
								('rec', 'Recaudo'),
								('cdp', 'CDP'),
								('reg', 'Compromiso'),
								('obl', 'Obligación'),
								('pago', 'Pago'),
								('lcdp', 'Liberación CDP'),
								('lreg', 'Liberación Compromiso'),
								('lobl', 'Liberación Obligación')], 'Tipo', select=True, required=True)


	@api.one
	@api.depends('move_rel_id')
	def _saldo_move(self):
		res = {}
		move_saldo = 0
		obj_tc = self.env['presupuesto.moverubros']
		record = self
		tipo = record.mov_type
		rubro = record.rubros_id.id
		moverel = record.move_rel_id.id
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
					_logger.info('entro al primero')
					saldo_rel += move.ammount
				if move.move_rel_id.id == moverel:
					_logger.info('entro al segundo')
					move_val += move.ammount

				move_saldo = (saldo_rel - move_val) if saldo_rel else move_val
			self.saldo_move = move_saldo

		if tipo == "cdp" or tipo == "rec" or tipo_doc == 'mod':

			move_saldo = saldo_resta = saldo_suma = 0.0
			for move in ids:
				if move.mov_type == 'ini' or move.mov_type == 'adi' or move.mov_type == 'cre':
					_logger.info('entro al tercero')
					saldo_suma += move.ammount
				if move.mov_type == 'red' or move.mov_type == 'cont' or move.mov_type == 'cdp' or move.mov_type == 'rec':
					_logger.info('entro al cuarto')
					saldo_resta += move.ammount
				move_saldo = saldo_suma - saldo_resta
			self.saldo_move = move_saldo
		else:
			self.saldo_move = move_saldo
		self.saldo_move = move_saldo

		return move_saldo

presupuesto_moverubros_inherit()