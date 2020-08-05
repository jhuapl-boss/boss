function collection_handler(response) {
    var detail_base_url = API_ROOT + "mgmt/resources/";
    var delete_function = "delete_collection";
    var delete_base_url = API_ROOT + "collection/";

    return resource_formatter(response, detail_base_url, delete_function, delete_base_url);
}

function coord_handler(response) {
    var detail_base_url = API_ROOT + "mgmt/coord/";
    var delete_function = "delete_coord_frame";
    var delete_base_url = API_ROOT + "coord/";

    return resource_formatter(response, detail_base_url, delete_function, delete_base_url);
}


function experiment_handler(response) {
    var resources = get_resource_names();
    var detail_base_url = API_ROOT + "mgmt/resources/" + resources[0] + "/";
    var delete_function = "delete_experiment";
    var delete_base_url = API_ROOT + "collection/" + resources[0] + "/experiment/";

    return resource_formatter(response, detail_base_url, delete_function, delete_base_url);
}

function get_collections_callback(params, response) {
    params.success(response.collections);
}
function get_collections(params) {
    get_api_call(API_ROOT + "collection", params, get_collections_callback);
}


function get_experiments_callback(params, response) {
    params.success(response.experiments);
}
function get_experiments(params) {
    var resources = get_resource_names();
    get_api_call(API_ROOT + "collection/" + resources[0], params, get_experiments_callback);
}


function get_coords_callback(params, response) {
    params.success(response.coords);
}
function get_coords(params) {
    get_api_call(API_ROOT + "coord", params, get_coords_callback);
}

function get_metadata_callback(params, response) {
    params.success(response.keys)
}
function get_metadata(params) {
    var resources = get_resource_names();
    get_api_call(API_ROOT + "meta/" + resources[0], params, get_metadata_callback);
}

function delete_collection(url){
    delete_api_call(url, "#collection_table", "Your collection has been marked for deletion")
}
function delete_coord_frame(url){
    delete_api_call(url, "#coord_table", "Your coordinate frame has been marked for deletion")
}
function delete_experiment(url){
    delete_api_call(url, "#experiment_table", "Your experiment has been marked for deletion")
}
function delete_metadata(url){
    delete_api_call(url, "#metadata_table", "Your metadata item has been deleted")
}
