import sqlite3

from config import DATABASE_PATH

from scheduler.conflict_checker import can_schedule


DAY_START = 9 * 60
DAY_END = 17 * 60

LUNCH_START = 13 * 60
LUNCH_END = 14 * 60

NUMBER_OF_DAYS = 4

SLOT_GRANULARITY = 15


def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


def minutes_to_time(minutes):

    hours = minutes // 60

    mins = minutes % 60

    return f"{hours:02d}:{mins:02d}"


def time_to_minutes(time_string):

    if not time_string:

        return DAY_START

    hours, minutes = map(
        int,
        time_string.split(":")
    )

    return (
        hours * 60
        + minutes
    )


def generate_time_slots(duration):

    slots = []

    current = DAY_START


    while (
        current + duration
        <= DAY_END
    ):

        # Skip lunch

        if (
            current >= LUNCH_START
            and current < LUNCH_END
        ):

            current = LUNCH_END

            continue


        # Do not cross lunch

        if (
            current < LUNCH_START
            and
            current + duration >
            LUNCH_START
        ):

            current = LUNCH_END

            continue


        slots.append(current)


        current += SLOT_GRANULARITY


    return slots


def priority_value(priority):

    return {

        "HIGH": 3,

        "MEDIUM": 2,

        "LOW": 1

    }.get(
        priority,
        1
    )


def get_interview_requests(
    connection
):

    return connection.execute(
        """
        SELECT

            s.id AS student_id,

            s.student_code,

            s.name AS student_name,

            s.cgpa,

            s.branch,

            c.id AS company_id,

            c.name AS company_name,

            c.priority,

            c.interview_duration,

            c.panel_count,

            c.arrival_time

        FROM shortlists sc

        JOIN students s
            ON s.id = sc.student_id

        JOIN companies c
            ON c.id = sc.company_id
        """
    ).fetchall()


def sort_requests(requests):

    return sorted(

        requests,

        key=lambda request: (

            -priority_value(
                request["priority"]
            ),

            -request[
                "interview_duration"
            ],

            -request["cgpa"]

        )

    )


def is_panel_free(
    connection,
    company_id,
    panel_id,
    day,
    start_time,
    end_time
):

    rows = connection.execute(
        """
        SELECT
            start_time,
            end_time

        FROM interviews

        WHERE company_id = ?

        AND panel_id = ?

        AND day = ?

        AND status = 'SCHEDULED'
        """,
        (
            company_id,
            panel_id,
            day
        )
    ).fetchall()


    new_start = time_to_minutes(
        start_time
    )


    new_end = time_to_minutes(
        end_time
    )


    for row in rows:

        old_start = time_to_minutes(
            row["start_time"]
        )


        old_end = time_to_minutes(
            row["end_time"]
        )


        if (
            new_start < old_end
            and
            old_start < new_end
        ):

            return False


    return True


