var current_f_offset = 0
var current_r_offset = 0
var reached_max_f_next = false;
var reached_max_r_next = false;

function get_next_f_page() {
    current_f_offset += page_limit
    get_different_f_page()

    if (current_f_offset != 0) {
        $("#findings button[name='prev-btn").prop("disabled", false)
    }
}

function get_next_r_page() {
    current_r_offset += page_limit
    get_different_r_page()

    if (current_r_offset != 0) {
        $("#rules button[name='prev-btn").prop("disabled", false)
    }
}

function get_previous_f_page() {
    if (current_f_offset == 0) {
        return

    }

    current_f_offset -= page_limit
    get_different_f_page()

    if (current_f_offset == 0) {
        $("#findings button[name='prev-btn").prop("disabled", true)
    }

    // clicking the "previous" button would make it not the last page
    $("#findings button[name='next-btn").prop("disabled", false)
}

function get_previous_r_page() {
    if (current_r_offset == 0) {
        return

    }

    current_r_offset -= page_limit
    get_different_r_page()

    if (current_r_offset == 0) {
        $("#rules button[name='prev-btn").prop("disabled", true)
    }

    // clicking the "previous" button would make it not the last page
    $("#rules button[name='next-btn").prop("disabled", false)
}

function get_different_f_page() {
    var select_object_data_url = "/api/tracking/select?object_name=_Alert_Finds&column_data=_id,rule_name,object_name,column_name,found_value"
    select_object_data_url += "&limit=" + (page_limit+2) + "&offset=" + current_f_offset

    $.get(select_object_data_url, function(data) {
        page_data = data.page_data

        if (page_data.length < (page_limit+1)) {
            // reached the max page
            $("#findings button[name='next-btn").prop("disabled", true)
        }
        if (page_data.length > 0) {
            fill_valued_f_rows(page_data)
            clear_remaining_f_rows(page_data.length)
        }
        else {
            get_previous_f_page()
        }
    })
}

function get_different_r_page() {
    var select_object_data_url = "/api/tracking/select?object_name=_Alert_Rules"
    select_object_data_url += "&column_data=_id,name,object_name,column_name,column_value"
    select_object_data_url += "&limit=" + (page_limit+2) + "&offset=" + current_r_offset

    $.get(select_object_data_url, function(data) {
        page_data = data.page_data

        if (page_data.length < (page_limit+1)) {
            // reached the max page
            $("#rules button[name='next-btn").prop("disabled", true)
        }
        if (page_data.length > 0) {
            fill_valued_r_rows(page_data)
            clear_remaining_r_rows(page_data.length)
        }
        else {
            get_previous_r_page()
        }
    })
}

function fill_valued_f_rows(page_data) {
    $.each(page_data, function(row_index, row_object) {
        $.each(row_object, function(col_key, col_value) {
            if (typeof(col_value) == "boolean") {
                col_value = title_case_boolean_values(col_value)
            }

            var elem_to_change = $("#findings tr[row_id='" + row_index + "'] td[col_id='" + col_key + "']")
            if (col_key == "_id") {
                elem_to_change.attr("onclick", "deleteRow(this, " + col_value + ")").html("&#10003;")
            }
            else if (col_key == "object_name") {
                var object_link = "<a href='/trackers/profile/" + col_value.toLowerCase().split(' ').join('_') + "'>";
                object_link += col_value+"</a>"
                elem_to_change.text(object_link)
            }
            else {
                elem_to_change.text(col_value)
            }
        })
    })
}

function fill_valued_r_rows(page_data) {
    $.each(page_data, function(row_index, row_object) {
        $.each(row_object, function(col_key, col_value) {
            if (typeof(col_value) == "boolean") {
                col_value = title_case_boolean_values(col_value)
            }

            var elem_to_change = $("#rules tr[row_id='" + row_index + "'] td[col_id='" + col_key + "']")
            if (col_key == "_id") {
                elem_to_change.attr("onclick", "deleteRow(this, " + col_value + ")").html("&times")
            }
            else if (col_key == "object_name") {
                var object_link = "<a href='/trackers/profile/" + col_value.toLowerCase().split(' ').join('_') + "'>";
                object_link += object_name+"</a>"
                elem_to_change.text(object_link)
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

function clear_remaining_f_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("#findings tr[row_id='" + i + "'] td").text("")
        }
    }
}

function clear_remaining_r_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("#rules tr[row_id='" + i + "'] td").text("")
        }
    }
}