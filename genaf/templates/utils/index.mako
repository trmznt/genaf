<%inherit file="rhombus:templates/base.mako" />

<h3>${title}</h3>

<div class='row'><div class='col-md-8'>
  ${html}
</div></div>

##
##
<%def name='jscode()'>

${code | n}

</%def>
