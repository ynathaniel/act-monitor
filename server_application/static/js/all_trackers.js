function removeTracker(elem, object_name) {
    $(elem).parent().parent().remove()

    var obj_to_drop = {
        name: object_name
    }

    var api_url = "/api/tracking/drop"
    $.post(api_url,
        JSON.stringify(obj_to_drop),
        function (data, status) {
            console.log(data.status)
            if (data.status == "success") {

            }
    });
}