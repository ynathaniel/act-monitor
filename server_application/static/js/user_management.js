function openNewUserForm(text_to_use) {
    $("#form-popup").show(500)
}

function closeNewUserForm() {
    $("#form-popup").hide(800, $.easing.easeInOutQuart)
    clearNewUserForm()
}

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

function clearNewUserForm() {
    $("input[name='name']").val("")
    $("input[name='password']").val("")
    $("input[name='email']").val("")
    $("input[name='is_admin']").prop('checked', false)
}

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
