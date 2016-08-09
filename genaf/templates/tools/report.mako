<%inherit file="rhombus:templates/base.mako" />

%if path_qs:
    <a href="${path_qs}" class="btn btn-info">Resubmit analysis</a>
%endif

<h3>${header_text}</h3>

<div class='row'><div class='col-md-10'>
<h4>Filtering Summary</h4>

${sample_report}
${marker_report}

</div></div>

<div class='row'><div class='col-md-12'>

${html}

</div></div>

% if refs:
<div class='row'><div class='col-md-12'>
<p>References:</p>
${refs or '' | n}
</div></div>
% endif
##
##
<%def name="jscode()">
${code | n}
</%def>