def schedule_interview(
    connection,
    request,
    blocked_room_id=None,
    blocked_panel_id=None
):

    student_id = request[
        "student_id"
    ]


    company_id = request[
        "company_id"
    ]


    duration = int(
        request[
            "interview_duration"
        ]
    )


    panel_count = int(
        request[
            "panel_count"
        ]
    )


    arrival_time = request[
        "arrival_time"
    ]


    if arrival_time:

        arrival_minutes = (
            time_to_minutes(
                arrival_time
            )
        )

    else:

        arrival_minutes = DAY_START


    slots = generate_time_slots(
        duration
    )


    # --------------------------------------------------------
    # Rooms
    # --------------------------------------------------------

    rooms = connection.execute(
        """
        SELECT
            id

        FROM rooms

        WHERE available = 1

        ORDER BY id
        """
    ).fetchall()


    # --------------------------------------------------------
    # Search days
    # --------------------------------------------------------

    for day in range(
        1,
        NUMBER_OF_DAYS + 1
    ):


        for start_minutes in slots:


            # Company arrival

            if (
                start_minutes
                < arrival_minutes
            ):

                continue


            end_minutes = (
                start_minutes
                + duration
            )


            start_time = (
                minutes_to_time(
                    start_minutes
                )
            )


            end_time = (
                minutes_to_time(
                    end_minutes
                )
            )


            # ------------------------------------------------
            # Rooms
            # ------------------------------------------------

            for room in rooms:

                room_id = room["id"]


                if (
                    blocked_room_id
                    is not None
                    and
                    room_id ==
                    blocked_room_id
                ):

                    continue


                # --------------------------------------------
                # Panels
                # --------------------------------------------

                for panel_id in range(
                    1,
                    panel_count + 1
                ):


                    if (
                        blocked_panel_id
                        is not None
                        and
                        panel_id ==
                        blocked_panel_id
                    ):

                        continue


                    # Panel conflict

                    if not is_panel_free(
                        connection,

                        company_id,

                        panel_id,

                        day,

                        start_time,

                        end_time
                    ):

                        continue


                    # All hard constraints

                    if not can_schedule(
                        student_id=
                            student_id,

                        company_id=
                            company_id,

                        room_id=
                            room_id,

                        panel_id=
                            panel_id,

                        day=
                            day,

                        start_time=
                            start_time,

                        end_time=
                            end_time,

                        connection=
                            connection
                    ):

                        continue


                    # Valid slot

                    connection.execute(
                        """
                        INSERT INTO interviews
                        (
                            student_id,
                            company_id,
                            room_id,
                            day,
                            start_time,
                            end_time,
                            panel_id,
                            status
                        )

                        VALUES
                        (
                            ?, ?, ?, ?,
                            ?, ?, ?, ?
                        )
                        """,
                        (
                            student_id,

                            company_id,

                            room_id,

                            day,

                            start_time,

                            end_time,

                            panel_id,

                            "SCHEDULED"
                        )
                    )


                    return True


    return False


def generate_schedule():

    connection = get_connection()


    try:

        print(
            "\n========================================"
        )

        print(
            "OPTIMIZED PLACEMENT SCHEDULER"
        )

        print(
            "========================================\n"
        )


        # Clear old schedule

        connection.execute(
            "DELETE FROM interviews"
        )


        connection.commit()


        # Get requests

        requests = (
            get_interview_requests(
                connection
            )
        )


        print(
            "Total interview requests: "
            + str(len(requests))
        )


        # Prioritize

        requests = sort_requests(
            requests
        )


        scheduled = 0

        unscheduled = 0

        total = len(requests)


        # Schedule

        for index, request in enumerate(
            requests,
            start=1
        ):


            if schedule_interview(
                connection,
                request
            ):

                scheduled += 1

            else:

                unscheduled += 1


            if index % 250 == 0:

                connection.commit()


                print(
                    "Processed "
                    + str(index)
                    + "/"
                    + str(total)
                    + " | Scheduled: "
                    + str(scheduled)
                    + " | Unscheduled: "
                    + str(unscheduled)
                )


        connection.commit()


        percentage = 0


        if total > 0:

            percentage = (
                scheduled
                / total
            ) * 100


        print(
            "\n========================================"
        )

        print(
            "SCHEDULING COMPLETED"
        )

        print(
            "========================================"
        )

        print(
            "Total requests : "
            + str(total)
        )

        print(
            "Scheduled      : "
            + str(scheduled)
        )

        print(
            "Unscheduled    : "
            + str(unscheduled)
        )

        print(
            "Success rate   : "
            + f"{percentage:.2f}%"
        )

        print(
            "========================================\n"
        )


        return {

            "total": total,

            "scheduled": scheduled,

            "unscheduled":
                unscheduled,

            "percentage":
                percentage

        }


    except Exception as error:

        connection.rollback()

        print(
            "Scheduler error: "
            + str(error)
        )

        raise


    finally:

        connection.close()


if __name__ == "__main__":

    generate_schedule()