(function () {
    "use strict";

    document.documentElement.lang = "vi";

    var translationData = document.getElementById("ui-translations");
    var translations = translationData ? JSON.parse(translationData.textContent) : {};
    var sourceByVietnamese = Object.keys(translations).reduce(function (result, source) {
        result[translations[source]] = source;
        return result;
    }, {});
    var translationSources = Object.keys(translations).sort(function (left, right) {
        return right.length - left.length;
    });

    function escapedPattern(value) {
        return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    var patterns = [
        [/^Found (\d+) results?(?: for "(.+)")?\.$/, function (m) { return "Tìm thấy " + m[1] + " kết quả" + (m[2] ? " cho “" + (translations[m[2]] || m[2]) + "”" : "") + "."; }],
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
                    result = typeof entry[1] === "function"
                        ? entry[1](clean.match(entry[0]))
                        : clean.replace(entry[0], entry[1]);
                    return true;
                }
                return false;
            });
        }
        if (!result) {
            var partial = clean;
            translationSources.forEach(function (source) {
                var boundaryPattern = new RegExp(
                    "(^|[\\s·|:,(])" + escapedPattern(source) + "(?=$|[\\s·|:,.!?;)])",
                    "g"
                );
                partial = partial.replace(boundaryPattern, function (match, prefix) {
                    return prefix + translations[source];
                });
            });
            if (partial !== clean) result = partial;
        }
        return result ? value.replace(clean, result) : value;
    }

    function translateElement(root) {
        if (!root || root.nodeType !== Node.ELEMENT_NODE) return;
        var elements = [root].concat(Array.from(root.querySelectorAll("[placeholder], [aria-label], [title]")));
        elements.forEach(function (element) {
            ["placeholder", "aria-label", "title"].forEach(function (name) {
                if (element.hasAttribute(name)) element.setAttribute(name, translated(element.getAttribute(name)));
            });
            if (element.matches('input[type="search"][value]')) {
                element.value = translated(element.value);
            }
        });
        var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
        var node;
        while ((node = walker.nextNode())) {
            if (!node.parentElement || /^(SCRIPT|STYLE|TEXTAREA)$/.test(node.parentElement.tagName)) continue;
            if (node.parentElement.closest(".post-body, .doctor-public-introduction, .doctor-review-comment, .message-text, .conversation-copy")) continue;
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

    document.addEventListener("submit", function (event) {
        event.target.querySelectorAll('input[type="search"]').forEach(function (input) {
            input.value = sourceByVietnamese[input.value.trim()] || input.value;
        });
    }, true);
}());
