var current_f_offset = 0
var current_r_offset = 0
var reached_max_f_next = false;
var reached_max_r_next = false;

/*
NAME
    get_next_f_page - get the next page of alert findings
Synopsis
    get_next_f_page()
DESCRIPTION
    increases the target offset of the database
        For example, if showing findings 0-4, increase offset to 5 so the page will show 5-9
    calls get_different_f_page function

    makes sure to enable the "previous page" button so the user can go back
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_next_f_page() {
    current_f_offset += page_limit
    get_different_f_page()

    if (current_f_offset != 0) {
        $("#findings button[name='prev-btn").prop("disabled", false)
    }
}

/*
NAME
    get_next_r_page - get the next page of alert rules
Synopsis
    get_next_r_page()
DESCRIPTION
    increases the target offset of the database
        For example, if showing rules 0-4, increase offset to 5 so the page will show 5-9
    calls get_different_r_page function

    makes sure to enable the "previous page" button so the user can go back
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_next_r_page() {
    current_r_offset += page_limit
    get_different_r_page()

    if (current_r_offset != 0) {
        $("#rules button[name='prev-btn").prop("disabled", false)
    }
}

/*
NAME
    get_previous_f_page - get the previous page of alert findings
Synopsis
    get_previous_f_page()
DESCRIPTION
    Makes sure the user is not trying to go back to a negative offset.

    decreases the target offset of the database
        For example, if showing findings 5-9, decrease offset to 0 so the page will be 0-4
    calls get_different_f_page function

    potentially disables the "previous page" button so the user will not be able to go back to negative offsets

    makes sure to enable the "next page" button so the user can go forward again
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    get_previous_r_page - get the previous page of alert rules
Synopsis
    get_previous_r_page()
DESCRIPTION
    Makes sure the user is not trying to go back to a negative offset.

    decreases the target offset of the database
        For example, if showing rules 5-9, decrease offset to 0 so the page will be 0-4
    calls get_different_r_page function

    potentially disables the "previous page" button so the user will not be able to go back to negative offsets

    makes sure to enable the "next page" button so the user can go forward again
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    get_different_f_page - change the finding page shown on the screen
Synopsis
    get_different_f_page()
DESCRIPTION
    Synchronously calls the SELECT API to get the next/previous rows of alert findings
        requests page_limit (currently set to 5) + 2 = 7 findings

        If I get 0 findings, remain in current page
        If I get 1 - page_limit findings, show requested page and disable "next page" button
        If I get more than page_limit findings, show requested page and keep "next page" button enabled

    calls fill_valued_f_rows and clear_remaining_f_rows to change the actual table of data

RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    get_different_r_page - change the rule page shown on the screen
Synopsis
    get_different_r_page()
DESCRIPTION
    Synchronously calls the SELECT API to get the next/previous rows of alert rules
        requests page_limit (currently set to 5) + 2 = 7 findings

        If I get 0 rules, remain in current page
        If I get 1 - page_limit rules, show requested page and disable "next page" button
        If I get more than page_limit rules, show requested page and keep "next page" button enabled

    calls fill_valued_r_rows and clear_remaining_r_rows to change the actual table of data

RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    fill_valued_f_rows - fills rows of findings
Synopsis
    fill_valued_f_rows(page_data)
        page_data      -> findings to be displayed in the table page
DESCRIPTION
    Fills the findings table rows with recently fetched data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function fill_valued_f_rows(page_data) {
    $.each(page_data, function(row_index, row_object) {
        $.each(row_object, function(col_key, col_value) {
            if (typeof(col_value) == "boolean") {
                col_value = title_case_boolean_values(col_value)
            }

            var elem_to_change = $("#findings tr[row_id='" + row_index + "'] td[col_id='" + col_key + "']")
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

/*
NAME
    fill_valued_r_rows - fills rows of rules
Synopsis
    fill_valued_r_rows(page_data)
        page_data      -> rules to be displayed in the table page
DESCRIPTION
    Fills the rules table rows with recently fetched data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function fill_valued_r_rows(page_data) {
    $.each(page_data, function(row_index, row_object) {
        $.each(row_object, function(col_key, col_value) {
            if (typeof(col_value) == "boolean") {
                col_value = title_case_boolean_values(col_value)
            }

            var elem_to_change = $("#rules tr[row_id='" + row_index + "'] td[col_id='" + col_key + "']")
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
    clear_remaining_f_rows - clears findings table rows when changing pages
Synopsis
    clear_remaining_f_rows(last_row_edited)
        last_row_edited      -> int index of table row last filled
DESCRIPTION
    Clears findings table rows when switching pages with a different number of findings.

    For example: If I switch from a page with 5 findings to a page with 4 findings, you need to clear the last row.
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function clear_remaining_f_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("#findings tr[row_id='" + i + "'] td").text("")
        }
    }
}

/*
NAME
    clear_remaining_r_rows - clears rules table rows when changing pages
Synopsis
    clear_remaining_r_rows(last_row_edited)
        last_row_edited      -> int index of table row last filled
DESCRIPTION
    Clears rules table rows when switching pages with a different number of rules.

    For example: If I switch from a page with 5 rules to a page with 4 rules, you need to clear the last row.
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function clear_remaining_r_rows(last_row_edited) {
    for (var i = 0; i <= page_limit; i++) {
        if (i >= last_row_edited) {
            $("#rules tr[row_id='" + i + "'] td").text("")
        }
    }
}