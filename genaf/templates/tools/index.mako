<%inherit file="rhombus:templates/base.mako" />

<h3>${header_text}</h3>

<div class='row'><div class='col-md-8'>

<ul class='nav nav-tabs' role='tablist'>
  <li role='presentation' class='active'>
    <a href="#form_pane" aria-controls='form_pane' role='tab' data-toggle='tab'>Form Query</a>
  </li>
  <li role='presentation'>
    <a href="#yaml_pane" aria-controls='yaml_pane' role='tab' data-toggle='tab'>YAML Query</a>
  </li>
</ul>

<div class='tab-content'>

  <div role='tabpanel' class='tab-pane active' id='form_pane'>

    <div class='row'><div class='col-md-12'>
      &nbsp;
      ${queryform}
    </div></div>
  </div>

  <div role='tabpanel' class='tab-pane' id='yaml_pane'>

    <div class='row'><div class='col-md-12'>
      &nbsp;
      ${yamlform}
    </div></div>
  </div>

</div>

</div></div>
##
##
<%def name="jscode()">
${code | n}
</%def>
