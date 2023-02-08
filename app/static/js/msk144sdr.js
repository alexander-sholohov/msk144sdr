/**
 * @file   msk144sdr.js
 * @author Alexander Sholokhov <ra9yer(at)yahoo.com>
 * @date   Mon Feb 06 2023
 */

// Source code available at https://github.com/alexander-sholohov/msk144sdr


var last_launch_id = -1;
var spot_last_record_id = 0;
var wf_last_record_id = 0;

var start_stamp = (new Date()).getTime();
var session_timeout_in_seconds = 120 * 60; // 120 minutes


function fetch_spots() {
    var xmlHttp;
    try { xmlHttp = new XMLHttpRequest(); }
    catch (e) {
        try { xmlHttp = new ActiveXObject("Msxml2.XMLHTTP"); }
        catch (e) {
            try { xmlHttp = new ActiveXObject("Microsoft.XMLHTTP"); }
            catch (e) { alert("Your browser does not support AJAX!"); return false; }
        }
    }
    xmlHttp.onreadystatechange = function () {
        if (xmlHttp.readyState == 4 && this.status == 200) {
            if (last_launch_id != -1 && last_launch_id != this.response.launch_id) {
                spot_last_record_id = 0; // next time reload all
                wf_last_record_id = 0;
                spots_clear_all();
                wf_clear_all();
            } else {
                spot_last_record_id = this.response.spot_last_record_id;
                wf_last_record_id = this.response.wf_last_record_id;
                spots_add_multiple_lines(this.response.spot_lines);
                wf_add_multiple_lines(this.response.wf_lines);
            }
            last_launch_id = this.response.launch_id;
        }
    }
    xmlHttp.responseType = 'json';
    xmlHttp.timeout = 2000; // in ms
    var url = "get_update?spot_record_id=" + spot_last_record_id + "&wf_record_id=" + wf_last_record_id;
    xmlHttp.open("GET", url, true);
    xmlHttp.setRequestHeader("Cache-Control", "no-cache, no-store, max-age=0");
    xmlHttp.send(null);
}

function spots_add_single_line(s) {
    var o = document.getElementById('spotsboxnew');
    if (!o) return;
    o.innerHTML += '<br>' + s + '\n';
    o.scrollTop = o.scrollHeight;
}

function spots_clear_all() {
    var o = document.getElementById('spotsboxnew');
    if (!o) return;
    o.innerHTML = "";
    o.scrollTop = o.scrollHeight;
}

function spots_add_multiple_lines(arr) {
    if (arr.length == 0) return;
    var o = document.getElementById('spotsboxnew');
    if (!o) return;
    s = "";

    arr.forEach(function (item) { s += '<br>' + item + '\n' });

    o.innerHTML += s;
    o.scrollTop = o.scrollHeight;
}

function wf_clear_all() {
    var o = document.getElementById('wfbox');
    if (!o) return;
    o.innerHTML = "";
    o.scrollTop = o.scrollHeight;
}

function wf_add_multiple_lines(arr) {
    if (arr.length == 0) return;
    var o = document.getElementById('wfbox');
    if (!o) return;
    s = "";

    arr.forEach(function (item) { s += '<div class="row_wf"><img src="' + item + '"></div>\n' });

    o.innerHTML += s;
    // o.scrollTop = o.scrollHeight;
    setTimeout(wf_scroll_down, "500");
}

function wf_scroll_down() {
    var o = document.getElementById('wfbox');
    if (!o) return;
    o.scrollTop = o.scrollHeight;
}

function tick() {
    var seconds_elapsed = ((new Date()).getTime() - start_stamp) / 1000;
    if (seconds_elapsed > session_timeout_in_seconds) {
        spots_clear_all();
        wf_clear_all();
        spots_add_single_line("Spots autoupdate has been stopped because of timeout. Please refresh the page.")
    }
    else {
        fetch_spots();
        setTimeout(tick, "3000");
    }
}

function long_tick() {
    setTimeout(long_tick, "60000");

    // spots scroll down
    var o = document.getElementById('spotsboxnew');
    if (!o) return;
    o.scrollTop = o.scrollHeight;
}

function bodyonload() {

    setTimeout(tick, "100");
    setTimeout(long_tick, "60000");
}
