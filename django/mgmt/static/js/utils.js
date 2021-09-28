function raise_ajax_error(response) {
    if(typeof response.responseJSON !== "undefined")
    {
        if ("detail" in response.responseJSON){
            var err_msg = response.responseJSON["detail"]
        } else{
            var err_msg = response.responseJSON["message"]
        }
        swal('Uh Oh.',
            'Something went wrong - ' + err_msg,
            'error'
        )
    }else{
        swal('Uh Oh.',
            'Something went wrong...',
            'error'
        )
    }
}

function get_csrf_token() {
    var csrf = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var idx in cookies) {
            var cookie = jQuery.trim(cookies[idx]);
            if (cookie.substring(0, 10) == ('csrftoken=')) {
                csrf = decodeURIComponent(cookie.substring(10));
                break;
            }
        }
    }
    return csrf;
}

function delete_api_call(url, table_id, confirm_message) {
    swal({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        type: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#18BC9C',
        cancelButtonColor: '#E74C3C',
        confirmButtonText: 'Yes, delete it!'
    }).then(function () {
        $.ajax({
            url: url,
            type: "DELETE",
            headers: {
                "Accept": "application/json; charset=utf-8",
                "Content-Type": "application/json; charset=utf-8",
                "X-CSRFToken": get_csrf_token()
            },
            cache: false,
            statusCode: {
                204: function (response) {
                    $(table_id).bootstrapTable('refresh');
                    swal({
                        title: 'Success',
                        text: confirm_message,
                        type: 'success',
                        confirmButtonColor: '#3498DB',
                        confirmButtonText: 'Got it.',
                        timer: 3000
                    })
                },
                404: function (response) {
                    raise_ajax_error(response)
                },
                400: function (response) {
                    raise_ajax_error(response)
                },
                403: function (response) {
                    raise_ajax_error(response)
                },
                500: function (response) {
                    raise_ajax_error(response)
                }
            }
        });

    });
}

function get_api_call(url, params, callback) {
    // Generic method to make API calls for the bootstrap table plugin
    // url is the API url to call.
    // params is the bootstrap table params instance
    // callback is a method to complete setting up the bootstrap table plugin.
    $.ajax({
        url: url,
        type: "GET",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8"
        },
        cache: false,
        statusCode: {
            200: function (response) {
                callback(params, response);
            },
            404: function (response) {
                raise_ajax_error(response)
            },
            400: function (response) {
                raise_ajax_error(response)
            },
            403: function (response) {
                raise_ajax_error(response)
            },
            500: function (response) {
                raise_ajax_error(response)
            }
        }
        });
}

function show_meta_detail(url) {
    $.ajax({
        url: url,
        type: "GET",
        headers: {
            "Accept": "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8",
            "X-CSRFToken": get_csrf_token()
        },
        cache: false,
        statusCode: {
            200: function (response) {
                // Set values
                $("#metadataKey").val(response.key);
                $("#metadataValue").val(response.value);

                // Show modal
                $('#metadataModal').modal('show')
            },
            404: function (response) {
                raise_ajax_error(response)
            },
            400: function (response) {
                raise_ajax_error(response)
            },
            403: function (response) {
                raise_ajax_error(response)
            },
            500: function (response) {
                raise_ajax_error(response)
            }
        }
    });
}

function get_resource_names(){
    var result = [];
    var parts = window.location.pathname.split("/");
    while (parts.length > 0) {
        var part = parts.pop();
        if (part == "resources"){
            break
        }

        result.unshift(part)
    }
    return result
}

function permission_formatter(response) {
    // Reformat
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-danger btn-sm action-button' href='" + window.location.href + "?rem_perms=" + response[idx]["group"] + "'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Remove Permission Set</a>";
        response[idx]["actions"] = actions_str
    }

    return response;
}

function resource_formatter(response, detail_base_url, delete_function, delete_base_url, is_admin) {
    // Base formatter for all resource bootstrap table plugins
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + detail_base_url + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        if (is_admin){
            actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='" + delete_function + "(\"" + delete_base_url + response[idx] + "\")'>";
            actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        }
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output
}

function channel_resource_formatter(response, detail_base_url, delete_function, delete_base_url, neuroglancer_url, is_admin) {
    // Base formatter for channel resource bottstrap table plugin
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + detail_base_url + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        actions_str += "<a type='button' class='btn btn-default btn-sm action-button' href=" + neuroglancer_url + response[idx] +  "','name':'" + response[idx] + "'}}}" + ">";
        actions_str += "<span class='glyphicon' aria-hidden='true'></span>  Neuroglancer</a>";
        if (is_admin){
            actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='" + delete_function + "(\"" + delete_base_url + response[idx] + "\")'>";
            actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        }
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output
}

function metadata_handler(response) {
    // Format handler for all metadata bootstrap table plugins
    var output = [];
    var meta_pathname = window.location.pathname.replace("/mgmt/resources", "/mgmt/meta");
    var meta_root = window.location.protocol + "//" + window.location.hostname + meta_pathname;

    var resource_path = window.location.pathname.split("/mgmt/resources")[1];

    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href='javascript:void(0);' onclick='show_meta_detail(\"" + API_ROOT + "meta" + resource_path + "?key=" + response[idx] +"\")'>";
        actions_str += "<span class='glyphicon glyphicon-eye-open' aria-hidden='true'></span>  View</a>";
        actions_str += "<a type='button' class='btn btn-default btn-sm action-button' href=" + meta_root + "?key=" + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Update</a>";
        actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='delete_metadata(\"" + API_ROOT + "meta" + resource_path + "?key=" + response[idx] +"\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        output.push({"key": response[idx], "actions": actions_str})
    }

    return output;
}
