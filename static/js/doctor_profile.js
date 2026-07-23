var doctorBookingForm = document.querySelector("[data-doctor-booking-form]");

if (doctorBookingForm) {
    var bookingMonthInput = doctorBookingForm.querySelector("input[name='booking_month']");
    var openBookingEntry = document.querySelector("[data-open-booking-entry]");
    var bookingDateSelect = doctorBookingForm.querySelector("[data-booking-date-select]");
    var bookingDateOptions = doctorBookingForm.querySelectorAll("[data-booking-date-option]");
    var bookingCalendarDays = doctorBookingForm.querySelectorAll("[data-booking-calendar-day]");
    var openBookingDatePicker = doctorBookingForm.querySelector("[data-open-booking-date-picker]");
    var bookingDatePicker = doctorBookingForm.querySelector("[data-booking-date-picker]");
    var bookingDateSummary = doctorBookingForm.querySelector("[data-booking-date-summary]");
    var bookingCalendarMonths = doctorBookingForm.querySelectorAll("[data-booking-calendar-month]");
    var bookingMonthActions = doctorBookingForm.querySelectorAll("[data-booking-month-direction]");
    var bookingMonthLabel = doctorBookingForm.querySelector("[data-booking-month-label]");
    var bookingTimeSelect = doctorBookingForm.querySelector("[data-booking-time-select]");
    var bookingRequestModal = doctorBookingForm.querySelector("[data-booking-request-modal]");
    var bookingServiceInputs = doctorBookingForm.querySelectorAll("input[name='service_type']");
    var bookingFeeTotal = doctorBookingForm.querySelector("[data-booking-fee-total]");
    var bookingFeeValue = doctorBookingForm.querySelector("[data-booking-fee-value]");
    var closeBookingRequestModal = doctorBookingForm.querySelector("[data-close-booking-request-modal]");

    function updateBookingServiceFee(selectedService) {
        bookingServiceInputs.forEach(function (serviceInput) {
            serviceInput.closest(".booking-service-option").classList.toggle("selected", serviceInput === selectedService);
        });
        if (!selectedService || !selectedService.dataset.serviceFee) {
            bookingFeeTotal.hidden = true;
            bookingFeeValue.textContent = "";
            return;
        }
        bookingFeeValue.textContent = "$" + Number(selectedService.dataset.serviceFee).toFixed(2) + " /visit";
        bookingFeeTotal.hidden = false;
    }

    bookingServiceInputs.forEach(function (serviceInput) {
        serviceInput.addEventListener("change", function () {
            updateBookingServiceFee(serviceInput);
        });
        if (serviceInput.checked) updateBookingServiceFee(serviceInput);
    });

    if (openBookingEntry) {
        openBookingEntry.addEventListener("click", function () {
            bookingRequestModal.hidden = false;
            document.body.classList.add("modal-open");
            bookingDateSelect.focus();
        });
    }

    if (bookingDateSelect) {
        bookingDateSelect.addEventListener("change", function () {
            var selectedDate = Array.from(bookingDateOptions).find(function (dateOption) {
                return dateOption.dataset.dateValue === bookingDateSelect.value;
            });
            var unavailableSlots = selectedDate
                ? (selectedDate.dataset.unavailableSlots || "").split("|").filter(Boolean)
                : [];
            bookingDateSelect.setCustomValidity(
                bookingDateSelect.value && !selectedDate
                    ? "The doctor is not available on this date. Please choose another date."
                    : ""
            );
            bookingTimeSelect.querySelectorAll("option[value]").forEach(function (timeOption) {
                timeOption.disabled = timeOption.value !== "" && unavailableSlots.includes(timeOption.value);
            });
            bookingTimeSelect.value = "";
            bookingTimeSelect.disabled = !bookingDateSelect.value || !selectedDate;
            bookingMonthInput.value = bookingDateSelect.value ? bookingDateSelect.value.slice(0, 7) : "";
            if (bookingDateSelect.value && !selectedDate) bookingDateSelect.reportValidity();
        });
    }

    if (openBookingDatePicker) {
        openBookingDatePicker.addEventListener("click", function () {
            bookingDatePicker.hidden = !bookingDatePicker.hidden;
            openBookingDatePicker.setAttribute("aria-expanded", String(!bookingDatePicker.hidden));
        });
    }

    var activeBookingMonthIndex = 0;

    function updateBookingMonthActions() {
        bookingMonthActions.forEach(function (action) {
            var direction = Number(action.dataset.bookingMonthDirection);
            action.disabled = (
                (direction < 0 && activeBookingMonthIndex === 0)
                || (direction > 0 && activeBookingMonthIndex === bookingCalendarMonths.length - 1)
            );
        });
        if (bookingCalendarMonths[activeBookingMonthIndex]) {
            bookingMonthLabel.textContent = bookingCalendarMonths[activeBookingMonthIndex].dataset.monthLabel;
        }
    }

    bookingMonthActions.forEach(function (action) {
        action.addEventListener("click", function () {
            var direction = Number(action.dataset.bookingMonthDirection);
            var nextIndex = activeBookingMonthIndex + direction;
            if (nextIndex < 0 || nextIndex >= bookingCalendarMonths.length) return;
            var currentMonth = bookingCalendarMonths[activeBookingMonthIndex];
            var nextMonth = bookingCalendarMonths[nextIndex];
            currentMonth.classList.add(direction > 0 ? "slide-out-left" : "slide-out-right");
            window.setTimeout(function () {
                currentMonth.hidden = true;
                currentMonth.classList.remove("slide-out-left", "slide-out-right");
                nextMonth.hidden = false;
                nextMonth.classList.add(direction > 0 ? "slide-in-right" : "slide-in-left");
                window.requestAnimationFrame(function () {
                    nextMonth.classList.remove("slide-in-right", "slide-in-left");
                });
                activeBookingMonthIndex = nextIndex;
                updateBookingMonthActions();
            }, 150);
        });
    });

    updateBookingMonthActions();

    bookingCalendarDays.forEach(function (calendarDay) {
        calendarDay.addEventListener("click", function () {
            bookingDateSelect.value = calendarDay.dataset.bookingCalendarDay;
            bookingDateSummary.textContent = calendarDay.dataset.bookingCalendarDay;
            bookingCalendarDays.forEach(function (day) {
                day.classList.toggle("selected", day === calendarDay);
            });
            bookingDateSelect.dispatchEvent(new Event("change"));
            bookingDatePicker.hidden = true;
            openBookingDatePicker.setAttribute("aria-expanded", "false");
        });
    });

    if (bookingDateSelect.value) bookingDateSummary.textContent = bookingDateSelect.value;

    if (bookingDateSelect && bookingDateSelect.value) {
        var retainedTimeValue = bookingTimeSelect.value;
        bookingDateSelect.dispatchEvent(new Event("change"));
        bookingTimeSelect.value = retainedTimeValue;
    }

    if (closeBookingRequestModal) {
        closeBookingRequestModal.addEventListener("click", function () {
            bookingRequestModal.hidden = true;
            document.body.classList.remove("modal-open");
        });
    }

}

