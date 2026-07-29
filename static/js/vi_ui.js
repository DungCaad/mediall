(function () {
    "use strict";

    document.documentElement.lang = "vi";

    var translationData = document.getElementById("ui-translations");
    var translations = translationData ? JSON.parse(translationData.textContent) : {};

    var patterns = [
        [/^Found (\d+) results?(?: for "(.+)")?\.$/, function (m) { return "Tìm thấy " + m[1] + " kết quả" + (m[2] ? " cho “" + m[2] + "”" : "") + "."; }],
        [/^(\d+) views$/, "$1 lượt xem"], [/^(\d+) reviews$/, "$1 đánh giá"], [/^(\d+) notifications$/, "$1 thông báo"],
        [/^(\d+) unread messages$/, "$1 tin nhắn chưa đọc"], [/^(\d+) stars?$/, "$1 sao"],
        [/^Order #(\d+)$/, "Đơn hàng #$1"], [/^Request #(\d+)$/, "Yêu cầu #$1"]
    ];

    function translated(value) {
        var clean = value.trim();
        if (!clean) return value;
        var result = translations[clean];
        if (!result) {
            patterns.some(function (entry) {
                if (entry[0].test(clean)) {
                    result = clean.replace(entry[0], entry[1]);
                    return true;
                }
                return false;
            });
        }
        return result ? value.replace(clean, result) : value;
    }

    function translateElement(root) {
        if (!root || root.nodeType !== Node.ELEMENT_NODE) return;
        ["placeholder", "aria-label", "title"].forEach(function (name) {
            if (root.hasAttribute(name)) root.setAttribute(name, translated(root.getAttribute(name)));
        });
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        var node;
        while ((node = walker.nextNode())) {
            if (!node.parentElement || /^(SCRIPT|STYLE|TEXTAREA)$/.test(node.parentElement.tagName)) continue;
            if (node.parentElement.closest(".post-body, .doctor-public-introduction, .doctor-review-comment")) continue;
            node.nodeValue = translated(node.nodeValue);
        }
    }

    document.title = translated(document.title);
    translateElement(document.body);
    new MutationObserver(function (changes) {
        changes.forEach(function (change) {
            change.addedNodes.forEach(function (node) {
                if (node.nodeType === Node.ELEMENT_NODE) translateElement(node);
                else if (node.nodeType === Node.TEXT_NODE && node.parentElement) node.nodeValue = translated(node.nodeValue);
            });
        });
    }).observe(document.body, {childList: true, subtree: true});
}());
