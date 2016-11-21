<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/sample/functions.mako" import="show_sample, show_sample_js" />
<%namespace file="genaf:templates/assay/functions.mako" import="list_assays, list_assays_js, add_assay_modal" />
<%namespace file="genaf:templates/allele/functions.mako" import="list_alleles_column" />


<h2>Sample Viewer</h2>

${show_sample(sample)}

<h3>Alleles</h3>
${list_alleles_column(allele_list)}

<h3>Assay</h3>
${list_assays(sample.assays, request)}

<!-- modal -->
${add_assay_modal(sample)}
<!-- /modal -->


<%def name="jscode()">
  ${show_sample_js(sample)}
  ${list_assays_js(sample)}
</%def>

