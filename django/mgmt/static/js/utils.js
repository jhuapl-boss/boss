function raise_ajax_error(response) {
    if(typeof response.responseJSON !== "undefined")
    {
        swal('Uh Oh.',
            'Something went wrong - ' + response.responseJSON["detail"],
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

function mgmt_path_root() {
    return window.location.protocol + "//" + window.location.hostname + window.location.pathname
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
        var actions_str = "<a type='button' class='btn btn-danger btn-sm action-button' href='" + mgmt_path_root() + "?rem_perms=" + response[idx]["group"] + "'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Remove Permission Set</a>";
        response[idx]["actions"] = actions_str
    }

    return response;
}