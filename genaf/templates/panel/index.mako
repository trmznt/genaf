<%inherit file='rhombus:templates/base.mako' />

<h2>Panels</h2>

<p>Please note that the colours of the marker names reflect the colours of the filters and do not necessarily reflect the emission colours of the dyes.</p>
<div class='row'><div class='col-md-12'>
    ${panel_table}
</div></div>

##
<%def name='jscode()'>
</%def>
