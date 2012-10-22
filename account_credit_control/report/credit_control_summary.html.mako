<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body>
    %for comm in objects :
    ${setLang(comm.partner_id.lang)}
       <%
             current_uri = '%s_policy_template' % (comm.partner_id.lang)
             if not context.lookup.has_template(current_uri):
                 context.lookup.put_string(current_uri, comm.current_policy_level.mail_template_id.body_html)
       %>
       <%include file="${current_uri}" args="object=comm,mode='pdf'"/>
       </br>
     %endfor
</body>
</html>
