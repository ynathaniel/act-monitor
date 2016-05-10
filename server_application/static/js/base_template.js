/*
NAME
    activate_nav_item - highlights the menu item of the current page
Synopsis
    activate_nav_item()
DESCRIPTION
    The navigation menu item of the current page will get highlighted
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    open_submenu - expands navigation group
Synopsis
    open_submenu(elem)
        elem    -> html element of navigation items group
DESCRIPTION
    Expands the navigation items group to reveal sub-navigation items
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function open_submenu(elem) {
    var items = get_nav_group_items(elem)

    // open nav list
    $(items.list).removeClass("hidden-item").addClass("expanded")
    // change the arrow direction to left
    $(items.arrow).addClass("fa-angle-left").removeClass("fa-angle-down")
    // change some padding
    $(elem).addClass("expanded")
}

/*
NAME
    close_submenu - closes navigation group
Synopsis
    close_submenu(elem)
        elem    -> html element of navigation items group
DESCRIPTION
    Closes the navigation items group to stop revealing sub-navigation items
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
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

/*
NAME
    get_nav_group_items - retrieves the sub-items of the navigation group
Synopsis
    get_nav_group_items(elem)
        elem    -> html element of navigation items group
DESCRIPTION
    Retrieves the arrow symbol of the navigation group

    Retrieves the list of sub-navigation items
RETURNS
    object containing sub-items and arrow
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function get_nav_group_items(elem) {
    var group = {
        list: $(elem).find("ul"),
        arrow: $(elem).find("i")
    }
    return group
}

/*
NAME
    openPopup - opens the basic error popup
Synopsis
    openPopup(text_to_use)
        text_to_use    -> text to show in the popup
DESCRIPTION
    Opens the basic error popup that exists on every page
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function openPopup(text_to_use) {
    $("#alert-popup span").html(text_to_use)
    $("#alert-popup").show(500)
}

/*
NAME
    closePopup - closes the basic error popup
Synopsis
    closePopup()
DESCRIPTION
    Closes the basic error popup that exists on every page
RETURNS
    null
AUTHOR
    Yoav Nathaniel
DATE
    5/9/2016
*/
function closePopup() {
    $("#alert-popup").hide(800, $.easing.easeInOutQuart)

}