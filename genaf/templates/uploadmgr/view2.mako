<%inherit file="rhombus:templates/base.mako" />

<h3>FSA Bulk Upload Manager</h3>

<p>Batch: <a href="${request.route_url('genaf.batch-view', id=batch.id)}">${batch.code}</a> | Started by: ${meta['user']} | Started at: ${meta['ctime']} | Last modified at: ${meta['mtime']}</p>


<div id='mainpanel' class='col-md-12'>
</div>

<!-- global progressbar -->
<div id='fileprogress' class='progress progressbar-container' style='display:none'>
  <div class='progress-bar progress-bar-success'></div>
</div>

<!-- spinner -->
<div id='spinner' class='spinner' style='display:none;'>
  <!-- <img id='img-spinner' src="${request.static_url('genaf:static/spinner.gif')}" alt='Loading...' /> -->
  <div class="loading"></div>
</div>

<div id='screen'>
</div>

##
##
<%def name="stylelink()">
    <link href="${request.static_url('genaf:static/jquery.fileupload/css/jquery.fileupload.css')}" rel="stylesheet" />
    <link href="${request.static_url('genaf:static/spinner.css')}" rel="stylesheet" />
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

var _fileop = false;

$(function () {
    'use strict';

    $(document)
    .ajaxStart(function() { show_spinner(); } )
    .ajaxStop(function() { hide_spinner(); });

    $(window).resize( function() {
        $('#spinner').css('display') == 'block' ? show_spinner() : '';
    });

    get_main_panel();
    show_spinner();

});

function show_spinner() {
    $('#screen').css({  "display": "block", opacity: 0.8, "width":$(document).width(),"height":$(document).height()});
    $('#spinner').show();
}

function hide_spinner() {
    $('#spinner').hide();
    $('#screen').hide();
}
    
function hide_spinne() {
    
}

function get_main_panel() {
    $.getJSON( "${request.route_url('genaf.uploadmgr-mainpanel', id=sesskey)}",
        function(data) {
            show_main_panel( data );
        }
    );
}

function show_main_panel( data ) {
    if (data) {
        if (data.html) {
            $('#mainpanel').html( data.html );
        }
        if (data.code) {
            jQuery.globalEval( data.code );
        }
    }
}

</%def>
