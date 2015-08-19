<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/batch/functions.mako" import="show_batch" />
<%namespace file="rhombus:templates/common/form.mako" import="input_file, input_hidden, submit_bar" />

<h2>Batch</h2>

<div class='row'><div class='col-md-6'>
  ${show_batch(batch)}
</div></div>

<div class='row'>
<div class='col-md-6'>

  <h4>Samples</h4>

  <div class='row'>
    <div class='col-sm-12'>
      <p><a href="${request.route_url('genaf.sample', _query = dict(batch_id=batch.id))}"><span class="btn btn-info">Browse samples</span></a></p>
      <p><button class="btn btn-info">Add new sample</button></p>
    </div>
  </div>

  <div class='row'>
    <div class='col-sm-12'>
        <hr />
        <p>Use the form below if you want to add multiple sample data from
            a single tab-delimited or csv file.</p>
    </div>
  </div>

  <div class='row'><div class='col-sm-12'>
    <form class="form form-horizontal" action='${request.route_url("genaf.batch-action")}'
            method='POST' enctype="multipart/form-data">
      <fieldset>
        ${input_hidden(name='batch_id', value=batch.id)}
        ${input_file('sampleinfo_file', "Sample info file")}
        ${submit_bar('Upload', 'add-sample-info')}
      </fieldset>
    </form>
  </div></div>


</div>
<div class='col-md-6'>
  
  <h4>FSA Bulk Uploading</h4>
  <p>Use the form below for uploading a zip or tgz file containing multiple FSA files.</p>
  <div class='row'><div class='col-sm-12'>
    <a href="${request.route_url('genaf.batch-action',
        _query = dict( batch_id = batch.id, _method = 'new-assay-upload-session'))}">
        <button>Start upload session</button></a>
    <br />
    <a href="${request.route_url('genaf.batch-action',
        _query = dict( batch_id = batch.id, _method = 'list-assay-upload-session'))}">
        <button>List pending sessions</button></a>
    
  </div></div>

</div>
<div class='col-md-6'>

  <h4>FSA Processing</h4>
  <a href="${request.route_url('genaf.famgr-view', id=batch.id)}">
    <button>Start FSA Process Session</button>
  </a>
  </ul>

</div>
</div>

##
<%def name="jscode()">

  ## single-click file submission
  $('#add-sample-info').upload( { 
    name: 'sampleinfo_file',
    action: '${request.route_url("genaf.batch-action")}',
    params: { _method: 'add-sample-info', batch_id: '${batch.id}' },
    onComplete: function (response) {
        var resp = jQuery.parseJSON( response );
        window.location.replace( resp['url'] );
      }
    }
  );


</%def>
