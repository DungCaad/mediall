var adminOrderTabs = document.querySelectorAll("[data-admin-order-tab]");
var adminOrderPanels = document.querySelectorAll("[data-admin-order-panel]");

adminOrderTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
        var target = tab.dataset.adminOrderTab;

        adminOrderTabs.forEach(function (item) {
            var isActive = item === tab;
            item.classList.toggle("active", isActive);
            item.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        adminOrderPanels.forEach(function (panel) {
            panel.classList.toggle(
                "active",
                panel.dataset.adminOrderPanel === target
            );
        });
    });
});
