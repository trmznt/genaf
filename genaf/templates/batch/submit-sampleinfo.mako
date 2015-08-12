<%inherit file='rhombus:templates/base.mako' />
<%namespace file="rhombus:templates/common/form.mako" import="input_file, input_hidden, radioboxes, submit_bar" />


<h2>Sample Data Submission</h2>

<p>Your sample data contains:
<ul>
  <li>Existing sample code(s): ${existing_samples}</li>
  <li>New sample code(s): ${new_samples}</li>
</ul>
<p>

<form method='POST' action='${request.route_url("genaf.batch-action")}'>

  <fieldset>
    ${input_hidden('batch_id', value=batch.id)}
    ${input_hidden('_path', value=path)}
    ${radioboxes('options', 'Options', params = option_params)}
    ${submit_bar('Proceed', 'process-sample-info')}
  </fieldset>
</form>
