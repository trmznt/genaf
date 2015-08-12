<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/batch/functions.mako" import="list_batches, list_batches_js" />

<h2>Batches</h2>

<div class='row'><div class='col-md-10'>
  ${list_batches(batches)}
</div></div>

<%def name="jscode()">
  ${list_batches_js()}
</%def>


