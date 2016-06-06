<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/sample/functions.mako" import="list_samples, list_samples_js" />

<h2>Samples</h2>

<form class='form-inline' method='get'>
  <input type='text' id='q' name='q' value='${request.params.get("q","")}' class='input-xlarge' placeholder='QueryText' />
  <button type='submit' cls='btn'>Filter</button>
</form>

${ html | n }

##<div class='row'><div class='col-md-12'>
##% if request.params.get('sampleview') == 'detailed':
##  <!-- show samples in detailed view -->
##% elif request.params.get('sampleview') == 'condensed':
##  <!-- show samples in condensed view -->
##% else:
##  <!-- show samples in standard, simple view -->
##  ${list_samples(samples)}
##% endif
##</div></div>

##
##  START OF METHODS
##
<%def name="stylelink()">
  <link href="${request.static_url('genaf:static/datatables/datatables.min.css')}" rel="stylesheet" />  
</%def>
##
##
<%def name="jslink()">
<script src="${request.static_url('genaf:static/datatables/datatables.min.js')}"></script>
</%def>
##
##
<%def name="jscode()">
${ code | n }
</%def>
##
##
<%def name="jscode_XXX()">
  ${list_samples_js()}
</%def>




