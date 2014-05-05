# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Numérigraphe SARL.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

from openerp.osv import fields, orm


# XXX: this is used for checking various codes such as credit card
# numbers: should it be moved to tools.py?
def _check_luhn(string):
    """Luhn test to check control keys

    Credits:
        http://rosettacode.org/wiki/Luhn_test_of_credit_card_numbers#Python
    """
    r = [int(ch) for ch in string][::-1]
    return (sum(r[0::2]) + sum(sum(divmod(d * 2, 10))
                               for d in r[1::2])) % 10 == 0


class Partner(orm.Model):
    """Add the French official company identity numbers SIREN, NIC and SIRET"""
    _inherit = 'res.partner'

    def _get_siret(self, cr, uid, ids, field_name, arg, context=None):
        """Concatenate the SIREN and NIC to form the SIRET"""
        return {partner.id: '%s%s' % (partner.siren, partner.nic or '*****')
                            if partner.siren else ''
                for partner in self.browse(cr, uid, ids, context=context)}

    def _check_siret(self, cr, uid, ids):
        """Check the SIREN's and NIC's keys (last digits)"""
        for partner in self.browse(cr, uid, ids, context=None):
            if partner.nic:
                # Check the NIC type and length
                if not partner.nic.isdecimal() or len(partner.nic) != 5:
                    return False
            if partner.siren:
                # Check the SIREN type, length and key
                if (not partner.siren.isdecimal()
                        or len(partner.siren) != 9
                        or not _check_luhn(partner.siren)):
                    return False
                # Check the NIC key (you need both SIREN and NIC to check it)
                if partner.nic and not _check_luhn(partner.siren
                                                   + partner.nic):
                    return False
        return True

    _columns = {
        'siren': fields.char('SIREN', size=9,
                             help="The SIREN number is the official identity "
                                  "number of the company in France. It makes "
                                  "the first 9 digits of the SIRET number."),
        'nic': fields.char('NIC', size=5,
                           help="The NIC number is the official rank number "
                                "of this office in the company in France. It "
                                "makes the last 5 digits of the SIRET "
                                "number."),
        'siret': fields.function(
            _get_siret, type="char", string='SIRET',
            method=True, size=14,
            store={
                'res.partner': [lambda self, cr, uid, ids, context=None: ids,
                                ['siren', 'nic'], 10]},
            help="The SIRET number is the official identity number of this "
                 "company's office in France. It is composed of the 9 digits "
                 "of the SIREN number and the 5 digits of the NIC number, ie. "
                 "14 digits."),
        'company_registry': fields.char(
            'Company Registry', size=64,
            help="The name of official registry where this "
                 "company was declared."),
    }

    _constraints = [
        (_check_siret,
         "The SIREN or NIC number is incorrect.",
         ["siren", "nic"]),
    ]
