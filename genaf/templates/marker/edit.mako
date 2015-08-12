<%inherit file="rhombus:templates/base.mako" />
<%namespace file="genaf:templates/marker/functions.mako" import="edit_marker" />

<h3>${h.link_to('Marker', request.route_url('genaf.marker'))}: ${marker.code}</h3>

${form}


