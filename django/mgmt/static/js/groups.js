
function groups_handler(response) {
    // Reformat
    var group_detail_root = window.location.href.replace("/mgmt/groups", "/mgmt/group/");
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm action-button' href=" + group_detail_root + response[idx] + ">";
        actions_str += "<span class='glyphicon glyphicon-pencil' aria-hidden='true'></span>  Details</a>";
        actions_str += "<a type='button' class='btn btn-danger btn-sm action-button' href='javascript:void(0);' onclick='delete_group(\"" + API_ROOT + "groups/" + response[idx] + "\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Delete</a>";
        output.push({"name": response[idx], "actions": actions_str})
    }

    return output;
}


function group_user_formatter(response) {
    // Reformat
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-danger btn-sm action-button' href='" + window.location.href + "?rem_perms=" + response[idx]["group"] + "'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span>  Remove Permission Set</a>";
        response[idx]["actions"] = actions_str
    }

    return response;
}

function get_groups(params) {
    $.ajax({
        url: API_ROOT + "groups",
        type: "GET",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8"
        },
        cache: false,
        statusCode: {
            200: function (response) {
                params.success(response.groups)
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

function delete_group(url){
    delete_api_call(url, "#group_table", "Your group has been deleted")
}