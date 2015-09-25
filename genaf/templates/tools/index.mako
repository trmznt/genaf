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
      &nbsp;<br />
      <p>More detailed information about each field can be found <a>here</a>.</p>
      ${queryform}
    </div></div>
  </div>

  <div role='tabpanel' class='tab-pane' id='yaml_pane'>

    <div class='row'><div class='col-md-12'>
      &nbsp;<br />
      <p>More detailed information about YAML syntax can be found <a>here</a>.</p>
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
