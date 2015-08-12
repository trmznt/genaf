<%inherit file='rhombus:templates/base.mako' />

<h3>Uploading Report</h3>

<p>Your sample data has been successfully uploaded, with the following log:</p>

<p>${msg}</p>

<a href="${request.route_url('genaf.batch-view', id = batch.id)}"><button>Continue</button></a>
