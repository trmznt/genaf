<%inherit file="rhombus:templates/base.mako" />
<%namespace file='genaf:templates/location/functions.mako' import='show_location' />

<h2>Location</h2>

${show_location(location)}
