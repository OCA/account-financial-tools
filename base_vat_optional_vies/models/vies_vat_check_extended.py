from odoo import fields, models


class ViesVatCheckExtension(models.Model):
    _name = "vies_vat_check_extension"
    _description = "vies_vat_check_extension"
    _order = "requestdate desc, id desc"

    name = fields.Char()
    res_partner_id = fields.Many2one("res.partner")
    countrycode = fields.Char(string="Country code")
    vatnumber = fields.Char(string="VAT number")
    valid = fields.Boolean(string="Valid")
    requestdate = fields.Char("Request date")
    tradername = fields.Char(string="Trader name")
    tradercompanytype = fields.Char(string="Trader company type")
    traderaddress = fields.Char(string="Trader address")
    traderstreet = fields.Char(string="Trader street")
    traderpostcode = fields.Char(string="Trader postcode")
    tradercity = fields.Char(string="Trader city")
    tradernamematch = fields.Boolean(string="Trader name match")
    tradercompanytypematch = fields.Boolean(string="Trader company type match")
    traderstreetmatch = fields.Boolean(string="Trader street match")
    traderpostcodematch = fields.Boolean(string="Trader postcode match")
    tradercitymatch = fields.Boolean(string="Trader city match")
    requestidentifier = fields.Char(string="Request identifier")
