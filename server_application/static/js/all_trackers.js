/*
NAME
    removeTracker - Deletes a tracker from the database
Synopsis
    removeTracker(elem, object_name)
DESCRIPTION
    Removes the row of the tracker from the UI

    sends a request to remove the the tracker from the database
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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
    });
}