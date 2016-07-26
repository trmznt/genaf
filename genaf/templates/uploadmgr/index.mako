<%inherit file="rhombus:templates/base.mako" />

<h2>Current Pending Upload Session</h2>

<p>Batch: ${batch.code}</p>

<table class="table table-condensed table-striped">
<thead>
    <tr>
        <th>Session ID</th><th>Created by</th><th>Created at</th><th>Last modified at</th>
    </tr>
</thead>
<tbody>
% for sess in sessions:
    <tr>
        <td><a href="${request.route_url('genaf.uploadmgr-view', id=sess.sesskey)}">${sess.sesskey}</a></td>
        <td>${sess.meta['user']}</td>
        <td>${sess.ctime.strftime("%A, %d %B %Y %I:%M%p")}</td>
        <td>${sess.mtime.strftime("%A, %d %B %Y %I:%M%p")}</td>
    </tr>
% endfor
</tbody>
</table>
