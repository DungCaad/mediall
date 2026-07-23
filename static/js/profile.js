var avatarInput = document.querySelector(".profile-avatar-input input[type='file']");
var avatarPreview = document.querySelector(".profile-avatar-preview");
var avatarFallback = document.querySelector(".profile-avatar-fallback");

if (avatarInput && avatarPreview && avatarFallback) {
    avatarInput.addEventListener("change", function () {
        var file = avatarInput.files && avatarInput.files[0];
        if (!file) {
            return;
        }

        avatarPreview.src = URL.createObjectURL(file);
        avatarPreview.classList.remove("hidden");
        avatarFallback.classList.add("hidden");
    });
}

var profileTabs = document.querySelectorAll("[data-profile-tab]");
var profilePanels = document.querySelectorAll("[data-profile-panel]");

profileTabs.forEach(function (tab) {
    tab.addEventListener("click", function () {
        var target = tab.dataset.profileTab;

        profileTabs.forEach(function (item) {
            var isActive = item === tab;
            item.classList.toggle("active", isActive);
            item.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        profilePanels.forEach(function (panel) {
            panel.classList.toggle("active", panel.dataset.profilePanel === target);
        });
    });
});

var workScheduleForm = document.querySelector("[data-work-schedule-form]");

if (workScheduleForm) {
    var workScheduleInputs = workScheduleForm.querySelectorAll("input[name='work_schedule_type']");
    var customWorkHours = workScheduleForm.querySelector("[data-custom-work-hours]");
    var customTimeInputs = customWorkHours.querySelectorAll("input[type='time']");

    function updateWorkScheduleFields(selectedInput) {
        var isCustom = selectedInput.value === "custom";
        customWorkHours.hidden = !isCustom;
        customTimeInputs.forEach(function (input) {
            input.required = isCustom;
        });
        workScheduleInputs.forEach(function (input) {
            input.closest(".work-schedule-option").classList.toggle("active", input === selectedInput);
        });
    }

    workScheduleInputs.forEach(function (input) {
        input.addEventListener("change", function () {
            updateWorkScheduleFields(input);
        });
    });

    var selectedWorkSchedule = workScheduleForm.querySelector("input[name='work_schedule_type']:checked");
    if (selectedWorkSchedule) {
        updateWorkScheduleFields(selectedWorkSchedule);
    }
}

var busyScheduleForm = document.querySelector("[data-busy-schedule-form]");

if (busyScheduleForm) {
    var busyTimeEditor = busyScheduleForm.querySelector("[data-busy-time-editor]");
    var selectedDateInput = busyScheduleForm.querySelector("[data-selected-date]");
    var selectedDateLabel = busyScheduleForm.querySelector("[data-selected-date-label]");
    var calendarDays = busyScheduleForm.querySelectorAll("[data-calendar-date]");
    var busyTimeInputs = busyScheduleForm.querySelectorAll("input[name='busy_time_slots']");
    var busyCalendar = busyScheduleForm.querySelector("[data-busy-calendar]");
    var busyCalendarHeader = busyScheduleForm.querySelector("[data-busy-calendar-header]");
    var busyCalendarBack = busyScheduleForm.querySelector("[data-busy-calendar-back]");
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    calendarDays.forEach(function (dayButton) {
        dayButton.addEventListener("click", function () {
            var selectedSlots = (dayButton.dataset.busySlots || "").split("|").filter(Boolean);
            var dateValue = dayButton.dataset.calendarDate;

            calendarDays.forEach(function (item) {
                item.classList.toggle("selected", item === dayButton);
            });

            busyTimeInputs.forEach(function (input) {
                input.checked = selectedSlots.includes(input.value);
                input.closest(".busy-time-slot").classList.toggle("selected", input.checked);
            });

            selectedDateInput.value = dateValue;
            selectedDateLabel.textContent = new Intl.DateTimeFormat("vi-VN", {
                weekday: "long",
                day: "2-digit",
                month: "2-digit",
                year: "numeric"
            }).format(new Date(dateValue + "T00:00:00"));

            var formRect = busyScheduleForm.getBoundingClientRect();
            var buttonRect = dayButton.getBoundingClientRect();
            busyTimeEditor.style.setProperty("--reveal-x", (buttonRect.left + buttonRect.width / 2 - formRect.left) + "px");
            busyTimeEditor.style.setProperty("--reveal-y", (buttonRect.top + buttonRect.height / 2 - formRect.top) + "px");
            dayButton.classList.add("activating");
            busyCalendar.classList.add("is-leaving");
            busyCalendarHeader.classList.add("is-leaving");

            window.setTimeout(function () {
                busyCalendar.hidden = true;
                busyCalendarHeader.hidden = true;
                busyCalendar.classList.remove("is-leaving");
                busyCalendarHeader.classList.remove("is-leaving");
                dayButton.classList.remove("activating");
                busyTimeEditor.hidden = false;
                busyTimeEditor.classList.add("is-revealing");
                busyTimeEditor.addEventListener("animationend", function removeRevealClass() {
                    busyTimeEditor.classList.remove("is-revealing");
                    busyTimeEditor.removeEventListener("animationend", removeRevealClass);
                });
                busyTimeEditor.scrollIntoView({behavior: reducedMotion ? "auto" : "smooth", block: "nearest"});
            }, reducedMotion ? 0 : 190);
        });
    });

    busyTimeInputs.forEach(function (input) {
        input.addEventListener("change", function () {
            input.closest(".busy-time-slot").classList.toggle("selected", input.checked);
        });
    });

    busyCalendarBack.addEventListener("click", function () {
        busyTimeEditor.classList.add("is-closing");
        window.setTimeout(function () {
            busyTimeEditor.hidden = true;
            busyTimeEditor.classList.remove("is-closing", "is-revealing");
            busyCalendarHeader.hidden = false;
            busyCalendar.hidden = false;
            busyCalendarHeader.classList.add("is-returning");
            busyCalendar.classList.add("is-returning");
            window.setTimeout(function () {
                busyCalendarHeader.classList.remove("is-returning");
                busyCalendar.classList.remove("is-returning");
            }, reducedMotion ? 0 : 340);
        }, reducedMotion ? 0 : 170);
    });
}

var referralModal = document.querySelector("[data-referral-modal]");

if (referralModal) {
    var referralForm = referralModal.querySelector("[data-referral-form]");
    var referralAppointmentInput = referralModal.querySelector("[data-referral-appointment-id]");
    var referralPatientName = referralModal.querySelector("[data-referral-patient-name]");
    var referralOptions = referralModal.querySelectorAll(".referral-doctor-option input");

    function closeReferralModal() {
        referralModal.hidden = true;
        document.body.classList.remove("modal-open");
    }

    document.querySelectorAll("[data-open-referral-modal]").forEach(function (button) {
        button.addEventListener("click", function () {
            referralAppointmentInput.value = button.dataset.appointmentId;
            referralPatientName.textContent = button.dataset.patientName;
            referralOptions.forEach(function (input) {
                input.checked = false;
                input.closest(".referral-doctor-option").classList.remove("selected");
            });
            referralModal.hidden = false;
            document.body.classList.add("modal-open");
        });
    });

    referralModal.querySelector("[data-close-referral-modal]").addEventListener("click", closeReferralModal);

    referralOptions.forEach(function (input) {
        input.addEventListener("change", function () {
            referralOptions.forEach(function (item) {
                item.closest(".referral-doctor-option").classList.toggle("selected", item.checked);
            });
        });
    });

    referralForm.querySelector("[data-skip-referral]").addEventListener("click", function () {
        referralOptions.forEach(function (input) {
            input.checked = false;
        });
    });

    referralForm.querySelector("[data-require-referral]").addEventListener("click", function (event) {
        if (!referralForm.querySelector("input[name='referral_doctor_id']:checked")) {
            event.preventDefault();
            window.alert("Vui lòng chọn một bác sĩ để giới thiệu hoặc nhấn Bỏ qua giới thiệu.");
        }
    });
}

var paymentModals = document.querySelectorAll("[data-payment-modal]");

function closePaymentModal(modal) {
    modal.hidden = true;
    document.body.classList.remove("modal-open");
}

document.querySelectorAll("[data-open-payment-modal]").forEach(function (button) {
    button.addEventListener("click", function () {
        var modal = document.getElementById(button.dataset.openPaymentModal);
        if (!modal) return;
        modal.hidden = false;
        document.body.classList.add("modal-open");
        var firstInput = modal.querySelector("input:not([type='hidden'])");
        if (firstInput) firstInput.focus();
    });
});

paymentModals.forEach(function (modal) {
    var closeButton = modal.querySelector("[data-close-payment-modal]");
    var cardNumberInput = modal.querySelector("[data-payment-card-number]");
    var cardPreview = modal.querySelector("[data-payment-card-preview]");
    var expiryInput = modal.querySelector("[data-payment-expiry]");

    if (closeButton) {
        closeButton.addEventListener("click", function () {
            closePaymentModal(modal);
        });
    }

    if (cardNumberInput) {
        cardNumberInput.addEventListener("input", function () {
            var digits = cardNumberInput.value.replace(/\D/g, "").slice(0, 16);
            cardNumberInput.value = digits.replace(/(\d{4})(?=\d)/g, "$1 ");
            cardPreview.textContent = (digits.padEnd(16, "•").match(/.{1,4}/g) || []).join(" ");
        });
    }

    if (expiryInput) {
        expiryInput.addEventListener("input", function () {
            var digits = expiryInput.value.replace(/\D/g, "").slice(0, 4);
            expiryInput.value = digits.length > 2
                ? digits.slice(0, 2) + "/" + digits.slice(2)
                : digits;
        });
    }
});

document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    paymentModals.forEach(function (modal) {
        if (!modal.hidden) closePaymentModal(modal);
    });
});
