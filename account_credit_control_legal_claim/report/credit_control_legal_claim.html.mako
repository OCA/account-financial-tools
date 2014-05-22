## -*- coding: utf-8 -*-
<html>
  <head>
    <style type="text/css">
      ${css}
body {

    font-family: helvetica;
    font-size: 12px;
}

.left_form_no{
    font-family: helvetica;
    font-size: 12px;
    text-align: left;
    border-bottom-style:solid;
    border-width:1px;
    width:30%;
}

.right_form_no{
    font-family: helvetica;
    font-size: 12px;
    text-align: left;
    border-bottom-style:solid;
    border-width:1px;
    width:30%;
}
.custom_text {
    font-family: helvetica;
    font-size: 12px;
}

.receive_date{
    font-family: helvetica;
    font-size: 12px;
    text-align: left;
    font-weight: bold;
}


.claim_office_address{
    font-family: helvetica;
    font-size: 12px;
    text-align: left;
    vertical-align:text-bottom;
}

.stake_holder_table td{
    border-width:1px;
    border-bottom-style:solid;
    border-top-style:solid;
}

.stake_holder_table{
    font-family: helvetica;
    font-size: 12px;
    border-collapse:collapse;
    width: 100%;
}

.stake_holder_name{
    vertical-align:text-top;
    font-weight: bold;
    text-decoration:underline;
    width:30%;
}

.stake_holder_reference{
    vertical-align:text-top;
    width:30%;
}

.claim_reasons{
    font-family: helvetica;
    font-size: 12px;
    font-weight:bold;

}

.claim_table{
    font-family: helvetica;
    font-size: 12px;
    border-collapse:collapse;
    width:55%
}

.summary_table{
    font-family: helvetica;
    font-size: 12px;
    border-collapse:collapse;
    width:55%
}

.paid_amount_summary_table{
    font-family: helvetica;
    font-size: 12px;
    font-weight:bold;
    border-collapse:collapse;
}

td.amount, th.amount {
    text-align: right;
    padding-right:2px;
}

.signature{
    font-family: helvetica;
    font-size: 12px;
    border-collapse:collapse;
}

.date_and_place{
    vertical-align:text-top;
    width:30%;
}

.signature_address{
    vertical-align:text-top;
    width:30%;
}

.title{
    text-align.center;
}

  </style>
  </head>
  <body>

    %for part in objects :
    <% setLang(part.lang) %>
    <br/>
  <h3 class="title" align="center">${_('Legal Claim Requisition')}</h3>
      <table width="100%">
        <tr>
          <td class="left_form_no">${_('From. No')}</td>
          <td></td>
          <td class="right_form_no">${_('Claim No')}</td>
        </tr>
        <tr height="50px">
          <td class="receive_date">${_('Claim receive by office, the:......')}</td>
          <td colspan="2"></td>
          <td></td>
        </tr>
        <tr>
          <td></td>
          <td></td>
          <td class="claim_office_address">${part.claim_office_id.partner_id.display_name}<br/>
        <% address_lines = part.claim_office_id.partner_id.contact_address.split("\n") %>
        %for add_part in address_lines:
            % if add_part:
                ${add_part}<br/>
            % endif
        %endfor
        </td>
        </tr>
      </table>
    <br/>
    <br/>
    <br/>
    <div class="state_style">${_('State:')} ${part.claim_office_id.partner_id.state_id.name}</div>
        <table class="stake_holder_table">
          <%
             debtor = part
             creditor = company.partner_id
          %>
          <tr class="stake_holder_line">
            <td class="stake_holder_name">${_('Debtor:')}</td>
            <td class="stake_holder_address">${part.display_name}<br/>
              <% address_lines = part.contact_address.split("\n") %>
              %for add_part in address_lines:
              % if add_part:
                ${add_part}<br/>
              % endif
        %endfor

            </td>
            <td class="stake_holder_reference">${part.ref or _('N/A')}
                <br/>
                <br/>
                 birthdate ${formatLang(part.birthday_date, date=True) or _('N/A')}
            </td>
          </tr>
          <tr class="stake_holder_line">
            <td class="stake_holder_name">${_('Creditor:')}</td>
            <td class="stake_holder_address">${creditor.display_name} <br/>
              <% address_lines = creditor.contact_address.split("\n") %>
              %for add_part in address_lines:
                % if add_part:
                  ${add_part}<br/>
                % endif
              %endfor
             </td>
            <td class="stake_holder_reference">${creditor.phone or ''} </td>
          </tr>
        </table>
    <br/>
    <br/>
    <div class="claim_reasons">${_('Claim Reasons')}</div>
    <div>

      <table class="claim_table">
      </tr>
%for inv in part.claim_invoices:
      <tr>
        <td class="date">${_('Invoice')} ${inv.number} of ${formatLang(inv.date_invoice, date=True)}, due at ${formatLang(inv.date_due, date=True)}</td>
        <td>${_('Due amount')}</td>
        <td class="amount">${formatLang(inv.residual)} ${part.claim_currency.name}</td>
      </tr>
%endfor
      </table>
      <br/>
      <br/>
      <table class="summary_table">
        <tr>
          <td>${_('Amount due')}</td>
          <td>${formatLang(compute_due_amount(part.claim_invoices))} ${part.claim_currency.name}</td>
          <td></td>
        </tr>
        <tr>
          <td>${_('Dunning Fees')}</td>
          <td>${formatLang(compute_dunning_fees(part.claim_invoices))} ${part.claim_currency.name}</td>
          <td></td>
        </tr>
        <tr>
          <td>${_('Legal Claim Fees')}</td>
            <td>${formatLang(get_legal_claim_fees(part, part.claim_invoices))} ${part.claim_currency.name}</td>
          <td></td>
        </tr>
      </table>
      <table class="paid_amount_summary_table">
        <tr>
          <td height="50px">${_('Debtor already paid amount')} ${formatLang(compute_paid_amount(part.claim_invoices))} ${part.claim_currency.name}</td>
        </tr>
      </table>
      <br/>
      <br/>
      <table class="signature">
        <tr>
          <td class="date_and_place"><b>${_('Date and place')}</b> <br/><br/><br/>
              ${creditor.city or ''}, ${formatLang(today, date=True)}
          </td>
          <td></td>
          <td class="signature_address">${creditor.display_name} <br/>
              <% address_lines = creditor.contact_address.split("\n") %>
              %for add_part in address_lines:
                % if add_part:
                  ${add_part}<br/>
                % endif
              %endfor
             </td>
        </tr>
      </table>
      <p style="page-break-after:always"></p>
    %endfor

  </body>
</html>
