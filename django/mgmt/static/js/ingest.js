
function get_status_str(val){
    var status = "Preparing";
    if (val == 1) {
        status = "Uploading";
    } else if (val == 2) {
        status = "Complete";
    } else if (val == 3) {
        status = "Deleted";
    } else if (val == 4) {
        status = "Failed";
    }
    return status
}

function set_button_modes(val) {

    if (val == 0) {
        // Preparing
        $("#complete-btn").addClass('disabled');
        $("#cancel-btn").removeClass('disabled');
    } else if (val == 1) {
        // Uploading
        $("#complete-btn").addClass('disabled');
        $("#cancel-btn").removeClass('disabled');
    } else if (val == 2) {
        // Complete
        $("#complete-btn").addClass('disabled');
        $("#cancel-btn").addClass('disabled');
    } else {
        // Canceled or Failed
        $("#complete-btn").addClass('disabled');
        $("#cancel-btn").addClass('disabled');
    }
}

function get_ingest_jobs_callback(params, response) {
    params.success(response.ingest_jobs);
}
function get_ingest_job_list(params) {
    get_api_call(API_ROOT + "ingest", params, get_ingest_jobs_callback);
}

function ingest_job_list_formatter(response) {
    // Base formatter for all resource bootstrap table plugins

    var detail_base_url = window.location.href + "/";

    var output = [];
    for (var idx in response) {

        var status = get_status_str(response[idx]["status"]);

        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + detail_base_url + response[idx]['id'] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        output.push({"id": response[idx]["id"],
                     "resource": response[idx]["collection"] + "/" + response[idx]["experiment"] + "/" + response[idx]["channel"],
                     "status": status,
                     "created": response[idx]["created_on"],
                     "actions": actions_str})
    }

    return output
}


function get_job_callback(params, response){
    // Update the UI
    $("#collection").text(response['ingest_job']["collection"]);
    $("#experiment").text(response['ingest_job']["experiment"]);
    $("#channel").text(response['ingest_job']["channel"]);
    $("#status").text(get_status_str(response["ingest_job"]["status"]));
}

function get_job_status_callback(params, response){
    // Update the UI
    $("#total_tiles").text(response["total_message_count"]);
    $("#current_tiles").text(response["current_message_count"]);
    $("#status").text(get_status_str(response["status"]));
    set_button_modes(response["status"]);

    var prog_bar = $("#progress-active");
    if (response["status"] == 0){
        // Preparing
        var val =  parseFloat(response["current_message_count"]) / parseFloat(response["total_message_count"]) * 100;
        val = val.toFixed(2);

        prog_bar.animate({width: val + "%"}, 200);
        prog_bar.attr('aria-valuenow', val);
        prog_bar.html(val + '%');

        if (val == 100) {
            $("#progress-detail").text("Please wait while queue integrity is verified.")
        } else{
            $("#progress-detail").text("Please wait while the upload task queue is populated.")
        }
    } else if (response["status"] == 1){
        // Uploading
        var val =  (parseFloat(response["total_message_count"]) - parseFloat(response["current_message_count"])) / parseFloat(response["total_message_count"]) * 100;
        val = val.toFixed(2);

        prog_bar.animate({width: val + "%"}, 200);
        prog_bar.attr('aria-valuenow', val);
        prog_bar.html(val + '%');

        if (val == 100){
            // The job is complete, stop animation and let user know to complete
            $("#complete-btn").removeClass('disabled');
            $("#complete-notify").removeClass('hidden');
            prog_bar.removeClass('active');
            prog_bar.removeClass('progress-bar-striped');
            $("#progress-detail").text("All Tiles Uploaded")
        } else{
            $("#progress-detail").text("Uploading Tiles")
        }
    } else {
        prog_bar.animate({width: "0%"}, 200);
        prog_bar.html('');
        prog_bar.removeClass('active');
        prog_bar.removeClass('progress-bar-striped');
        $("#progress-detail").text("");
        $("#complete-notify").addClass('hidden');
        // Stop the timer
        clearInterval(STATUS_TIMER);
    }
}

function get_job(id){
    get_api_call(API_ROOT + "ingest/" + id, [], get_job_callback);
}

function get_status(id){
     get_api_call(API_ROOT + "ingest/" + id + "/status", [], get_job_status_callback);
}

function complete_job(id){
    $("#complete-btn").addClass('disabled');
    $.ajax({
        url: API_ROOT + "ingest/" + id + "/complete",
        type: "POST",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8",
            "X-CSRFToken": get_csrf_token()
        },
        cache: false,
        statusCode: {
            204: function (response) {
                // Good to go
                get_status(id)
            },
            404: function (response) {
                raise_ajax_error(response);
                $("#complete-btn").removeClass('disabled');
            },
            400: function (response) {
                raise_ajax_error(response);
                $("#complete-btn").removeClass('disabled');
            },
            403: function (response) {
                raise_ajax_error(response);
                $("#complete-btn").removeClass('disabled');
            },
            500: function (response) {
                raise_ajax_error(response);
                $("#complete-btn").removeClass('disabled');
            }
        }
    });
}

function cancel_job(id){
    $("#cancel-btn").addClass('disabled');

    swal({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#18BC9C',
        cancelButtonColor: '#E74C3C',
        confirmButtonText: 'Yes, cancel it!'
    }).then(function () {
        // Stop Polling
        clearInterval(STATUS_TIMER);
        $("#status").text("Attempting To Cancel");
        $("#progress-detail").text("Cancelling Job. Please wait...");
        $("#cancel-btn").addClass('disabled');

        $.ajax({
            url: API_ROOT + "ingest/" + id,
            type: "DELETE",
            headers: {
                "Accept": "application/json; charset=utf-8",
                "Content-Type": "application/json; charset=utf-8",
                "X-CSRFToken": get_csrf_token()
            },
            cache: false,
            statusCode: {
                204: function (response) {
                    window.location = MGMT_ROOT + "/ingest";
                },
                404: function (response) {
                    raise_ajax_error(response);
                    $("#cancel-btn").removeClass('disabled');
                },
                400: function (response) {
                    raise_ajax_error(response);
                    $("#cancel-btn").removeClass('disabled');
                },
                403: function (response) {
                    raise_ajax_error(response);
                    $("#cancel-btn").removeClass('disabled');
                },
                500: function (response) {
                    raise_ajax_error(response);
                    $("#cancel-btn").removeClass('disabled');
                }
            }
        });

    });
}