<%inherit file='rhombus:templates/base.mako' />

<h2>Panels</h2>

<p>Please note that the colours of the marker name reflect the colour of the filter and do not necessarily reflect the emission colours of the dyes.</p>
<div class='row'><div class='col-md-12'>
    ${panel_table}
</div></div>

##
<%def name='jscode()'>
</%def>