var translateIntroductionButton = document.querySelector("[data-translate-introduction]");

var bookingAttachmentsInput = document.querySelector("[data-booking-attachments]");

if (bookingAttachmentsInput) {
    var bookingAttachmentPreview = document.querySelector("[data-booking-attachment-preview]");
    bookingAttachmentsInput.addEventListener("change", function () {
        bookingAttachmentsInput.setCustomValidity("");
        bookingAttachmentPreview.replaceChildren();
        Array.from(bookingAttachmentsInput.files).forEach(function (file) {
            var item = document.createElement("li");
            item.textContent = file.name + " · " + (file.size / 1024 / 1024).toFixed(1) + " MB";
            bookingAttachmentPreview.appendChild(item);

            if (file.type.startsWith("video/")) {
                var video = document.createElement("video");
                var videoUrl = URL.createObjectURL(file);
                video.preload = "metadata";
                video.onloadedmetadata = function () {
                    URL.revokeObjectURL(videoUrl);
                    if (video.duration > 30) {
                        item.textContent += " · Longer than 30 seconds";
                        item.classList.add("invalid");
                        bookingAttachmentsInput.setCustomValidity("Videos must be 30 seconds or shorter.");
                        bookingAttachmentsInput.reportValidity();
                    } else {
                        item.textContent += " · " + video.duration.toFixed(1) + "s";
                    }
                };
                video.onerror = function () {
                    URL.revokeObjectURL(videoUrl);
                    item.textContent += " · Duration could not be verified";
                    item.classList.add("invalid");
                    bookingAttachmentsInput.setCustomValidity("This video's duration could not be verified.");
                    bookingAttachmentsInput.reportValidity();
                };
                video.src = videoUrl;
            }
        });
        bookingAttachmentPreview.hidden = bookingAttachmentsInput.files.length === 0;
    });
}

if (translateIntroductionButton) {
    var introductionSource = JSON.parse(document.getElementById("doctor-introduction-source").textContent);
    var introductionTranslation = document.querySelector("[data-introduction-translation]");
    var introductionTranslationText = document.querySelector("[data-introduction-translation-text]");
    var csrfToken = document.querySelector("[name='csrfmiddlewaretoken']").value;

    translateIntroductionButton.addEventListener("click", function () {
        if (!introductionTranslation.hidden) {
            introductionTranslation.hidden = true;
            translateIntroductionButton.textContent = "View English translation";
            return;
        }
        if (introductionTranslationText.textContent) {
            introductionTranslation.hidden = false;
            translateIntroductionButton.textContent = "Hide English translation";
            return;
        }

        translateIntroductionButton.disabled = true;
        translateIntroductionButton.textContent = "Translating...";
        fetch(translateIntroductionButton.dataset.translationUrl, {
            method: "POST",
            headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
            body: JSON.stringify({text: introductionSource})
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    if (!response.ok) throw new Error(data.error || "Translation failed.");
                    return data;
                });
            })
            .then(function (data) {
                introductionTranslationText.textContent = data.translation;
                introductionTranslation.hidden = false;
                translateIntroductionButton.textContent = "Hide English translation";
            })
            .catch(function (translationError) {
                introductionTranslationText.textContent = translationError.message;
                introductionTranslation.hidden = false;
                translateIntroductionButton.textContent = "Try translation again";
            })
            .finally(function () {
                translateIntroductionButton.disabled = false;
            });
    });
}
