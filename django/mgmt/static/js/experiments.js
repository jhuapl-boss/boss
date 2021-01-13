function channel_handler(response) {
    var resources = get_resource_names();
    var detail_base_url = API_ROOT + "mgmt/resources/" + resources[0] + "/" + resources[1] + "/";
    var delete_function = "delete_channel";
    var delete_base_url = API_ROOT + "collection/" + resources[0] + "/experiment/" + resources[1] + "/channel/";
    var neuroglancer_url = "https://neuroglancer.bossdb.io/#!{'layers':{'" + resources[1] + "':{'source':'boss://https://" + window.location.host + "/" + resources[0] + "/" + resources[1] + "/";

    return channel_resource_formatter(response, detail_base_url, delete_function, delete_base_url, neuroglancer_url);
}

function get_channels_callback(params, response) {
    params.success(response.channels);
}
function get_channels(params) {
    var resources = get_resource_names();
    get_api_call(API_ROOT + "collection/" + resources[0] + "/experiment/" + resources[1], params, get_channels_callback);
}

function get_metadata_callback(params, response) {
    params.success(response.keys)
}
function get_metadata(params) {
    var resources = get_resource_names();
    get_api_call(API_ROOT + "meta/" + resources[0] + "/" + resources[1], params, get_metadata_callback);
}

function delete_channel(url){
    delete_api_call(url, "#channel_table", "Your channel has been marked for deletion")
}

function delete_metadata(url){
    delete_api_call(url, "#metadata_table", "Your metadata item has been deleted")
}

function add_coord_frame_link() {
    // Get the input box
    var input_box = $("#id_coord_frame");

    // Get the link to the coord frame
    var link_url = MGMT_ROOT + "coord/" + input_box.val();

    input_box.parent().addClass("input-group");
    input_box.siblings()[0].remove();
    input_box.parent().append('<div class="input-group-btn"><a id="b1" href="' + link_url + '" target="_blank" class="btn btn-default"><span class="glyphicon glyphicon-new-window" aria-hidden="true"></span> Show Details</a></div>');
}
