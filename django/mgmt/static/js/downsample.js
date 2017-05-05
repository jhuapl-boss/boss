
function set_status_str(val){
    // Set the status label and color
    var ds_label = $("#downsample_status");
    remove_label_styles(ds_label);
    if (val == "NOT_DOWNSAMPLED") {
        status = "Not Downsampled";
        ds_label.addClass('label-default');
    } else if (val == "IN_PROGRESS") {
        status = "In Progress";
        ds_label.addClass('label-info');
    } else if (val == "DOWNSAMPLED") {
        status = "Downsampled";
        ds_label.addClass('label-success');
    } else if (val == "FAILED") {
        status = "Failed";
        ds_label.addClass('label-danger');
    }

    ds_label.text(status);
}

function remove_label_styles(object) {
    object.removeClass('label-default');
    object.removeClass('label-primary');
    object.removeClass('label-success');
    object.removeClass('label-info');
    object.removeClass('label-warning');
    object.removeClass('label-danger');
}

function set_button_modes(val) {
    // Method to update the button disabled states
    if (val == "NOT_DOWNSAMPLED") {
        $("#downsample-btn").removeClass('disabled');
        $("#cancel-btn").addClass('disabled');
    } else if (val == "IN_PROGRESS") {
        // Uploading
        $("#downsample-btn").addClass('disabled');
        $("#cancel-btn").removeClass('disabled');
    } else if (val == "DOWNSAMPLED") {
        // Complete
        $("#downsample-btn").addClass('disabled');
        $("#cancel-btn").addClass('disabled');
    } else {
        // Failed
        $("#downsample-btn").removeClass('disabled');
        $("#cancel-btn").addClass('disabled');
    }
}

function get_downsample_status() {
    // Use generic methods for Bootstrap tables, since no params needed, set to empty dict
    var params = {};
    var resources = get_resource_names();
    get_api_call(API_ROOT + "downsample/" + resources[0] + "/" + resources[1]+ "/" + resources[2], params, get_downsample_callback);
}

function get_downsample_callback(params, response){
    // Update Status
    set_status_str(response['status']);

    // Update Button State
    set_button_modes(response['status'])
}

function downsample_ajax(collection, experiment, channel, type){
    $.ajax({
        url: API_ROOT + "downsample/" + collection + "/" + experiment + "/" + channel,
        type: type,
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8",
            "X-CSRFToken": get_csrf_token()
        },
        cache: false,
        statusCode: {
            201: function (response) {
                // Good to go. refresh dumping any prior form posts
                swal({text: 'Please wait...',
                      type: "info",
                      showConfirmButton: false,
                      timer: 5000,
                      onClose:function() {
                            window.location = window.location.protocol +'//'+ window.location.host + window.location.pathname
                        }
                    })
            },
            204: function (response) {
                // Good to go. refresh dumping any prior form posts
                swal({text: 'Please wait...',
                      type: "info",
                      showConfirmButton: false,
                      timer: 5000,
                      onClose:function() {
                            window.location = window.location.protocol +'//'+ window.location.host + window.location.pathname
                        }
                    })
            },
            404: function (response) {
                raise_ajax_error(response);
                $("#downsample-btn").removeClass('disabled');
            },
            400: function (response) {
                raise_ajax_error(response);
                $("#downsample-btn").removeClass('disabled');
            },
            403: function (response) {
                raise_ajax_error(response);
                $("#downsample-btn").removeClass('disabled');
            },
            500: function (response) {
                raise_ajax_error(response);
                $("#downsample-btn").removeClass('disabled');
            }
        }
    });
}


function start_downsample(collection, experiment, channel){
    $("#downsample-btn").addClass('disabled');
    downsample_ajax(collection, experiment, channel, "POST")

}

function cancel_downsample(collection, experiment, channel){
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
        downsample_ajax(collection, experiment, channel, "DELETE")
    });
    $("#cancel-btn").removeClass('disabled');
}
