var current_offset = 0
var reached_max_next = false;

function get_next_page() {
    current_offset += page_limit
    get_different_page()

    if (current_offset != 0) {
        $("button[name='prev-btn").prop("disabled", false)
    }
}

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

function title_case_boolean_values(bool_value) {
    if (bool_value == true) {
        return "True"
    }
    else {
        return "False"
    }
}

function clear_remaining_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("tr[row_id='" + i + "'] td").text("")
        }
    }
}

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

function openNewAlertForm() {
    $("#form-popup").show(500)
}

function closeNewAlertForm() {
    $("#form-popup").hide(800, $.easing.easeInOutQuart)
    $("input[name='alert_value']").val("")
    $("input[name='alert_name']").val("")
    $("input[name='alert_column']").val($("input[name='alert_column'] option").first().text)
}

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