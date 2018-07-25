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
								('lib', 'Liberación')], 'Tipo', select=True, required=True, states={'confirm': [('readonly', True)]})
	hide_button_confirm= fields.Boolean(compute='_hide_button_confirm', default=False)	
	rp_move_rel_id = fields.Many2one('account.invoice', string=u'Documento', ondelete='cascade')
	obl_move_rel_id = fields.Many2one('account.voucher', string=u'Documento', ondelete='cascade')




	@api.one
	@api.onchange('gastos_ids')
	def hide_button_change(self):
		if self.gastos_ids:
			diff = self._get_diff_money(self.gastos_ids)
			if diff <= 0:
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
		if self.gastos_ids:
			diff = self._get_diff_money(self.gastos_ids)
			if diff <= 0:
				self.hide_button_confirm = True
			else:
				self.hide_button_confirm = False

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
			return saldo_move - ammount

	""" 
		boton que nos sirve para liberar el presupuesto es usado en la vista
		de cdp, compromiso y obligacion

	"""			


	@api.onchange('presupuesto_rel_move')
	def _onchange_rel_move_ids(self):
		
		val_rel_ids= self.presupuesto_rel_move
		lista_rubros = []
		for x in val_rel_ids:
			rpre_moverubros = self.env['presupuesto.moverubros']
			cdp_moverubros = rpre_moverubros.search([('move_id.id', '=', x.id)])
			_logger.info(cdp_moverubros)
			for rubro in cdp_moverubros:

				if rubro.ammount > 0:

					lista_rubros.append((0,0,{'move_id' : self.id , 'ammount': 0 , 'rubros_id' : rubro.rubros_id.id, 'mov_type' : self.doc_type, 'date' : datetime.now().strftime('%Y-%m-%d'), 'period_id' : self.period_id.id, 'move_rel_id':x.id}))
		#cargando gastos
		_logger.info(lista_rubros)
		self.gastos_ids = lista_rubros







presupuesto_move_inherit()