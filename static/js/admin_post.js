var postEditorForm = document.querySelector("[data-post-editor-form]");

if (postEditorForm) {
    var postEditor = postEditorForm.querySelector("[data-post-editor]");
    var postEditorInput = postEditorForm.querySelector("[data-post-editor-input]");
    var seoDescription = postEditorForm.querySelector("[data-seo-description]");
    var seoCount = postEditorForm.querySelector("[data-seo-count]");

    function syncPostContent() {
        postEditorInput.value = postEditor.innerHTML.trim();
    }

    function updateSeoCount() {
        seoCount.textContent = String(seoDescription.value.length);
    }

    postEditorForm.querySelectorAll("[data-editor-command]").forEach(function (button) {
        button.addEventListener("click", function () {
            postEditor.focus();
            var command = button.dataset.editorCommand;
            var value = button.dataset.editorValue || null;

            if (button.dataset.editorPrompt === "true") {
                value = window.prompt("Nhập địa chỉ liên kết (https://...):", "https://");
                if (!value) return;
            }

            document.execCommand(command, false, value);
            syncPostContent();
        });
    });

    postEditor.addEventListener("input", syncPostContent);
    seoDescription.addEventListener("input", updateSeoCount);
    postEditorForm.addEventListener("submit", function (event) {
        syncPostContent();
        if (!postEditor.textContent.trim()) {
            event.preventDefault();
            postEditor.focus();
            window.alert("Vui lòng nhập nội dung bài viết.");
        }
    });

    syncPostContent();
    updateSeoCount();
}
