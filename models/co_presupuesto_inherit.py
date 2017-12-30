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
import logging
import difflib
from openerp import models, fields, api, _
import re
import codecs
from openerp.tools.translate import _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import math
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
import time
_logger = logging.getLogger(__name__)

class presupuesto_move_compromiso_inherit(models.Model):
    _inherit = 'presupuesto.move'
    _order = 'date desc'



presupuesto_move_compromiso_inherit()