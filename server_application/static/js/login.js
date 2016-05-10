/*
NAME
    attemptLogin - Try to login with some username and password
Synopsis
    attemptLogin()
DESCRIPTION
    Grabs the credentials from the input fields
    Asks server if these are working credentials
    If authenticated, redirect to dashboard
    Else, open error popup
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function attemptLogin() {
    var login_details = {
        email: $("input[name='email']").val(),
        password: $("input[name='password']").val()
    }
    var login_url = "/login/"
     $.post(login_url,
        JSON.stringify(login_details),
        function (response_data, status) {
            if (response_data.status == "success") {
                window.location.replace("/")
            }
            else {
                openPopup("WRONG CREDENTIALS")
            }
    });
}

/*
NAME
    openPopup - opens the basic error popup
Synopsis
    openPopup(text_to_use)
        text_to_use    -> text to show in the popup
DESCRIPTION
    Opens the basic error popup that exists on the login page
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function openPopup(text_to_use) {
    $(".popup span").html(text_to_use)
    $(".popup").show(500)
}

/*
NAME
    closePopup - closes the basic error popup
Synopsis
    closePopup()
DESCRIPTION
    Closes the basic error popup that exists on the login page
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function closePopup() {
    $(".popup").hide(800, $.easing.easeInOutQuart)
}