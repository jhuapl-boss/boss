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

function delete_resource(url) {
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
                    $('#collection_table').bootstrapTable('refresh');
                    swal({
                        title: 'Success',
                        text: "Your resource has been marked for deletion",
                        type: 'success',
                        confirmButtonColor: '#3498DB',
                        confirmButtonText: 'Got it.'
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