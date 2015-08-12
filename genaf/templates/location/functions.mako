<%namespace file="rhombus:templates/common/selection_bar.mako" import="selection_bar, selection_bar_js" />
<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit" />
<%namespace file='rhombus:templates/group/functions.mako' import='select_group_js' />

##
<%def name="list_locations(locations)">
<form method='post' action='${request.route_url("genaf.location-action")}'>
${selection_bar('location', ('Add Location', request.route_url("genaf.location-edit", id=0)))}
<table id="batch-list" class="table table-striped table-condensed">
<thead><tr><th></th><th>ID</th><th>Country</th><th>1st Level</th><th>2nd Level</th><th>3rd Level</th><th>4th Level</th><th>Lat/Lon/Alt</th><th>Samples</th></tr></thead>
<tbody>
% for l in locations:
    <tr><td><input type="checkbox" name="location-ids" value='${l.id}' /> </td>
        <td><a href="${request.route_url('genaf.location-view', id=l.id)}">${l.id}</a></td>
        <td>${l.country}</td>
        <td>${l.level1}</td><td>${l.level2}</td><td>${l.level3}</td><td>${l.level4}</td>
        <td>${l.latitude} / ${l.longitude} / ${l.altitude}</td>
        <td><a href="${request.route_url('genaf.sample', _query={ 'location_id': l.id })}">${l.samples.count()}</a></td>
    </tr>
% endfor
</tbody>
</table>
</form>
</%def>


##
<%def name="list_locations_js()">
  ${selection_bar_js("location", "location-ids")}
</%def>


##
<%def name="edit_location(location)">
<form class='form-horizontal' method='post'
    action='${request.route_url("genaf.location-save", id=location.id)}' >
  <fieldset>
    ${input_hidden('genaf-location_id', value = location.id)}
    ${input_text('genaf-country', 'Country', value = location.country or '')}
    ${input_text('genaf-adminl1', '1st Level', value = location.level1 or '')}
    ${input_text('genaf-adminl2', '2nd Level', value = location.level2 or '')}
    ${input_text('genaf-adminl3', '3rd Level', value = location.level3 or '')}
    ${input_text('genaf-adminl4', '4th Level', value = location.level4 or '')}
    ${input_text('genaf-latitude', 'Latitude', value = location.latitude or '')}
    ${input_text('genaf-longitude', 'Longitude', value = location.longitude or '')}
    ${input_text('genaf-altitude', 'Altitude', value = location.altitude or '')}
    ${submit_bar()}
  </fieldset>
</form>
</%def>

##
<%def name="edit_location_js(location)">
    $.each( ['#genaf-country', '#genaf-state', '#genaf-region', '#genaf-town'], function(idx, val) {
        $(val).typeahead( {
            source: function( query, process ){
                return $.get("${request.route_url('genaf.location-lookup')}", { q: query, field: 1 }, function(data) {
                    return process(data);
                });
            },
            minLength: 3
        });
    })
</%def>

##
##
<%def name="show_location(location)">
</%def>

