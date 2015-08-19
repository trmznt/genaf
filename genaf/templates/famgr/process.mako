<%inherit file="rhombus:templates/base.mako" />

<h3>Assay Processing Progress</h3>

<p>Batch code: ${batch_code}</p>

<div>
  ${msg}
</div>

<div id="refresh_status"></div>


##
##
<%def name="jscode()">
 
var secs;
var timerID = null;
var timerRunning = false;
var delay = 1000;
 
function InitializeTimer(seconds) {
    // Set the length of the timer, in seconds
    secs = seconds;
    $("#refresh_status").html(
        "<p>This page will refresh in <span id='second_label'>10</span> seconds</p>");
    StopTheClock();
    StartTheTimer();
}
 
function StopTheClock() {
    if (timerRunning)
        clearTimeout(timerID);
    timerRunning = false;
}
 
function StartTheTimer() {
    if (secs == 0) {
        StopTheClock();
        // Here's where you put something useful that's
        // supposed to happen after the allotted time.
        // For example, you could display a message:
        location.reload(true);

    }
    else {
        $("#second_label").text(secs);
        secs = secs - 1;
        timerRunning = true;
        timerID = self.setTimeout("StartTheTimer()", delay);
    }
}

$(function() {
    'use strict';

    if (${seconds}) {
        InitializeTimer(${seconds});
    }
});

</%def>
