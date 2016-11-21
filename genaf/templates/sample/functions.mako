<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />

<%!
from rhombus.lib.roles import GUEST
%>

##
<%def name="list_samples(samples)">
<form method='post' action='${request.route_url("genaf.sample-action")}'>
${selection_bar('sample')}

<table id='sample-list' class='table table-striped table-condensed'>
<thead><tr>
  <th></th>
  <th>Sample code</th>
  <th>Batch</th>
  <th>Assay</th>
  <th>Marker</th>
</tr></thead>
<tbody>
% for s in samples:
  <tr><td><input type="checkbox" name="sample-ids" value="${s.id}" /> </td>
      <td><a href="${request.route_url('genaf.sample-view', id=s.id)}">${s.code}</a></td>
      <td>${h.link_to( s.batch.code, request.route_url('genaf.batch-view', id=s.batch.id))}</td>
      <td>${s.assays.count()}</td>
      <td>${len(s.markers)}</td>
  </tr>
% endfor
</tbody></table>
</form>
</%def>

##
<%def name="list_samples_js()">
  ${selection_bar_js("sample", "sample-ids")}
</%def>

##
<%def name="edit_sample(sample, batch=None)">
<form class='form-horizontal' method='post'
    action='${request.route_url("genaf.sample-save", id=sample.id)}'>
  <fieldset>
    ${input_hidden('genaf-sample_batch_id', value = sample.batch_id)}
    ${input_hidden('genaf-sample_id', value = sample.id)}
    ${input_show('Sample batch', batch.code)}
    ${input_text('genaf-sample_code', 'Sample code', value = sample.code or '')}
    ${input_text('genaf-sample_collection_date', 'Collection date', value = sample.collection_date or '')}
    ${input_text('genaf_sample_comment', 'Comment', value = sample.comments or '')}
    ${selection_ek('genaf-sample_type_id', 'Sample type', '@SAMPLE_TYPE', value = sample.type_id or '')}
    ${checkboxes('genaf-sample_shared', 'Shared', [('genaf-sample_shared', '', sample.shared)] )}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
<%def name="edit_sample_js(sample)">
</%def>

##
<%def name="show_sample_XXX(sample)">
<form class='form-horizontal'>
  <fieldset>
    ${input_show('Sample batch', h.literal('<a href="' + request.route_url('genaf.sample', _query={ 'batch_id': sample.batch.id }) + '"> ' + sample.batch.code + '</a>'))}
    ${input_show('Sample code', sample.code)}
    ${input_show('Collection date', sample.collection_date)}
    ${button_edit('Edit', request.route_url('genaf.sample-edit', id=sample.id))}
  </fieldset>
</form>
</%def>

##
<%def name="show_sample(sample)">
<pre style="font-family: 'PT Mono'; line-height: 11px; font-size: 12px;">
    ${'%15s : %s<br />' % ('Sample Code', sample.code) | n}
    ${'%15s : <a href="%s">%s</a><br />' % ('Batch Code',
                request.route_url('genaf.batch', sample.batch.id),
                sample.batch.code) | n}
##    ${'%15s : <a href="%s">%s</a><br />' % ('Subject Code',
##               request.route_url('plasmogen.subject', sample.subject.id),
##                sample.subject.code) | n}
    ${'%15s : %s<br />' % ('Collection date', sample.collection_date ) | n}
    ${'%15s : %s<br />' % ('Location', sample.location.render() ) | n}
</pre>
% if not request.user.has_roles(GUEST):
${button_edit('Edit', request.route_url('genaf.sample-edit', id=sample.id))}
% endif
</%def>



##
<%def name="show_sample_js(sample)">
</%def>
