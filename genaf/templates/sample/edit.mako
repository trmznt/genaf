<%inherit file="rhombus:templates/base.mako" />
<%namespace file="plasmoms:templates/sample/widget.mako" import="edit_plasmosample, edit_plasmosample_js" />

<h2>Sample Editor</h2>

<div class='row'><div class='span8'>
  ${edit_plasmosample(sample, subject, batch)}
</div></div>

<%def name="jscode()">
  ${edit_plasmosample_js(sample)}
</%def>
