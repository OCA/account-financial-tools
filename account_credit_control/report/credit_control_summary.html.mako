<html>
  <head>
    <style type="text/css">
      ${css}
body {
    font-family: helvetica;
    font-size: 12px;
}

.custom_text {
    font-family: helvetica;
    font-size: 12px;
}

table {
    font-family: helvetica;
    font-size: 12px;
}

.header {
    margin-left: 0px;
    text-align: left;
    width: 300px;
    font-size: 12px;
}

.title {
    font-size: 16px;
    font-weight: bold;
}

.basic_table{
    text-align: center;
    border: 1px solid lightGrey;
    border-collapse: collapse;
    font-family: helvetica;
    font-size: 12px;
}

.basic_table th {
    border: 1px solid lightGrey;
    font-size: 11px;
    font-weight: bold;

}

.basic_table td {
    border: 1px solid lightGrey;
    font-size: 12px;
}

.list_table {
    border-color: black;
    text-align: center;
    border-collapse: collapse;
}

.list_table td {
    border-color: gray;
    border-top: 1px solid gray;
    text-align: left;
    font-size: 12px;
    padding-right: 3px;
    padding-left: 3px;
    padding-top: 3px;
    padding-bottom:3px;
}

.list_table th {
    border-bottom: 2px solid black;
    text-align: left;
    font-size: 11px;
    font-weight: bold;
    padding-right: 3px
    padding-left: 3px
}

.list_table thead {
    display: table-header-group;
}

.address table {
    font-size: 11px;
    border-collapse: collapse;
    margin: 0px;
    padding: 0px;
}

.address .shipping {

}

.address .invoice {
    margin-top: 10px;
}

.address .recipient {
    font-size: 13px;
    margin-right: 120px;
    margin-left: 350px;
    float: right;
}


table .address_title {
    font-weight: bold;
}

.address td.name {
    font-weight: bold;
}

td.amount, th.amount {
    text-align: right;
    padding-right:2px;
}

h1 {
    font-size: 16px;
    font-weight: bold;
}

tr.line .note {
    border-style: none;
    font-size: 9px;
    padding-left: 10px;
}

tr.line {
    margin-bottom: 10px;
}
    </style>
  </head>
  <body>

    %for comm in objects :
    <% setLang(comm.get_contact_address().lang) %>
    <div class="address">
        <table class="recipient">
          <%
             add = comm.get_contact_address()
          %>
            %if comm.partner_id.id == add.id:
              <tr><td class="name">${comm.partner_id.title and comm.partner_id.title.name or ''} ${comm.partner_id.name }</td></tr>
              <% address_lines = comm.partner_id.contact_address.split("\n") %>

            %else:
              <tr><td class="name">${comm.partner_id.name or ''}</td></tr>
              <tr><td>${add.title and add.title.name or ''} ${add.name}</td></tr>
              <% address_lines = add.contact_address.split("\n")[1:] %>
            %endif
            %for part in address_lines:
                %if part:
                <tr><td>${part}</td></tr>
                %endif
            %endfor
        </table>
        <br/>
        <br/>
        <br/>
        <br/>

    </div>
        <br/>
        <br/>
        <br/>
    <div>

      <h3 style="clear: both; padding-top: 20px;">
          ${_('Reminder')}: ${comm.current_policy_level.name or '' }
      </h3>

      <p>${_('Dear')},</p>
      <p class="custom_text" width="95%">${comm.current_policy_level.custom_text.replace('\n', '<br />')}</p>

      <br/>
      <br/>
      <p><b>${_('Summary')}<br/></b></p>
      <table class="basic_table" style="width: 100%;">
      <tr>
        <th width="200">${_('Invoice number')}</th>
        <th>${_('Invoice date')}</th>
        <th>${_('Date due')}</th>
        <th>${_('Invoiced amount')}</th>
        <th>${_('Open amount')}</th>
        <th>${_('Currency')}</th>

      </tr>
%for line in comm.credit_control_line_ids:
      <tr>
      %if line.invoice_id:
          <td width="200">${line.invoice_id.number}
              %if line.invoice_id.name:
              <br/>
              ${line.invoice_id.name}
              %endif
          </td>
      %else:
          <td width="200">${line.move_line_id.name}</td>
      %endif
        <td class="date">${line.date_entry}</td>
        <td class="date">${line.date_due}</td>
        <td class="amount">${line.amount_due}</td>
        <td class="amount">${line.balance_due}</td>
        <td class="amount">${line.currency_id.name or comm.company_id.currency_id.name}</td>
      </tr>
%endfor
      </table>
      <br/>
      <br/>
<%doc>
      <!-- uncomment to have info after summary -->
      <p>${_('If you have any question, do not hesitate to contact us.')}</p>

      <p>${comm.user_id.name} ${comm.user_id.email and '<%s>'%(comm.user_id.email) or ''}<br/>
      ${comm.company_id.name}<br/>
      % if comm.company_id.street:
      ${comm.company_id.street or ''}<br/>

      % endif

      % if comm.company_id.street2:
      ${comm.company_id.street2}<br/>
      % endif
      % if comm.company_id.city or comm.company_id.zip:
      ${comm.company_id.zip or ''} ${comm.company_id.city or ''}<br/>
      % endif
      % if comm.company_id.country_id:
      ${comm.company_id.state_id and ('%s, ' % comm.company_id.state_id.name) or ''} ${comm.company_id.country_id.name or ''}<br/>
      % endif
      % if comm.company_id.phone:
      Phone: ${comm.company_id.phone}<br/>
      % endif
      % if comm.company_id.website:
      ${comm.company_id.website or ''}<br/>
      % endif
</%doc>

      <p style="page-break-after:always"></p>
    %endfor

  </body>
</html>
