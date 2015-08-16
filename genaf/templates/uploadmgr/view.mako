<%inherit file="rhombus:templates/base.mako" />

<h2>FSA Bulk Upload Manager</h2>

<p>Batch: ${batch.code}</p>



<div id="dataupload_form" class='col-md-12'>
<p>Please upload archived file (zip, tgz, tar.gz) containing FSA files</p>
    <span class="btn btn-info fileinput-button">
        <span>Select files...</span>
        <!-- The file input field used as target for the file upload widget -->
        <input id="dataupload" type="file" name="files[]">
    </span>
    <br>
    <br>
    <!-- The global progress bar -->
    <div id="dataprogress" class="progress col-sm-6">
        <div class="progress-bar progress-bar-success"></div>
    </div>
</div>
<div id="dataupload_panel" class='col-md-12'>
    <div id="dataupload_filecheck">
    </div>
    <p> <span class="btn btn-info" onclick="_datafile=false; check_files();">Change file</span>
        or 
        <span class="btn btn-info" id="verifydatafile">Verify file</span></p>
    <div id="verifydatafile_report">
    </div>
</div>


<div id="infoupload_form" class='col-md-12'>
<p>Please upload assay info file (in tab-delimited or CSV format)</p>
    <span class="btn btn-info fileinput-button">
        <span>Select files...</span>
        <!-- The file input field used as target for the file upload widget -->
        <input id="infoupload" type="file" name="files[]">
    </span>
    <br>
    <br>
    <!-- The global progress bar -->
    <div id="infoprogress" class="progress col-sm-6">
        <div class="progress-bar progress-bar-success"></div>
    </div>
    <br>
</div>
<div id="infoupload_panel" class='col-md-12'>
    <div id="infoupload_filecheck">
    </div>
    <div id="verifyinfofile_report">
    </div>
    <p><span class="btn btn-info" onclick="_infofile=false; check_files();">Change file</span> or <span class="btn btn-info" id="verifyinfofile">Verify file</span></p>
</div>


<div id="verify">
  <p><a href="${request.route_url('genaf.uploadmgr-save', id=sesskey)}">
        <span class="btn btn-info" id="commitpayload2">Proceed</span></a></p>
  <div id="commitpayload_report">
  </div>
</div>



##
##
<%def name="stylelink()">
    <link href="${request.static_url('genaf:static/jquery.fileupload/css/jquery.fileupload.css')}" rel="stylesheet" />
</%def>
##
##
<%def name="jslink()">
    <script src="${request.static_url('genaf:static/jquery.fileupload/js/vendor/jquery.ui.widget.js')}"></script>

    <script src="${request.static_url('genaf:static/jquery.fileupload/js/jquery.fileupload.js')}"></script>
</%def>
##
##
<%def name="jscode()">

var _datafile = null;
var _infofile = "${meta['infofile'] if 'infofile' in meta and meta['infofile'] else ''}";
check_datafile();
check_infofile();
check_files();

$(function () {
    'use strict';

    $('#dataupload').fileupload({
        url: '${request.route_url("genaf.uploadmgr-uploaddata", id = sesskey)}',
        dataType: 'json',
        maxChunkSize: 1000000,
        done: function (e, data) {
            check_datafile();
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#dataprogress .progress-bar').css(
                'width',
                progress + '%'
            );
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');

    $('#infoupload').fileupload({
        url: '${request.route_url("genaf.uploadmgr-uploadinfo", id = sesskey)}',
        dataType: 'json',
        maxChunkSize: 1000000,
        done: function (e, data) {
            check_infofile();
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#infoprogress .progress-bar').css(
                'width',
                progress + '%'
            );
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');


    $('#verifydatafile').click( function() {
        $.getJSON( "${request.route_url('genaf.uploadmgr-verifydatafile', id=sesskey)}",
                    function(data) {
            if (data) {
                $('#verifydatafile_report').html( data.html );
            }
        });

        return false;
    });


    $('#verifyinfofile').click( function() {
        $.getJSON( "${request.route_url('genaf.uploadmgr-verifyinfofile', id=sesskey)}",
                    function(data) {
            if (data) {
                $('#verifyinfofile_report').html( data.html );
            }
        });

        return false;
    });

    $('#commitpayload').click( function() {
        $.getJSON( "${request.route_url('genaf.uploadmgr-commitpayload', id=sesskey)}",
                    function(data) {
            if (data) {
                $('#commitpayload_report').html( data.html );
            }
        });

        return false;
    });



});


function check_files() {
    if (_datafile) {
        $('#dataupload_form').hide();
        $('#dataupload_panel').show();
    } else {
        $('#dataupload_form').show();
        $('#dataprogress .progress-bar').css('width','0%');
        $('#dataupload_panel').hide();
    }

    if (_infofile) {
        $('#infoupload_form').hide();
        $('#infoupload_panel').show();
    } else {
        $('#infoupload_form').show();
        $('#dataprogress .progress-bar').css('width','0%');
        $('#infoupload_panel').hide();
    }

    if (_datafile && _infofile ) {
        $('#verify').show();
    } else {
        $('#verify').hide();
    }
}


function check_datafile() {
    // check whether we already have the payload file
    $.getJSON( "${request.route_url('genaf.uploadmgr-checkdatafile', id=sesskey)}", function(data) {
        if (data) {
            _datafile = true;
            $('#dataupload_filecheck').html( data.html );
            check_files();
        }
    });
}


function check_infofile() {
    // check whether we already have the payload file
    $.getJSON( "${request.route_url('genaf.uploadmgr-checkinfofile', id=sesskey)}", function(data) {
        if (data) {
            _infofile = true;
            $('#infoupload_filecheck').html( data.html );
            check_files();
        }
    });
}


</%def>
