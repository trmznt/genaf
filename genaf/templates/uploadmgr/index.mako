<%inherit file="rhombus:templates/base.mako" />

<h2>Current Pending Upload Session</h2>

<p>Batch: ${batch.code}</p>

<ul>
% for sess in sessions:
    <li><a href="${request.route_url('genaf.uploadmgr-view', id=sess.sesskey)}">${sess.sesskey}</a></li>
% endfor
</ul>
