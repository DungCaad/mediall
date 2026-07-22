document.querySelectorAll("[data-account-menu]").forEach(function (menu) {
    var toggle = menu.querySelector("[data-account-toggle]");
    if (!toggle) {
        return;
    }

    toggle.addEventListener("click", function (event) {
        event.stopPropagation();
        document.querySelectorAll("[data-notification-menu].active").forEach(function (notificationMenu) {
            notificationMenu.classList.remove("active");
            var notificationToggle = notificationMenu.querySelector("[data-notification-toggle]");
            if (notificationToggle) notificationToggle.setAttribute("aria-expanded", "false");
        });
        menu.classList.toggle("active");
    });
});

document.querySelectorAll("[data-notification-menu]").forEach(function (menu) {
    var toggle = menu.querySelector("[data-notification-toggle]");
    if (!toggle) return;

    toggle.addEventListener("click", function (event) {
        event.stopPropagation();
        document.querySelectorAll("[data-account-menu].active").forEach(function (accountMenu) {
            accountMenu.classList.remove("active");
        });
        var isOpen = menu.classList.toggle("active");
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    var panel = menu.querySelector("[data-notification-panel]");
    if (panel) panel.addEventListener("click", function (event) { event.stopPropagation(); });
});

document.addEventListener("click", function () {
    document.querySelectorAll("[data-account-menu].active").forEach(function (menu) {
        menu.classList.remove("active");
    });
    document.querySelectorAll("[data-notification-menu].active").forEach(function (menu) {
        menu.classList.remove("active");
        var toggle = menu.querySelector("[data-notification-toggle]");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
    });
});
