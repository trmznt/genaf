<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, selection, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, button" />
<%namespace file='rhombus:templates/group/functions.mako' import='select_group_js' />
<%!
from rhombus.lib.roles import GUEST
%>

##
<%def name="list_batches(batches)">
<form method='post' action='${request.route_url("genaf.batch-action")}'>
${selection_bar('batch', ('Add New Batch', request.route_url("genaf.batch-edit", id=0)))}
<table id="batch-list" class="table table-striped table-condensed">
<thead><tr><th></th><th>Batch Code</th><th>Samples</th><th>Group</th><th>Status</th></tr></thead>
<tbody>
% for b in batches:
    <tr><td><input type="checkbox" name="batch-ids" value='${b.id}' /> </td>
        <td><a href="${request.route_url('genaf.batch-view', id=b.id)}">${b.code}</a></td>
        <td><a href="${request.route_url('genaf.sample', _query={ 'batch_id': b.id })}">${b.samples.count()}</a></td>
        <td>${b.group.name}</td>
        <td>status</td>
        ##<td>${'PUB' if b.published else 'UNPUB'} ${'SHARED' if b.shared else 'UNSHARED'}</td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%def>


##
<%def name="list_batches_js()">
  ${selection_bar_js("batch", "batch-ids")}
</%def>


##
<%def name="show_batch(batch)">
  <form class='form-horizontal'>
    <fieldset>
      ${input_show('Batch Code', batch.code)}
      ${input_show('Group Owner', batch.group.name)}
      ${textarea_show('Description', batch.desc)}
      ##${input_show('Published', 'Yes' if batch.published else 'No')}
      ##${input_show('Shared', 'Yes' if batch.shared else 'No')}
      ${button_edit('Edit', request.route_url('genaf.batch-edit', id=batch.id))}
    </fieldset>
  </form>
</%def>

##
##
<%def name="show_batch(batch)">
  <table class='table table-condensed'>
  <tr><td class='text-right'>Batch Code : </td><td>${batch.code}</td></tr>
  <tr><td class='text-right'>Group Owner : </td><td>${batch.group.name}</td></tr>
  <tr><td class='text-right'>Description : </td><td>${batch.description}</td></tr>
  <tr><td class='text-right'>Status :</td>
        <td>
            ##${'Published' if batch.published else 'Unpublished'}
            ##${'Shared' if batch.shared else 'Unshared'}
        </td></tr>
  % if not request.user.has_roles(GUEST):
  <tr><td></td>
        <td>${button('Edit', request.route_url('genaf.batch-edit', id=batch.id),
                'icon-edit icon-white')}
        </td></tr>
  % endif
  </table>

</%def>


##
<%def name="edit_batch(batch)">
<form class='form-horizontal input-group-sm' method='post'
        action='${request.route_url("genaf.batch-save", id=batch.id)}' >
  <fieldset>
    ${input_hidden('genaf-batch_id', value = batch.id)}
    ${input_text('genaf-batch_code', 'Batch code', value = batch.code)}
    ${selection('genaf-batch_group_id', 'Primary group',
            params = user_groups,
            value=batch.group_id)}
    ${selection('genaf-assay_provider_id', 'Assay provider group',
            params = all_groups,
            value=batch.assay_provider_id)}
    ${input_textarea('genaf-batch_desc', 'Description', value = batch.description)}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
<%def name="edit_batch_js__(batch)">
  ${select_group_js('#genaf-batch_group_id')}
  ${select_group_js('#genaf-assay_provider_id')}

% if batch.group:
    $('#genaf-batch_group_id').select2("data", { id: '${batch.group.id}', text: '${batch.group.name}' });
    $('#genaf-assay_provider_id').select2("data", { id: '${batch.group.id}', text: '${batch.group.name}' });

% endif
</%def>
##
##
##
<%def name="edit_batch_js(batch)">
  $('#genaf-batch_group_id').select2()}
  $('#genaf-assay_provider_id').select2()}
</%def>
##

