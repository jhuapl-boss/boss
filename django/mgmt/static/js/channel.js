function get_metadata_callback(params, response) {
    params.success(response.keys)
}
function get_metadata(params) {
    var resources = get_resource_names();
    get_api_call(API_ROOT + "meta/" + resources[0] + "/" + resources[1]+ "/" + resources[2], params, get_metadata_callback);
}

function delete_metadata(url){
    delete_api_call(url, "#metadata_table", "Your metadata item has been deleted")
}