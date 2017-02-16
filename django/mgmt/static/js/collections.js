
function collection_handler(response) {
    // Reformat
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + window.location.href + "/" + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='delete_resource(\"" + API_ROOT + "collection/" + response[idx] + "\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output;
}
function coord_handler(response) {
    // Reformat
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + API_ROOT + "mgmt/coord/" + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='delete_resource(\"" + API_ROOT + "coord/" + response[idx] + "\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output;
}

function experiment_handler(response) {
    // Reformat
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + window.location.href + "/experiment/" + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='delete_resource(\"" + API_ROOT + "experiment/" + response[idx] + "\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output;
}

function get_collections(params) {
    $.ajax({
        url: API_ROOT + "collection",
        type: "GET",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8"
        },
        cache: false,
        statusCode: {
            200: function (response) {
                params.success(response.collections)
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

function get_experiments(params) {
    // Generate API url
    var collection_name = window.location.pathname.substring(window.location.pathname.lastIndexOf("/") + 1, window.location.pathname.length);
    $.ajax({
        url: API_ROOT + "collection/" + collection_name,
        type: "GET",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8"
        },
        cache: false,
        statusCode: {
            200: function (response) {
                params.success(response.experiments)
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

function get_coords(params) {
    $.ajax({
        url: API_ROOT + "coord",
        type: "GET",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8"
        },
        cache: false,
        statusCode: {
            200: function (response) {
                params.success(response.coords)
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

