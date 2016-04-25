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

function openPopup(text_to_use) {
    $(".popup span").html(text_to_use)
    $(".popup").show(500)
}

function closePopup() {
    $(".popup").hide(800, $.easing.easeInOutQuart)
}