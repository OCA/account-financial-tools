<html>
  <head>
    <style type="text/css">
      ${css}
body {
    font-family: helvetica;
    font-size: 11px;
}

.custom_text {
    font-family: helvetica;
    font-size: 11px;
}

table {
    font-family: helvetica;
    font-size: 11px;
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
}

.basic_table th {
    border: 1px solid lightGrey;
    font-size: 12px;
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
    margin-right: 120px;
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
    <% setLang(comm.partner_id.lang) %>
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
    <div>
      <%
        setLang(comm.partner_id.lang)
        current_uri = '%s_policy_template' % (comm.partner_id.lang)
        if not context.lookup.has_template(current_uri):
          # awfully horrible we add page tags here beacause openerp replaced
          # mako by Jinga but not everywere so they sandbox mako into jinga
          # and jinga prevent %page tag to wwork
          context.lookup.put_string(current_uri,
                                    """<%page args="object, user=None, ctx=None, quote=None, format_exception=True, mode='email'" />
                                    """ + comm.current_policy_level.email_template_id.body_html)
      %>
      <%include file="${current_uri}" args="object=comm,user=user,ctx=ctx,quote=quote,format_exception=format_exception,mode='pdf'"/>

      <p style="page-break-after:always"></p>
    %endfor

  </body>
</html>
