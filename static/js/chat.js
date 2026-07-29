(() => {
    "use strict";

    const app = document.querySelector("[data-chat-app]");
    if (!app) return;

    const conversationId = app.dataset.activeConversation;
    const stage = app.querySelector("[data-message-stage]");
    const list = app.querySelector("[data-message-list]");
    const loading = app.querySelector("[data-message-loading]");
    const loadOlderButton = app.querySelector("[data-load-older]");
    const form = app.querySelector("[data-message-form]");
    const input = app.querySelector("[data-message-input]");
    const newMessageJump = app.querySelector("[data-new-message-jump]");
    const attachmentToggle = app.querySelector("[data-toggle-attachments]");
    const attachmentMenu = app.querySelector("[data-attachment-menu]");
    const attachmentInput = app.querySelector("[data-attachment-input]");
    let oldestId = null;
    let newestId = null;
    let hasMore = false;
    let fetching = false;
    let pollTimer = null;

    if (conversationId) app.classList.add("has-active-chat");

    function getCookie(name) {
        const item = document.cookie.split("; ").find((row) => row.startsWith(`${name}=`));
        return item ? decodeURIComponent(item.split("=").slice(1).join("=")) : "";
    }

    function nearBottom() {
        if (!stage) return true;
        return stage.scrollHeight - stage.scrollTop - stage.clientHeight < 110;
    }

    function scrollToBottom(behavior = "auto") {
        if (stage) stage.scrollTo({ top: stage.scrollHeight, behavior });
        if (newMessageJump) newMessageJump.hidden = true;
    }

    function messageNode(message) {
        const row = document.createElement("article");
        row.className = `message-row ${message.is_mine ? "mine" : "theirs"}${message.display_status === "failed" ? " failed" : ""}`;
        row.dataset.messageId = String(message.id);

        if (!message.is_mine) {
            const avatar = document.createElement("a");
            avatar.className = "avatar message-avatar";
            avatar.href = message.sender.profile_url;
            avatar.setAttribute("aria-label", `View ${message.sender.name}'s profile`);
            if (message.sender.avatar_url) {
                const image = document.createElement("img");
                image.src = message.sender.avatar_url;
                image.alt = "";
                avatar.append(image);
            } else {
                avatar.textContent = message.sender.initial;
            }
            row.append(avatar);
        }

        const content = document.createElement("div");
        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        if (message.attachment) {
            if (message.attachment.type === "image") {
                const link = document.createElement("a");
                link.href = message.attachment.url;
                link.target = "_blank";
                link.rel = "noopener";
                const image = document.createElement("img");
                image.className = "message-attachment-image";
                image.src = message.attachment.url;
                image.alt = message.attachment.name;
                link.append(image);
                bubble.append(link);
            } else if (message.attachment.type === "video") {
                const video = document.createElement("video");
                video.className = "message-attachment-video";
                video.src = message.attachment.url;
                video.controls = true;
                video.preload = "metadata";
                bubble.append(video);
            } else {
                const link = document.createElement("a");
                link.className = "message-attachment-document";
                link.href = message.attachment.url;
                link.textContent = message.attachment.name;
                bubble.append(link);
            }
        }
        if (message.content) {
            const text = document.createElement("span");
            text.className = "message-text";
            text.textContent = message.content;
            bubble.append(text);
        }
        content.append(bubble);

        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = message.time_label;
        if (message.is_mine) {
            const status = document.createElement("span");
            status.className = `message-status ${message.display_status}`;
            status.textContent = message.display_status === "failed" ? " · Failed to send" : " · Sent";
            meta.append(status);
            if (message.display_status === "failed") {
                const error = document.createElement("span");
                error.className = "message-error";
                error.textContent = "Check the message and try again.";
                content.append(error);
            }
        }
        content.append(meta);
        row.append(content);
        return row;
    }

    function upsertMessages(messages, prepend = false) {
        const wasNearBottom = nearBottom();
        const previousHeight = stage ? stage.scrollHeight : 0;
        const fragment = document.createDocumentFragment();
        messages.forEach((message) => {
            const current = list.querySelector(`[data-message-id="${message.id}"]`);
            const node = messageNode(message);
            if (current) current.replaceWith(node);
            else fragment.append(node);
            oldestId = oldestId === null ? message.id : Math.min(oldestId, message.id);
            newestId = newestId === null ? message.id : Math.max(newestId, message.id);
        });
        if (prepend) list.prepend(fragment);
        else list.append(fragment);

        if (prepend && stage) stage.scrollTop += stage.scrollHeight - previousHeight;
        else if (wasNearBottom) scrollToBottom();
        else if (messages.length && newMessageJump) newMessageJump.hidden = false;
    }

    function applyStatusUpdates(updates) {
        updates.forEach((update) => {
            const row = list.querySelector(`[data-message-id="${update.id}"]`);
            if (!row) return;
            const status = row.querySelector(".message-status");
            const content = row.lastElementChild;
            const failed = update.display_status === "failed";
            row.classList.toggle("failed", failed);
            if (status) {
                status.className = `message-status ${update.display_status}`;
                status.textContent = failed ? " · Failed to send" : " · Sent";
            }
            let error = row.querySelector(".message-error");
            if (failed && !error) {
                error = document.createElement("span");
                error.className = "message-error";
                error.textContent = "Check the message and try again.";
                content.insertBefore(error, content.querySelector(".message-meta"));
            } else if (!failed && error) {
                error.remove();
            }
        });
    }

    async function fetchMessages(mode = "initial") {
        if (!conversationId || fetching) return;
        fetching = true;
        const params = new URLSearchParams({ limit: "20" });
        if (mode === "older" && oldestId) params.set("before_id", oldestId);
        if (mode === "newer" && newestId) params.set("after_id", newestId);
        try {
            const response = await fetch(`/chat/conversations/${conversationId}/messages?${params}`, {
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!response.ok) throw new Error("Messages could not be loaded.");
            const data = await response.json();
            hasMore = mode === "newer" ? hasMore : data.has_more;
            upsertMessages(data.messages, mode === "older");
            applyStatusUpdates(data.status_updates || []);
            if (loadOlderButton) loadOlderButton.hidden = !hasMore;
            if (loading) loading.hidden = true;
            if (mode === "initial") {
                scrollToBottom();
                if (stage && stage.scrollHeight <= stage.clientHeight && hasMore) {
                    fetching = false;
                    await fetchMessages("older");
                }
            }
        } catch (error) {
            if (loading) loading.textContent = "Messages could not be loaded.";
        } finally {
            fetching = false;
        }
    }

    if (conversationId) {
        fetchMessages().then(() => {
            pollTimer = window.setInterval(() => {
                if (!document.hidden) fetchMessages("newer");
            }, 3000);
        });
    }

    document.addEventListener("visibilitychange", () => {
        if (!document.hidden && conversationId) fetchMessages("newer");
    });

    if (stage) {
        stage.addEventListener("scroll", () => {
            if (stage.scrollTop < 90 && hasMore) fetchMessages("older");
            if (nearBottom() && newMessageJump) newMessageJump.hidden = true;
        }, { passive: true });
    }
    loadOlderButton?.addEventListener("click", () => fetchMessages("older"));
    newMessageJump?.addEventListener("click", () => scrollToBottom("smooth"));

    function closeAttachmentMenu() {
        if (!attachmentMenu || !attachmentToggle) return;
        attachmentMenu.hidden = true;
        attachmentToggle.setAttribute("aria-expanded", "false");
    }

    attachmentToggle?.addEventListener("click", (event) => {
        event.stopPropagation();
        const willOpen = attachmentMenu.hidden;
        attachmentMenu.hidden = !willOpen;
        attachmentToggle.setAttribute("aria-expanded", String(willOpen));
    });
    app.querySelectorAll("[data-attachment-option]").forEach((button) => {
        button.addEventListener("click", () => {
            attachmentInput.accept = button.dataset.accept || "*/*";
            closeAttachmentMenu();
            attachmentInput.click();
        });
    });
    attachmentInput?.addEventListener("change", async () => {
        const file = attachmentInput.files?.[0];
        if (!file) return;
        attachmentToggle.disabled = true;
        const body = new FormData();
        body.append("attachment", file);
        try {
            const response = await fetch(`/chat/conversations/${conversationId}/send`, {
                method: "POST",
                headers: { "X-CSRFToken": getCookie("csrftoken") },
                body,
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "The attachment could not be sent.");
            upsertMessages([data.message]);
            scrollToBottom("smooth");
        } catch (error) {
            window.alert(error.message);
        } finally {
            attachmentInput.value = "";
            attachmentToggle.disabled = false;
        }
    });
    document.addEventListener("click", (event) => {
        if (!event.target.closest(".composer-attachment")) closeAttachmentMenu();
    });
    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeAttachmentMenu();
    });

    form?.addEventListener("submit", async (event) => {
        event.preventDefault();
        const content = input.value.trim();
        if (!content) return;
        const submit = form.querySelector("[type='submit']");
        submit.disabled = true;
        try {
            const response = await fetch(`/chat/conversations/${conversationId}/send`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken"),
                },
                body: JSON.stringify({ content }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "The message could not be sent.");
            input.value = "";
            input.style.height = "auto";
            upsertMessages([data.message]);
            scrollToBottom("smooth");
        } catch (error) {
            window.alert(error.message);
        } finally {
            submit.disabled = false;
            input.focus();
        }
    });

    input?.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    });
    input?.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    const search = app.querySelector("[data-chat-search]");
    const cards = [...app.querySelectorAll("[data-conversation-card]")];
    let activeFilter = "all";
    function filterCards() {
        const query = (search?.value || "").trim().toLocaleLowerCase("vi");
        cards.forEach((card) => {
            const matchesText = card.dataset.searchText.includes(query);
            const matchesFilter = activeFilter === "all"
                || (activeFilter === "unread" && card.dataset.unread === "true")
                || (activeFilter === "group" && card.dataset.group === "true");
            card.hidden = !(matchesText && matchesFilter);
        });
    }
    search?.addEventListener("input", filterCards);
    app.querySelectorAll("[data-filter]").forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.filter;
            app.querySelectorAll("[data-filter]").forEach((item) => {
                const active = item === button;
                item.classList.toggle("active", active);
                item.setAttribute("aria-pressed", String(active));
            });
            filterCards();
        });
    });

    const modal = app.querySelector("[data-compose-modal]");
    const memberSearch = app.querySelector("[data-member-search]");
    app.querySelectorAll("[data-open-compose]").forEach((button) => button.addEventListener("click", () => {
        modal.hidden = false;
        memberSearch?.focus();
    }));
    app.querySelector("[data-close-compose]")?.addEventListener("click", () => { modal.hidden = true; });
    modal?.addEventListener("click", (event) => { if (event.target === modal) modal.hidden = true; });
    memberSearch?.addEventListener("input", () => {
        const query = memberSearch.value.trim().toLocaleLowerCase("vi");
        app.querySelectorAll("[data-user-name]").forEach((button) => {
            button.hidden = !button.dataset.userName.includes(query);
        });
    });
    app.querySelectorAll("[data-user-id]").forEach((button) => button.addEventListener("click", async () => {
        button.disabled = true;
        try {
            const response = await fetch("/chat/conversations", {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": getCookie("csrftoken") },
                body: JSON.stringify({ user_id: button.dataset.userId }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "The conversation could not be created.");
            window.location.assign(`/chat/?conversation=${data.conversation_id}`);
        } catch (error) {
            window.alert(error.message);
            button.disabled = false;
        }
    }));

    app.querySelector("[data-mobile-back]")?.addEventListener("click", () => app.classList.remove("has-active-chat"));
    window.addEventListener("beforeunload", () => { if (pollTimer) window.clearInterval(pollTimer); });
})();
