##############################################################################
#
#    Copyright (c) 2008 Camtocamp SA
#    @author JB Aubort, Nicolas Bessi, Joel Grand-Guillaume
#    European Central Bank and Polish National Bank invented by Grzegorz Grzelak
#    Banxico implemented by Agustin Cruz openpyme.mx
#    $Id: $
#    
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsability of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs
#    End users who are looking for a ready-to-use solution with commercial
#    garantees and support are strongly adviced to contract a Free Software
#    Service Company
#    
#    This program is Free Software; you can redistribute it and/or
#    modify it under the terms of the GNU General Public License
#    as published by the Free Software Foundation; either version 2
#    of the License, or (at your option) any later version.
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
{
    "name" : "Currency Rate Update",
    "version" : "0.6",
    "author" : "Camptocamp",
    "website" : "http://camptocamp.com",
    "category" : "Financial Management/Configuration",
    "description": """
Import exchange rates from three different sources on the internet :

1. Admin.ch
   Updated daily, source in CHF.

2. European Central Bank (ported by Grzegorz Grzelak)
   The reference rates are based on the regular daily concertation procedure between
   central banks within and outside the European System of Central Banks,
   which normally takes place at 2.15 p.m. (14:15) ECB time. Source in EUR.
   http://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html

3. Yahoo Finance
   Updated daily

4. Polish National Bank (Narodowy Bank Polski) (contribution by Grzegorz Grzelak)
   Takes official rates from www.nbp.pl. Adds rate table symbol in log.
   You should check when rates should apply to bookkeeping. If next day you should 
   change the update hour in schedule settings because in OpenERP they apply from 
   date of update (date - no hours).
   
5. Banxico for USD & MXN (created by Agustín Cruz)
   Updated daily

In the roadmap : Google Finance.
   Updated daily from Citibank N.A., source in EUR. Information may be delayed.
   This is parsed from an HTML page, so it may be broken at anytime.

The update can be set under de company form. 
You can set for each services which currency you want to update.
The log of the update are visible under the service note.
You can active or deactivate the update.
The module uses internal ir_cron feature from OpenERP, so the job is launched once
the server starts if the 'first execute date' is before the current day.
The module supports multi-company currency in two way :
    the currencies are shared, you can set currency update only on one 
    company
    the currency are separated, you can set currency on every company
    separately
A function field let you know your currency configuration.

If in multi-company mode, the base currency will be the first company's currency
found in database.


Special thanks and contribs to other Main contributor:   Grzegorz Grzelak, Alexis de Lattre
""",
    "depends" : ["base", "account"],
    "init_xml" : ["security/security.xml"],
    "update_xml" : [
                        "currency_rate_update.xml",
                        "company_view.xml",
                    ],
    "demo_xml" : [],
    "active": False,
    "installable": True
}
