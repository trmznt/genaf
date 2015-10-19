<%inherit file="rhombus:templates/base.mako" />

<h2>Assays</h2>

<table id="assay_table"></table>
##
##
<%def name="jslink()">
<script src="${request.static_url('genaf:static/datatables/datatables.min.js')}"></script>
</%def>
##
<%def name="jscode()">
var data = ${data | n};

$(document).ready(function() {
    $('#assay_table').DataTable( {
        data: dataSet,
        columns: [
            { title: "Name" },
            { title: "Position" },
            { title: "Office" },
            { title: "Extn." },
            { title: "Start date" },
            { title: "Salary" }
        ]
    } );
} );
</%def>
