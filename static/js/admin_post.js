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
                value = window.prompt(
                    button.dataset.editorPromptText || "Enter a value:",
                    button.dataset.editorPromptDefault || ""
                );
                if (!value) return;
            }

            document.execCommand(command, false, value);
            syncPostContent();
        });
    });

    var imageUploadButton = postEditorForm.querySelector("[data-editor-image-upload]");
    if (imageUploadButton) {
        var imageInput = document.createElement("input");
        imageInput.type = "file";
        imageInput.accept = "image/jpeg,image/png,image/webp,image/gif";
        imageInput.hidden = true;
        postEditorForm.appendChild(imageInput);

        var savedImageRange = null;
        imageUploadButton.addEventListener("click", function () {
            var selection = window.getSelection();
            if (selection.rangeCount && postEditor.contains(selection.anchorNode)) {
                savedImageRange = selection.getRangeAt(0).cloneRange();
            }
            imageInput.click();
        });

        imageInput.addEventListener("change", async function () {
            var imageFile = imageInput.files[0];
            if (!imageFile) return;

            var originalLabel = imageUploadButton.textContent;
            imageUploadButton.disabled = true;
            imageUploadButton.textContent = "Uploading...";

            try {
                var uploadData = new FormData();
                uploadData.append("image", imageFile);
                var csrfToken = postEditorForm.querySelector(
                    "input[name='csrfmiddlewaretoken']"
                ).value;
                var response = await fetch(imageUploadButton.dataset.editorImageUpload, {
                    method: "POST",
                    headers: {"X-CSRFToken": csrfToken},
                    body: uploadData
                });
                var result = await response.json();
                if (!response.ok) {
                    throw new Error(result.error || "The image could not be uploaded.");
                }

                postEditor.focus();
                if (savedImageRange) {
                    var selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(savedImageRange);
                }
                document.execCommand("insertImage", false, result.url);
                syncPostContent();
            } catch (error) {
                window.alert(error.message || "The image could not be uploaded.");
            } finally {
                imageUploadButton.disabled = false;
                imageUploadButton.textContent = originalLabel;
                imageInput.value = "";
            }
        });
    }

    postEditor.addEventListener("input", syncPostContent);
    seoDescription.addEventListener("input", updateSeoCount);
    postEditorForm.addEventListener("submit", function (event) {
        syncPostContent();
        if (!postEditor.textContent.trim()) {
            event.preventDefault();
            postEditor.focus();
            window.alert("Enter the post content.");
        }
    });

    syncPostContent();
    updateSeoCount();
}
