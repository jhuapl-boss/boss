
function raise_ajax_error(response){
    swal('Uh Oh.',
         'Something went wrong - ' + response.responseJSON["detail"],
          'error'
        )
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