var row_id_count = 1
// this is old
//      var property_type_list = [ "Boolean", "DateTime", "Integer", "Float", "String", "Unicode", "ARRAY(Integer)",
//          "ARRAY(String)", "ARRAY(Unicode)", "JSON"]
var property_type_list = [ "Boolean", "DateTime", "Integer", "Float", "String", "Unicode"]
var added_form_rows = {}


/*
NAME
    addEmptyFormRow - Add a new empty row to the new tracker form
Synopsis
    addEmptyFormRow()
DESCRIPTION
    Adds another row to the new tracker form
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function addEmptyFormRow() {
    var name_input = $("<input />")
                .attr("type", "text")
                .attr("name", "property_name_" + row_id_count)
                .attr("placeholder", "Property Name")
    var name_section = $("<div></div>")
                .addClass("col-md-4").addClass("col-xs-6")
                .append(name_input)

    var prop_type_select = $("<select></select>")
                .attr("name", "property_type_" + row_id_count)
    for (var prop_type in property_type_list) {
        var prop_type_option = $("<option></option>")
                    .text(property_type_list[prop_type])

        $(prop_type_select).append(prop_type_option)
    }
    var prop_type_section = $("<div></div>")
                .addClass("col-md-3").addClass("col-xs-6")
                .append(prop_type_select)

    var extras = $("<div></div>")
                .addClass("col-md-4").addClass("col-xs-6")
                .append($("<div></div>")
                    .addClass("form-part")
                    .append("Can be null: ")
                    .append($("<input />")
                        .attr("type", "checkbox")
                        .attr("name", "property_nullable_" + row_id_count)
                    )
                ).append($("<div></div>")
                    .addClass("form-part")
                    .append("Is Unique: ")
                    .append($("<input />")
                        .attr("type", "checkbox")
                        .attr("name", "property_unique_" + row_id_count)
                    )
                )

    var remove_section = $("<div></div>")
                .addClass("col-md-1").addClass("col-xs-6")
                .append($("<span></span>")
                    .addClass("remove-mark")
                    .attr("onclick", "removeFormRow(" + row_id_count + ")")
                    .html("&times;")
                )

    var form_row = $("<div></div>")
                .addClass("form-row")
                .attr("row-id", row_id_count)
                .append(name_section)
                .append(prop_type_section)
                .append(extras)
                .append(remove_section)

    $(".form-data").append($(form_row))
    added_form_rows[row_id_count] = form_row
    row_id_count += 1
}

/*
NAME
    removeFormRow - Delete a row from the new tracker form
Synopsis
    removeFormRow(row_id)
        row_id      -> id of the form row to delete
DESCRIPTION
    removes the html row
    removes the row from the recorded rows
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function removeFormRow(row_id) {
    if (row_id in added_form_rows) {
        $(added_form_rows[row_id]).remove()
        delete added_form_rows[row_id]
    }
}

/*
NAME
    gather_all_inputs - Gathers the inputs of all the fields in the new tracker form
Synopsis
    gather_all_inputs()
DESCRIPTION
    Gathers the tracker name and all of its properties from the UI
    If a required input field is missing, open popup with error
RETURNS
    data_found  -> object containing tracker name and its properties
    {
        name: TRACKER NAME,
        properties: [
            name: PROPERTY NAME,
            type: PROPERTY TYPE,
            nullable: BOOLEAN,
            unique: BOOLEAN
        ]
    }
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function gather_all_inputs() {
    if ($("[name='tracker_name']").val() == "") {
        alert("Tracker name is empty!")
        return null
    }

    if (row_id_count == 1) {
        openPopup("The tracker must have at least one property!")
        return null
    }

    data_found = {
        name: $("[name='tracker_name']").val(),
        properties: []
    }

    for (var row_id in added_form_rows) {
        if ($("[name='property_name_" + row_id + "']").val() == "") {
            openPopup("Property #" + (data_found.properties.length + 1) + " has no name!")
            return null
        }

        var row_info = {
            name: $("[name='property_name_" + row_id + "']").val(),
            type: $("[name='property_type_" + row_id + "']").val(),
            nullable: $("[name='property_nullable_" + row_id + "']").is(':checked'),
            unique: $("[name='property_unique_" + row_id + "']").is(':checked')
        }

        data_found.properties.push(row_info)
    }

    console.log(data_found)
    return data_found
}

/*
NAME
    createNewTracker - Submits the new tracker form
Synopsis
    createNewTracker()
DESCRIPTION
    Calls gather_all_inputs() to gather the form data. If found a problem, don't submit form.
    Request server to create tracker, if successful, redirect to All Trackers page
RETURNS
    data_found  -> object containing tracker name and its properties
    {
        name: TRACKER NAME,
        properties: [
            name: PROPERTY NAME,
            type: PROPERTY TYPE,
            nullable: BOOLEAN,
            unique: BOOLEAN
        ]
    }
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function createNewTracker() {
    all_inputs = gather_all_inputs()
    if (all_inputs == null) {
        return
    }
    var api_url = "/api/tracking/create"
    $.post(api_url,
        JSON.stringify(all_inputs),
        function (response_data, status) {
            if (response_data.status == "success") {
                setTimeout(function(){
                    window.location.replace("/trackers/")
                }, 430)
            }
            else {
                openPopup(response_data.status_description)
            }
    });
}