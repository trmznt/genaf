<%inherit file="rhombus:templates/base.mako" />

<h3>FSA Bulk Upload Manager</h3>

<p>Batch: <a href="${request.route_url('genaf.batch-view', id=batch.id)}">${batch.code}</a></p>


<div id='mainpanel' class='col-md-12'>
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

$(function () {
    'use strict';

    get_main_panel();

});

function get_main_panel() {
    $.getJSON( "${request.route_url('genaf.uploadmgr-mainpanel', id=sesskey)}",
        function(data) {
            if (data) {
                if (data.html) {
                    $('#mainpanel').html( data.html );
                }
                if (data.code) {
                    jQuery.globalEval( data.code );
                }
            }
        }
    );
}

</%def>
