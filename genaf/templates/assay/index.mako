<%inherit file="rhombus:templates/base.mako" />

<h2>Assays</h2>

<table id="assay_table" class='table table-condensed table-striped'></table>

##
##
<%def name="stylelink()">
  <link href="${request.static_url('genaf:static/datatables/datatables.min.css')}" rel="stylesheet" />  
</%def>
##
##
<%def name="jslink()">
<script src="${request.static_url('genaf:static/datatables/datatables.min.js')}"></script>
</%def>
##
<%def name="jscode()">
var dataset = ${dataset | n};

$(document).ready(function() {
    $('#assay_table').DataTable( {
        data: dataset,
        paging: false,
        fixedHeader: true,
        columns: [
            { title: "FSA Filename" },
            { title: "Sample Code" },
            { title: "Panel" },
            { title: "Score" },
            { title: "RSS" },
            { title: "Proctime (ms)" }
        ]
    } );
} );
</%def>
