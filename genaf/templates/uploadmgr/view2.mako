<%inherit file="rhombus:templates/base.mako" />

<h3>FSA Bulk Upload Manager</h3>

<p>Batch: <a href="${request.route_url('genaf.batch-view', id=batch.id)}">${batch.code}</a></p>


<div id='mainpanel' class='col-md-12'>
</div>

<!-- global progressbar -->
<div id='fileprogress' class='progress progressbar-container' style='display:none'>
  <div class='progress-bar progress-bar-success'></div>
</div>

##
##
<%def name="stylelink()">
    <link href="${request.static_url('genaf:static/jquery.fileupload/css/jquery.fileupload.css')}" rel="stylesheet" />
    <style>
.progressbar-container {
    position: fixed;
    top: 50%;
    left: 50%;
    margin-left: -200px; /* half width of the spinner gif */
    margin-top: -5px; /* half height of the spinner gif */
    text-align:center;
    z-index:1234;
    overflow: auto;
    width: 400px; /* width of the spinner gif */
    height: 10px; /*hight of the spinner gif +2px to fix IE8 issue */
}
    </style>
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

$(function () {
    'use strict';

    get_main_panel();

});

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
