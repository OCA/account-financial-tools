# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import werkzeug.exceptions

from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http, _
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class WebsiteSaleExtended(WebsiteSale):

    @http.route()
    def checkout(self, **post):
        if request.env.user.login == 'public':
            return super(WebsiteSaleExtended, self).cart(access_token=access_token, revive=revive, **post)
        order = request.website.sale_get_order()
        if order.state != 'cancel' and order.credit_overload or order.credit_due > 0.0 or order._credit_limit():
            return request.render("account_credit_control_extend.credit_control", {"current_order": order})
        return super(WebsiteSaleExtended, self).checkout(**post)

    @http.route()
    def cart(self, access_token=None, revive='', **post):
        if request.env.user.login == 'public':
            return super(WebsiteSaleExtended, self).cart(access_token=access_token, revive=revive, **post)
        order = request.website.sale_get_order()
        if order.state == 'cancel':
            request.website.sale_reset()
            return super(WebsiteSaleExtended, self).cart(access_token=access_token, revive=revive, **post)
        if post.get('type') == 'popover':
            # force no-cache so IE11 doesn't cache this XHR
            return super(WebsiteSaleExtended, self).cart(access_token=access_token, revive=revive, **post)
        if order.state != 'cancel' and order.credit_overload or order.credit_due > 0.0 or order._credit_limit():
            return request.render("account_credit_control_extend.credit_control", {"current_order": order})
        return super(WebsiteSaleExtended, self).cart(access_token=access_token, revive=revive, **post)

    @http.route()
    def confirm_order(self, **post):
        order = request.website.sale_get_order()
        #_logger.info("Redirect to control %s:%s" % (order, order._credit_limit()))
        if order.state != 'cancel' and order.credit_overload or order.credit_due > 0.0 or order._credit_limit():
            return request.render("account_credit_control_extend.credit_control", {"current_order": order})
        return super(WebsiteSaleExtended, self).confirm_order(**post)
