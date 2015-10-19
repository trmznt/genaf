<%inherit file="rhombus:templates/base.mako" />

<h3>${header_text}</h3>

<div class='row'><div class='col-md-12'>

${html}

</div></div>
##
##
<%def name="jscode()">
${code | n}
</%def>
