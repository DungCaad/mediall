var doctorBookingForm = document.querySelector("[data-doctor-booking-form]");

if (doctorBookingForm) {
    var bookingDateOptions = doctorBookingForm.querySelectorAll("[data-booking-date]");
    var bookingSlotOptions = doctorBookingForm.querySelectorAll("[data-booking-slot]");
    var selectedDateInput = doctorBookingForm.querySelector("[data-booking-selected-date]");
    var bookingMonthInput = doctorBookingForm.querySelector("input[name='booking_month']");
    var selectedDateLabel = doctorBookingForm.querySelector("[data-booking-selected-label]");
    var bookingShifts = doctorBookingForm.querySelector("[data-booking-shifts]");
    var bookingCalendar = doctorBookingForm.querySelector("[data-booking-calendar]");
    var bookingCalendarHeader = doctorBookingForm.querySelector("[data-booking-calendar-header]");
    var bookingDateStrip = doctorBookingForm.querySelector("[data-booking-date-strip]");
    var bookingStripButtons = doctorBookingForm.querySelectorAll("[data-booking-strip-scroll]");
    var unavailableSlotMessage = doctorBookingForm.querySelector("[data-booking-slot-message]");
    var bookingRequestModal = doctorBookingForm.querySelector("[data-booking-request-modal]");
    var bookingModalDate = doctorBookingForm.querySelector("[data-booking-modal-date]");
    var bookingModalTime = doctorBookingForm.querySelector("[data-booking-modal-time]");
    var closeBookingRequestModal = doctorBookingForm.querySelector("[data-close-booking-request-modal]");
    var reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function openBookingDate(dateButton) {
        var unavailableSlots = (dateButton.dataset.unavailableSlots || "").split("|").filter(Boolean);
        var dateValue = dateButton.dataset.bookingDate;

        bookingDateOptions.forEach(function (option) {
            option.classList.toggle("selected", option === dateButton);
        });

        bookingSlotOptions.forEach(function (option) {
            var input = option.querySelector("input");
            var isUnavailable = unavailableSlots.includes(input.value);
            input.disabled = isUnavailable;
            input.checked = false;
            option.classList.toggle("unavailable", isUnavailable);
            option.classList.remove("selected");
        });
        unavailableSlotMessage.hidden = true;

        selectedDateInput.value = dateValue;
        bookingMonthInput.value = dateValue.slice(0, 7);
        selectedDateLabel.textContent = new Intl.DateTimeFormat("en-GB", {
            weekday: "long",
            day: "2-digit",
            month: "2-digit",
            year: "numeric"
        }).format(new Date(dateValue + "T00:00:00"));

        bookingShifts.hidden = false;
        bookingShifts.classList.remove("is-closing");
        bookingShifts.classList.add("is-revealing");
        bookingShifts.addEventListener("animationend", function removeRevealClass() {
            bookingShifts.classList.remove("is-revealing");
            bookingShifts.removeEventListener("animationend", removeRevealClass);
        });
    }

    bookingDateOptions.forEach(function (option) {
        option.addEventListener("click", function () {
            openBookingDate(option);
        });
    });

    function updateBookingStripButtons() {
        var atStart = bookingDateStrip.scrollLeft <= 2;
        var atEnd = bookingDateStrip.scrollLeft + bookingDateStrip.clientWidth >= bookingDateStrip.scrollWidth - 2;
        bookingStripButtons.forEach(function (button) {
            var direction = Number(button.dataset.bookingStripScroll);
            button.disabled = direction < 0 ? atStart : atEnd;
        });
    }

    bookingStripButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            bookingDateStrip.scrollBy({
                left: Number(button.dataset.bookingStripScroll) * bookingDateStrip.clientWidth,
                behavior: reducedMotion ? "auto" : "smooth"
            });
        });
    });
    bookingDateStrip.addEventListener("scroll", updateBookingStripButtons);
    window.addEventListener("resize", updateBookingStripButtons);
    updateBookingStripButtons();

    if (bookingDateOptions.length) {
        openBookingDate(bookingDateOptions[0]);
    }

    bookingSlotOptions.forEach(function (option) {
        option.addEventListener("click", function (event) {
            if (option.classList.contains("unavailable")) {
                event.preventDefault();
                unavailableSlotMessage.hidden = false;
                unavailableSlotMessage.classList.remove("showing");
                window.requestAnimationFrame(function () {
                    unavailableSlotMessage.classList.add("showing");
                });
            } else {
                unavailableSlotMessage.hidden = true;
            }
        });

        option.querySelector("input").addEventListener("change", function () {
            bookingSlotOptions.forEach(function (item) {
                item.classList.toggle("selected", item.querySelector("input").checked);
            });
            if (bookingRequestModal && option.querySelector("input").checked) {
                bookingModalDate.textContent = selectedDateLabel.textContent;
                bookingModalTime.textContent = option.querySelector("span").textContent;
                bookingRequestModal.hidden = false;
                document.body.classList.add("modal-open");
                bookingRequestModal.querySelector("textarea").focus();
            }
        });
    });

    if (closeBookingRequestModal) {
        closeBookingRequestModal.addEventListener("click", function () {
            bookingRequestModal.hidden = true;
            document.body.classList.remove("modal-open");
        });
    }

}

var translateIntroductionButton = document.querySelector("[data-translate-introduction]");

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
