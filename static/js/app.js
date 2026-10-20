// ============================================================
// DISRUPTION FORM
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const type =
            document.getElementById(
                "disruptionType"
            );

        if (!type) {
            return;
        }


        updateDisruptionFields();


        type.addEventListener(
            "change",
            updateDisruptionFields
        );

    }
);


function updateDisruptionFields() {

    const type =
        document.getElementById(
            "disruptionType"
        ).value;


    const companyGroup =
        document.getElementById(
            "companyGroup"
        );


    const arrivalGroup =
        document.getElementById(
            "arrivalGroup"
        );


    const studentGroup =
        document.getElementById(
            "studentGroup"
        );


    const roomGroup =
        document.getElementById(
            "roomGroup"
        );


    // Hide everything first

    companyGroup.style.display = "none";

    arrivalGroup.style.display = "none";

    studentGroup.style.display = "none";

    roomGroup.style.display = "none";


    // Company late

    if (type === "company_late") {

        companyGroup.style.display = "block";

        arrivalGroup.style.display = "block";

    }


    // Student withdrawal

    if (type === "student_withdrawal") {

        studentGroup.style.display = "block";

    }


    // Room unavailable

    if (type === "room_unavailable") {

        roomGroup.style.display = "block";

    }

}


// ============================================================
// RUN REPLAN
// ============================================================

async function runReplan() {

    const type =
        document.getElementById(
            "disruptionType"
        ).value;


    const company =
        document.getElementById(
            "company"
        ).value;


    const student =
        document.getElementById(
            "student"
        ).value;


    const room =
        document.getElementById(
            "room"
        ).value;


    const arrival =
        document.getElementById(
            "newArrivalTime"
        ).value;


    const resultBox =
        document.getElementById(
            "replanResult"
        );


    // --------------------------------------------------------
    // Validation
    // --------------------------------------------------------

    if (!type) {

        showResult(
            "Please select a disruption type.",
            false
        );

        return;
    }


    if (
        type === "company_late"
        && !company
    ) {

        showResult(
            "Please select a company.",
            false
        );

        return;
    }


    if (
        type === "student_withdrawal"
        && !student
    ) {

        showResult(
            "Please select a student.",
            false
        );

        return;
    }


    if (
        type === "room_unavailable"
        && !room
    ) {

        showResult(
            "Please select a room.",
            false
        );

        return;
    }


    // --------------------------------------------------------
    // Loading
    // --------------------------------------------------------

    resultBox.style.display = "block";

    resultBox.innerHTML =
        "<strong>Replanning...</strong><br>" +
        "Please wait while the scheduler finds feasible slots.";


    // --------------------------------------------------------
    // Send request
    // --------------------------------------------------------

    try {

        const response =
            await fetch(
                "/api/replan",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        disruption_type: type,

                        company_id:
                            company || null,

                        student_id:
                            student || null,

                        room_id:
                            room || null,

                        new_arrival_time:
                            arrival || null
                    })
                }
            );


        const data =
            await response.json();


        // ----------------------------------------------------
        // Display result
        // ----------------------------------------------------

        if (!data.success) {

            showResult(
                data.message,
                false
            );

            return;
        }


        let html = "";

        html +=
            "<h3>Replan Successful</h3>";


        html +=
            "<p>" +
            data.message +
            "</p>";


        html +=
            "<p><strong>Affected interviews:</strong> " +
            data.affected_count +
            "</p>";


        if (
            data.changes
            &&
            data.changes.length > 0
        ) {

            html +=
                "<h3>Change Summary</h3>";


            html +=
                "<div class='change-list'>";


            data.changes.forEach(
                function (change) {

                    html +=
                        "<div class='change-item'>";


                    html +=
                        "<strong>" +
                        change.type +
                        "</strong>";


                    html +=
                        "<br>Student: " +
                        change.student;


                    html +=
                        "<br>Company: " +
                        change.company;


                    if (
                        change.old_day
                        !== undefined
                    ) {

                        html +=
                            "<br>Old: Day " +
                            change.old_day +
                            " | " +
                            change.old_time;

                    }


                    if (
                        change.new_day
                        !== undefined
                    ) {

                        html +=
                            "<br>New: Day " +
                            change.new_day +
                            " | " +
                            change.new_time;

                    }


                    if (
                        change.new_room
                        !== undefined
                    ) {

                        html +=
                            "<br>Room: " +
                            change.new_room;

                    }


                    html +=
                        "</div>";

                }
            );


            html +=
                "</div>";

        }


        html +=
            "<br>" +
            "<a href='/schedule' " +
            "class='button secondary'>" +
            "View Updated Schedule" +
            "</a>";


        resultBox.innerHTML = html;


    } catch (error) {

        showResult(
            "Could not connect to the server: " +
            error,
            false
        );

    }

}


// ============================================================
// SHOW RESULT
// ============================================================

function showResult(
    message,
    success
) {

    const resultBox =
        document.getElementById(
            "replanResult"
        );


    resultBox.style.display = "block";


    resultBox.innerHTML =
        "<strong>" +
        message +
        "</strong>";


    if (success) {

        resultBox.className =
            "replan-result success-result";

    } else {

        resultBox.className =
            "replan-result error-result";

    }

}