function activate_nav_item() {
    // get menu item corresponding with the current page
    active_item = $(".nav-item[name='{{ data.name }}']")
    // activate the menu item
    $(active_item).addClass("active")

    // make sure all menu groups leading to item are open
    parent_groups = $(active_item).parents(".nav-group")
    $.each(parent_groups, function(index, group) {
        console.log(group)
        $(group).addClass("keep-open")
        open_submenu(group)
    })
}

        function open_submenu(elem) {
            var items = get_nav_group_items(elem)

            // open nav list
            $(items.list).removeClass("hidden-item").addClass("expanded")
            // change the arrow direction to left
            $(items.arrow).addClass("fa-angle-left").removeClass("fa-angle-down")
            // change some padding
            $(elem).addClass("expanded")
        }

        function close_submenu(elem) {
            if ($(elem).hasClass("keep-open")) {
                return
            }

            var items = get_nav_group_items(elem)

            // close nav list
            $(items.list).addClass("hidden-item").removeClass("expanded")
            // change the arrow direction to down
            $(items.arrow).addClass("fa-angle-down").removeClass("fa-angle-left")
            // change some padding
            $(elem).removeClass("expanded")
        }

        function get_nav_group_items(elem) {
            var group = {
                list: $(elem).find("ul"),
                arrow: $(elem).find("i")
            }
            return group
        }

function openPopup(text_to_use) {
    $("#alert-popup span").html(text_to_use)
    $("#alert-popup").show(500)
}

function closePopup() {
    $("#alert-popup").hide(800, $.easing.easeInOutQuart)

}