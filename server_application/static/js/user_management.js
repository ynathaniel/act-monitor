
/*
NAME
    openNewUserForm - opens the user form popup
Synopsis
    openNewUserForm(text_to_use)
        text_to_use    -> text to show in the popup
DESCRIPTION
    Opens the new user form popup
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function openNewUserForm() {
    $("#form-popup").show(500)
}

/*
NAME
    closeNewUserForm - closes the user form popup
Synopsis
    closeNewUserForm()
DESCRIPTION
    Closes the user form popup
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function closeNewUserForm() {
    $("#form-popup").hide(800, $.easing.easeInOutQuart)
    clearNewUserForm()
}

/*
NAME
    submitNewUserForm - Submits the new user form
Synopsis
    submitNewUserForm()
DESCRIPTION
    Gathers all of the form inputs.
    Request server to create user.
    If successful, close the form popup and add new user row to the UI
    Else, open a popup error
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function submitNewUserForm() {
    var form_data = {
        name: $("input[name='name']").val(),
        password: $("input[name='password']").val(),
        email: $("input[name='email']").val(),
        is_admin: $("input[name='is_admin']").is(":checked")
    }
    var api_url = "/api/user-management/create-user"
    $.post(api_url,
        JSON.stringify(form_data),
        function (response_data, status) {
            if (response_data.status == "success") {
                closeNewUserForm()
                clearNewUserForm()
                addNewUserRow(form_data)
            }
            else {
                openPopup(response_data.status_description)
            }
    });
}

/*
NAME
    clearNewUserForm - Clears the new user form
Synopsis
    clearNewUserForm()
DESCRIPTION
    Clears all the fields of the new user form
    Only done when form is submitted correctly
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function clearNewUserForm() {
    $("input[name='name']").val("")
    $("input[name='password']").val("")
    $("input[name='email']").val("")
    $("input[name='is_admin']").prop('checked', false)
}

/*
NAME
    deleteUser - Deletes an authorized user
Synopsis
    deleteUser(elem, email)
        elem        -> html delete element of the user row
        email       -> the email of the user to delete
DESCRIPTION
    Removes the user row from the UI
    Requests server to delete the user with this email

    Does not acknowledge errors
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function deleteUser(elem, email) {
    $(elem).parent().parent().remove()

    var obj_to_drop = {
        email: email
    }

    var api_url = "/api/user-management/delete-user"
    $.post(api_url,
        JSON.stringify(obj_to_drop),
        function (data, status) {
            console.log(data.status)
            if (data.status == "success") {

            }
    });
}

/*
NAME
    addNewUserRow - Deletes an authorized user
Synopsis
    addNewUserRow(row_data)
        row_data     -> data of user to enter into this row
DESCRIPTION
    Creates a new row in the users table using the new user data
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function addNewUserRow(row_data) {
    var name_elem = $("<td></td>").text(row_data.name)
    var email_elem = $("<td></td>").text(row_data.email)

    admin_value = row_data.is_admin.toString()
    admin_value = admin_value.charAt(0).toUpperCase() + admin_value.slice(1);
    console.log(admin_value)
    var admin_elem = $("<td></td>").text(admin_value)

    var delete_elem = $("<td></td>")
            .addClass("col-md-1").addClass("col-xs-6")
            .append($("<span></span>")
                .addClass("remove-mark")
                .attr("onclick", "deleteUser(this, '" + row_data.email + "')")
                .html("&times;")
            )

    var new_row = $("<tr></tr>").append(name_elem).append(email_elem).append(admin_elem).append(delete_elem)

    console.log()

    $("tbody").append(new_row)
}
