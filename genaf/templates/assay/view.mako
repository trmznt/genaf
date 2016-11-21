<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/assay/functions.mako" import="show_assay, show_assay_js" />
<%namespace file="genaf:templates/channel/functions.mako" import="list_channels" />
<%namespace file="genaf:templates/allele/functions.mako" import="list_alleles" />

<%namespace file="rhombus:templates/common/form.mako" import="input_text, input_hidden, input_textarea, checkboxes, submit_bar, input_show, textarea_show, button_edit, selection_ek" />

<%!
from rhombus.lib.roles import GUEST
%>

## input: assay, lsp (ladder_scanning_parameter)

<h2>FSA Viewer</h2>

<div class='row'>
<div class='col-md-8'>
  ${assay_info}
</div>
<div class='col-md-4'>
  ${list_channels(assay.channels)}
</div>
</div><!-- row -->

% if not request.user.has_roles(GUEST):
<div class='row'>
<div class='col-md-8'>
${h.link_to( 'Process FSA', request.route_url('genaf.assay-action', _query=dict(_method='process_fsa', id=assay.id)), class_='btn btn-success', ** { 'data-toggle':'modal', 'data-target':'#allele-modal-view', 'data-remote': 'false' } )}
</div>
</div>
% endif

##<div class='row'>
##<form method='POST' action='/assay/@@action'>
##<input type="hidden" name='assay_id' value="${assay.id}" />
##<a role='button' data-target='#ladder_peak_params' href='#ladder_peak_params' class='btn' data-toggle='modal'>Find ladder peaks</a>
##<button name='_method' value='estimate_z'>Estimate Z</button>
##<button name='_method' value='find_peaks'>Find peaks</button>
##</form>

##<div id='ladder_peak_params' class="modal hide" role="dialog">
##<div class='modal-body'>

##<h3>Ladder Peaks Search Parameter</h3>
##<form method='POST' action='/assay/@@action'>
##${input_hidden('assay_id', value = assay.id)}
##${input_text('min_height', 'Minimum Height', value = lsp.min_height)}
##${input_text('relative_min', 'Min relative from median height', value = lsp.min_relative_ratio)}
##${input_text('relative_max', 'Max relative from median height', value = lsp.max_relative_ratio)}
##${submit_bar('Find ladder peaks', 'find_ladder_peaks')}

##</form>
##</div>
##</div>

##<div id='peak_params' class="modal hide" role="dialog">
##<div class='modal-body'>

##<h3>Peaks Search Parameter</h3>
##<form method='POST' action='/assay/@@action'>
##${input_hidden('assay_id', value = assay.id)}
##${input_text('min_height', 'Minimum Height', value = 30)}
##${input_text('relative_min', 'Min relative from median height', value = 0.50)}
##${input_text('relative_max', 'Max relative from median height', value = 4)}
##${submit_bar('Find ladder peaks', 'find_ladder_peaks')}

##</form>
##</div>
##</div>


##</div><!-- row -->


<div class='row'>
  <div class='col-md-10'>
    <div id="placeholder" style="width:800px;height:400px;"></div>
  </div>
  <div class='col-md-2'>
    <p id="choices">Show:</p>
  </div>
</div>

<div class='row'>
<div id="allele-modal-view" class="modal" role="dialog" tabindex="-1"  aria-labelledby="myModalLabel" aria-hidden="true">
  <div class='modal-dialog'>
    <div class='modal-content'>
      <div class='modal-body'>
      </div>
    </div>
  </div>
</div>
</div>

<br />
${allele_table}

% if False:

<br/>
<nav id="navbar-alleles" class="navbar navbar-default navbar-static">
  <ul class="nav navbar-nav">
  % for c in assay.channels:
    <li><a href="#M-${c.dye}">${c.dye} / ${c.marker.code}</a></li>
  % endfor
  </ul>
</nav>

<div class='row' style="height:300px;overflow-y:auto;position-relative;" data-spy="scroll" data-target="#navbar-alleles" >

<div class='col-md-12'>
% for c in assay.channels:
  <p id="M-${c.dye}"><b>${c.dye} / ${c.marker.code}</b></p>
    % if c.allelesets.count() >= 1:
        ${list_alleles(sorted(c.get_latest_alleleset().alleles, key=lambda x: x.rtime))}
    % endif
  <br />
% endfor
</div>
</div><!-- row -->

% endif
##
##
<%def name="jscode()">
  ${show_assay_js(assay)}
  $('#allele-modal-view').on('hidden.bs.modal', function() {
      $(this).find('.modal-body').empty();
    }
  );
  $('#allele-modal-view').on("show.bs.modal", function(e) {
    var link = $(e.relatedTarget);
    $(this).find(".modal-body").load(link.attr("href"));
  });

  ${code | n}
</%def>
##
<%def name="jslink()">
<script src="${request.static_url('genaf:static/js/jquery.stickytableheaders.min.js')}"></script>
<script src="${request.static_url('genaf:static/flot/jquery.flot.js')}"></script>
<script src="${request.static_url('genaf:static/flot/jquery.flot.selection.js')}"></script>
<script src="/assay/${assay.id}@@drawchannels" type="text/javascript"></script>
</%def>
