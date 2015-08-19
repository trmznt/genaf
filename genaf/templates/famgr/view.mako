<%inherit file="rhombus:templates/base.mako" />

<h3>Fragment Analysis Manager</h3>

<p>Batch code: <a href="${request.route_url('genaf.batch-view', id = batch.id)}">${batch.code}</a></p>

${content}



