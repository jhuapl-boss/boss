
function collection_handler(response) {
    console.log("in handler");
    console.log(response);
    // Reformat
    var output = [];
    for (var idx in response) {
        var actions_str = "<a type='button' class='btn btn-default btn-sm' href='javascript:void(0);' onclick='delete_collection(\"" + response[idx] + "\")'>";
        actions_str += "<span class='glyphicon glyphicon-remove' aria-hidden='true'></span> Delete</a>";
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
                console.log("itworked!");
                console.log(response);
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

function delete_collection(collection) {
    $.ajax({
        url: API_ROOT + "collection/" + collection,
        type: "DELETE",
        headers: {
            "Accept" : "application/json; charset=utf-8",
            "Content-Type": "application/json; charset=utf-8",
            "X-CSRFToken": get_csrf_token()
        },
        cache: false,
        statusCode: {
            204: function (response) {
                console.log("itworked!");
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
