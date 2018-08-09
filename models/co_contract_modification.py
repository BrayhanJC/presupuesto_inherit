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


class contract_modification(models.Model):
	_name = 'contract.modification'
	_description = 'Contract Modification'

	name= fields.Char(string='N°')
	date_begin = fields.Date(string='Fecha')
	description= fields.Char(string=u'Descripción')
	date_end = fields.Date(string=u'Duración Hasta')
	additional_value = fields.Float(string='Valor Adicional')
	cdp_move_rel = fields.Many2many(comodel_name='presupuesto.move', string="CDP",
						relation='presupuesto_origen_destino_contract',
						column1='origen_ids',
						column2='destino_ids', 
						domain=[('doc_type', '=' , 'cdp')])
	rp = fields.Many2one('presupuesto.move', string='RP', ondelete='restrict', domain=[('doc_type', '=' , 'reg'), ('state','=','confirm')])
	contract_move_rel_id = fields.Many2one('hr.contract', string=u'Contract')


	@api.multi
	def button_create_rp(self):
		_logger.info('hola')
contract_modification()