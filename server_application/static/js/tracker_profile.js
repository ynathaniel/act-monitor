var current_offset = 0
var reached_max_next = false;


/*
NAME
    get_next_page - get the next page of tracker data findings
Synopsis
    get_next_page()
DESCRIPTION
    increases the target offset of the database
        For example, if showing rows 0-4, increase offset to 5 so the page will show 5-9
    calls get_different_page function

    makes sure to enable the "previous page" button so the user can go back
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_next_page() {
    current_offset += page_limit
    get_different_page()

    if (current_offset != 0) {
        $("button[name='prev-btn").prop("disabled", false)
    }
}

/*
NAME
    get_previous_page - get the previous page of tracker data findings
Synopsis
    get_previous_page()
DESCRIPTION
    increases the target offset of the database
        For example, if showing rows 0-4, increase offset to 5 so the page will show 5-9
    calls get_different_page function

    makes sure to enable the "previous page" button so the user can go back
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_previous_page() {
    if (current_offset == 0) {
        return

    }

    current_offset -= page_limit
    get_different_page()

    if (current_offset == 0) {
        $("button[name='prev-btn").prop("disabled", true)
    }

    // clicking the "previous" button would make it not the last page
    $("button[name='next-btn").prop("disabled", false)
}

/*
NAME
    get_different_page - change the events page shown on the screen
Synopsis
    get_different_page()
DESCRIPTION
    Synchronously calls the SELECT API to get the next/previous rows of tracker events
        requests page_limit (currently set to 5) + 2 = 7 events

        If I get 0 events, remain in current page
        If I get 1 - page_limit events, show requested page and disable "next page" button
        If I get more than page_limit events, show requested page and keep "next page" button enabled

    calls fill_valued_rows and clear_remaining_rows to change the actual table of data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_different_page() {
    var select_object_data_url = "/api/tracking/select?object_name=" + object_name + "&column_data=" + select_columns
    select_object_data_url += "&limit=" + (page_limit+2) + "&offset=" + current_offset

    $.get(select_object_data_url, function(data) {
        page_data = data.page_data

        if (page_data.length < (page_limit+1)) {
            // reached the max page
            $("button[name='next-btn").prop("disabled", true)
        }
        if (page_data.length > 0) {
            fill_valued_rows(page_data)
            clear_remaining_rows(page_data.length)
        }
        else {
            get_previous_page()
        }
    })
}

/*
NAME
    fill_valued_rows - fills rows of tracker events
Synopsis
    fill_valued_rows(page_data)
        page_data      -> events to be displayed in the table page
DESCRIPTION
    Fills the events table rows with recently fetched data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function fill_valued_rows(page_data) {
    $.each(page_data, function(row_index, row_object) {
        $.each(row_object, function(col_key, col_value) {
            if (typeof(col_value) == "boolean") {
                col_value = title_case_boolean_values(col_value)
            }

            var elem_to_change = $("tr[row_id='" + row_index + "'] td[col_id='" + col_key + "']")
            if (col_key == "_id") {
                elem_to_change.attr("onclick", "deleteRow(this, " + col_value + ")").html("&times")
            }
            else {
                elem_to_change.text(col_value)
            }
        })
    })
}

/*
NAME
    title_case_boolean_values - title case a bool value
Synopsis
    title_case_boolean_values(bool_value)
        bool_value      -> boolean value to title case
DESCRIPTION
    Python booleans are written in title case (True, False) instead of lower case (true, false)

    To match this with javascript, I have to convert the lower case to title case

RETURNS
    title case string of boolean
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function title_case_boolean_values(bool_value) {
    if (bool_value == true) {
        return "True"
    }
    else {
        return "False"
    }
}

/*
NAME
    clear_remaining_rows - clears table rows when changing pages
Synopsis
    clear_remaining_rows(last_row_edited)
        last_row_edited      -> int index of table row last filled
DESCRIPTION
    Clears table rows when switching pages with a different number of tracked events.

    For example: If I switch from a page with 5 events to a page with 4 events, you need to clear the last row.
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function clear_remaining_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("tr[row_id='" + i + "'] td").text("")
        }
    }
}

/*
NAME
    deleteRow - deletes an event from the tracker
Synopsis
    deleteRow(elem, row_id)
        elem      -> html element of the delete button
        row_id    -> the id of the event in the tracker database table
DESCRIPTION
    Deletes a row from the database and from the UI table

    Refreshes the page to make sure to show updated results
    For example: If the table page showed 5 events and 1 was deleted, it now shows 4.
        The refresh fetches results from the database and potentially shows 5 events again
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function deleteRow(elem, row_id) {
    var table_row_id = $(elem).parent().attr("row_id")
    $("tr[row_id='" + table_row_id + "'] td").text("")

    var obj_to_drop = {
        _id: row_id
    }

    var api_url = "/api/tracking/delete/" + object_name
    $.post(api_url,
        JSON.stringify(obj_to_drop),
        function (data, status) {
            console.log(data.status)
            if (data.status == "success") {

            }
    });
    setTimeout(function(){
        get_different_page()
    }, 350)

}

/*
NAME
    sendExampleRequest - Sends an example insert request to insert sample row
Synopsis
    sendExampleRequest()
DESCRIPTION
    Uses constant data to fill out a database table row that fits most data types.

    Refreshes the page after a short wait (waiting for the backend to asynchronously insert the item)
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function sendExampleRequest() {
    var insert_data = {}

    for (var key in column_types) {
        if (key == "_id") {
            continue
        }

        if (column_types[key] == "BOOLEAN") {
            insert_data[key] = true
        }
        else if (column_types[key] == "VARCHAR" || column_types[key] == "UNICODE") {
            insert_data[key] = "Example String"
        }
        else if (column_types[key] == "INTEGER") {
            insert_data[key] = 12345
        }
    }


    var api_url = "/api/tracking/insert/" + object_name
    $.post(api_url,
        JSON.stringify(insert_data),
        function (data, status) {
            console.log(data.status)
            if (data.status == "success") {
                setTimeout(function(){
                    location.reload(true)
                }, 405)
            }
    });
}

/*
NAME
    openNewAlertForm - Opens the popup to create a new alert rule
Synopsis
    openNewAlertForm()
DESCRIPTION
    Opens a popup that creates an alert rule for this tracker
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function openNewAlertForm() {
    $("#form-popup").show(500)
}

/*
NAME
    closeNewAlertForm - Closes the popup to create a new alert rule
Synopsis
    closeNewAlertForm()
DESCRIPTION
    Closes a popup that creates an alert rule for this tracker

    Clears/resets the fields of the form
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function closeNewAlertForm() {
    $("#form-popup").hide(800, $.easing.easeInOutQuart)
    $("input[name='alert_value']").val("")
    $("input[name='alert_name']").val("")
    $("input[name='alert_column']").val($("input[name='alert_column'] option").first().text)
}

/*
NAME
    submitNewAlertForm - Submits the form to create a new alert rule
Synopsis
    submitNewAlertForm()
DESCRIPTION
    Submits the form to create an alert rule for this tracker

    Gathers all of the form inputs and verifies none are null
        If any fields are null, open pop up of error

    Sends an insert request to the database to insert an alert rule
    Closes the popup
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function submitNewAlertForm() {
    var new_alert_data = {
        name: $("[name='alert_name']").val(),
        object_name: object_name,
        column_name: $("[name='alert_column']").val(),
        column_value: $("[name='alert_value']").val()
    }
    $.each(new_alert_data, function(key, value) {
        if (value == null || value == "") {
            openPopup("Missing argument - " + key)
            return
        }
    })

    var api_url = "/api/tracking/insert/_Alert_Rules"
    $.post(api_url,
        JSON.stringify(new_alert_data),
        function (data, status) {
            console.log(data.status)
            if (data.status == "success") {
                closeNewAlertForm()
            }
        });

}