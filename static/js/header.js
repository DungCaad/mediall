document.querySelectorAll("[data-account-menu]").forEach(function (menu) {
    var toggle = menu.querySelector("[data-account-toggle]");
    if (!toggle) {
        return;
    }

    toggle.addEventListener("click", function (event) {
        event.stopPropagation();
        document.querySelectorAll("[data-header-chat-menu].active").forEach(function (chatMenu) {
            chatMenu.classList.remove("active");
            var chatToggle = chatMenu.querySelector("[data-header-chat-toggle]");
            if (chatToggle) chatToggle.setAttribute("aria-expanded", "false");
        });
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
        document.querySelectorAll("[data-header-chat-menu].active").forEach(function (chatMenu) {
            chatMenu.classList.remove("active");
            var chatToggle = chatMenu.querySelector("[data-header-chat-toggle]");
            if (chatToggle) chatToggle.setAttribute("aria-expanded", "false");
        });
        document.querySelectorAll("[data-account-menu].active").forEach(function (accountMenu) {
            accountMenu.classList.remove("active");
        });
        var isOpen = menu.classList.toggle("active");
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    var panel = menu.querySelector("[data-notification-panel]");
    if (panel) panel.addEventListener("click", function (event) { event.stopPropagation(); });
});

document.querySelectorAll("[data-header-chat-menu]").forEach(function (menu) {
    var toggle = menu.querySelector("[data-header-chat-toggle]");
    var search = menu.querySelector("[data-header-chat-search]");
    var items = Array.from(menu.querySelectorAll("[data-header-chat-item]"));
    var activeFilter = "all";
    if (!toggle) return;

    function filterItems() {
        var query = search ? search.value.trim().toLocaleLowerCase("vi") : "";
        items.forEach(function (item) {
            var matchesText = item.dataset.searchText.indexOf(query) !== -1;
            var matchesFilter = activeFilter === "all"
                || (activeFilter === "unread" && item.dataset.unread === "true")
                || (activeFilter === "group" && item.dataset.group === "true");
            item.hidden = !(matchesText && matchesFilter);
        });
    }

    toggle.addEventListener("click", function (event) {
        event.stopPropagation();
        document.querySelectorAll("[data-account-menu].active, [data-notification-menu].active").forEach(function (openMenu) {
            openMenu.classList.remove("active");
        });
        var isOpen = menu.classList.toggle("active");
        toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    menu.querySelector("[data-header-chat-panel]").addEventListener("click", function (event) {
        event.stopPropagation();
    });
    if (search) search.addEventListener("input", filterItems);
    menu.querySelectorAll("[data-header-chat-filter]").forEach(function (button) {
        button.addEventListener("click", function () {
            activeFilter = button.dataset.headerChatFilter;
            menu.querySelectorAll("[data-header-chat-filter]").forEach(function (filterButton) {
                var active = filterButton === button;
                filterButton.classList.toggle("active", active);
                filterButton.setAttribute("aria-pressed", active ? "true" : "false");
            });
            filterItems();
        });
    });
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
    document.querySelectorAll("[data-header-chat-menu].active").forEach(function (menu) {
        menu.classList.remove("active");
        var toggle = menu.querySelector("[data-header-chat-toggle]");
        if (toggle) toggle.setAttribute("aria-expanded", "false");
    });
});
