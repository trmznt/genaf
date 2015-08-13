<%inherit file="rhombus:templates/base.mako" />
<%namespace file='genaf:templates/batch/functions.mako' import='edit_batch, edit_batch_js' />

<h2>Batch</h2>
<div class='row'><div class='col-md-10'>
  ${editform}
</div></div>

<%def name="jscode()">
  ${edit_batch_js(batch)}
</%def>

