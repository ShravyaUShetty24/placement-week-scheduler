import sqlite3
import json
import os

from config import DATABASE_PATH

from scheduler.scheduler import (
    schedule_interview
)


SNAPSHOT_FILE = (
    "data/last_schedule.json"
)


def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# SAVE CURRENT SCHEDULE
# ============================================================

def save_schedule_snapshot(
    connection
):

    rows = connection.execute(
        """
        SELECT

            interviews.id,

            interviews.student_id,

            interviews.company_id,

            interviews.room_id,

            interviews.day,

            interviews.start_time,

            interviews.end_time,

            interviews.panel_id,

            interviews.status,

            students.student_code,

            students.name AS student_name,

            companies.name AS company_name,

            rooms.name AS room_name

        FROM interviews

        JOIN students
            ON students.id =
               interviews.student_id

        JOIN companies
            ON companies.id =
               interviews.company_id

        JOIN rooms
            ON rooms.id =
               interviews.room_id

        WHERE interviews.status =
              'SCHEDULED'

        ORDER BY

            interviews.day,

            interviews.start_time
        """
    ).fetchall()


    snapshot = []


    for row in rows:

        snapshot.append(
            dict(row)
        )


    os.makedirs(
        "data",
        exist_ok=True
    )


    with open(
        SNAPSHOT_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            snapshot,
            file,
            indent=4
        )


    return snapshot


# ============================================================
# GET INTERVIEW REQUEST
# ============================================================

def get_request(
    connection,
    student_id,
    company_id
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

        FROM students s

        JOIN shortlists sc
            ON sc.student_id = s.id

        JOIN companies c
            ON c.id = sc.company_id

        WHERE s.id = ?

        AND c.id = ?

        LIMIT 1
        """,
        (
            student_id,
            company_id
        )
    ).fetchone()


# ============================================================
# FIND AFFECTED INTERVIEWS
# ============================================================

def find_affected_interviews(
    connection,
    disruption_type,
    company_id=None,
    panel_id=None,
    student_id=None,
    room_id=None
):

    if disruption_type == "company_late":

        rows = connection.execute(
            """
            SELECT

                interviews.*,

                students.student_code,

                students.name AS student_name,

                companies.name AS company_name,

                rooms.name AS room_name

            FROM interviews

            JOIN students
                ON students.id =
                   interviews.student_id

            JOIN companies
                ON companies.id =
                   interviews.company_id

            JOIN rooms
                ON rooms.id =
                   interviews.room_id

            WHERE interviews.company_id = ?

            AND interviews.status =
                'SCHEDULED'

            ORDER BY

                interviews.day,

                interviews.start_time
            """,
            (
                company_id,
            )
        ).fetchall()


    elif disruption_type == "panel_dropped":

        rows = connection.execute(
            """
            SELECT

                interviews.*,

                students.student_code,

                students.name AS student_name,

                companies.name AS company_name,

                rooms.name AS room_name

            FROM interviews

            JOIN students
                ON students.id =
                   interviews.student_id

            JOIN companies
                ON companies.id =
                   interviews.company_id

            JOIN rooms
                ON rooms.id =
                   interviews.room_id

            WHERE interviews.company_id = ?

            AND interviews.panel_id = ?

            AND interviews.status =
                'SCHEDULED'

            ORDER BY

                interviews.day,

                interviews.start_time
            """,
            (
                company_id,

                panel_id
            )
        ).fetchall()


    elif disruption_type == "student_withdrawal":

        rows = connection.execute(
            """
            SELECT

                interviews.*,

                students.student_code,

                students.name AS student_name,

                companies.name AS company_name,

                rooms.name AS room_name

            FROM interviews

            JOIN students
                ON students.id =
                   interviews.student_id

            JOIN companies
                ON companies.id =
                   interviews.company_id

            JOIN rooms
                ON rooms.id =
                   interviews.room_id

            WHERE interviews.student_id = ?

            AND interviews.status =
                'SCHEDULED'

            ORDER BY

                interviews.day,

                interviews.start_time
            """,
            (
                student_id,
            )
        ).fetchall()


    elif disruption_type == "room_unavailable":

        rows = connection.execute(
            """
            SELECT

                interviews.*,

                students.student_code,

                students.name AS student_name,

                companies.name AS company_name,

                rooms.name AS room_name

            FROM interviews

            JOIN students
                ON students.id =
                   interviews.student_id

            JOIN companies
                ON companies.id =
                   interviews.company_id

            JOIN rooms
                ON rooms.id =
                   interviews.room_id

            WHERE interviews.room_id = ?

            AND interviews.status =
                'SCHEDULED'

            ORDER BY

                interviews.day,

                interviews.start_time
            """,
            (
                room_id,
            )
        ).fetchall()


    else:

        rows = []


    return rows


# ============================================================
# REPLAN
# ============================================================

def replan(
    disruption_type,
    company_id=None,
    panel_id=None,
    student_id=None,
    room_id=None,
    new_arrival_time=None
):

    connection = get_connection()


    try:

        # ----------------------------------------------------
        # STEP 1: Save old schedule
        # ----------------------------------------------------

        old_schedule = (
            save_schedule_snapshot(
                connection
            )
        )


        print(
            "Saved "
            + str(len(old_schedule))
            + " scheduled interviews."
        )


        # ----------------------------------------------------
        # STEP 2: Find affected interviews
        # ----------------------------------------------------

        affected = (
            find_affected_interviews(

                connection,

                disruption_type,

                company_id,

                panel_id,

                student_id,

                room_id

            )
        )


        if not affected:

            return {

                "success": False,

                "message":
                    "No scheduled interviews were "
                    "affected by this disruption.",

                "affected_count": 0,

                "changes": []

            }


        # ----------------------------------------------------
        # STEP 3: Company late
        # ----------------------------------------------------

        if (
            disruption_type ==
            "company_late"
            and
            company_id is not None
            and
            new_arrival_time
        ):

            connection.execute(
                """
                UPDATE companies

                SET arrival_time = ?

                WHERE id = ?
                """,
                (
                    new_arrival_time,

                    company_id
                )
            )


        # ----------------------------------------------------
        # STEP 4: Save requests
        # ----------------------------------------------------

        requests = []


        for interview in affected:

            request = get_request(

                connection,

                interview[
                    "student_id"
                ],

                interview[
                    "company_id"
                ]

            )


            if request:

                requests.append({

                    "request":
                        request,

                    "old":
                        dict(interview)

                })


        # ----------------------------------------------------
        # STEP 5: Delete affected interviews
        # ----------------------------------------------------

        affected_ids = [

            interview["id"]

            for interview in affected

        ]


        placeholders = ",".join(
            ["?"] *
            len(affected_ids)
        )


        connection.execute(

            "DELETE FROM interviews "
            "WHERE id IN ("
            + placeholders
            + ")",

            affected_ids

        )


        connection.commit()


        # ----------------------------------------------------
        # STEP 6: Student withdrawal
        # ----------------------------------------------------

        if (
            disruption_type ==
            "student_withdrawal"
        ):

            changes = []


            for item in requests:

                old = item["old"]


                changes.append({

                    "type":
                        "WITHDRAWN",

                    "student":
                        old["student_name"],

                    "company":
                        old["company_name"],

                    "old_day":
                        old["day"],

                    "old_time":
                        old["start_time"]
                        + " - "
                        + old["end_time"],

                    "old_room":
                        old["room_name"],

                    "new_day":
                        "-",

                    "new_time":
                        "Removed",

                    "new_room":
                        "-",

                    "new_panel":
                        "-"

                })


            connection.commit()


            return {

                "success": True,

                "message":
                    "Student withdrawal "
                    "processed successfully.",

                "affected_count":
                    len(affected),

                "changes":
                    changes

            }


        # ----------------------------------------------------
        # STEP 7: Re-schedule
        # ----------------------------------------------------

        changes = []


        for item in requests:

            request = item[
                "request"
            ]


            old = item[
                "old"
            ]


            blocked_room = None

            blocked_panel = None


            # Room unavailable

            if (
                disruption_type ==
                "room_unavailable"
            ):

                blocked_room = room_id


            # Panel dropped

            if (
                disruption_type ==
                "panel_dropped"
            ):

                blocked_panel = panel_id


            success = schedule_interview(

                connection,

                request,

                blocked_room_id=
                    blocked_room,

                blocked_panel_id=
                    blocked_panel

            )


            if success:

                new_interview = (
                    connection.execute(
                        """
                        SELECT

                            interviews.day,

                            interviews.start_time,

                            interviews.end_time,

                            interviews.room_id,

                            interviews.panel_id,

                            rooms.name AS room_name

                        FROM interviews

                        JOIN rooms
                            ON rooms.id =
                               interviews.room_id

                        WHERE
                            interviews.student_id = ?

                        AND
                            interviews.company_id = ?

                        AND
                            interviews.status =
                            'SCHEDULED'

                        ORDER BY
                            interviews.id DESC

                        LIMIT 1
                        """,
                        (
                            request[
                                "student_id"
                            ],

                            request[
                                "company_id"
                            ]
                        )
                    ).fetchone()
                )


                if new_interview:

                    changes.append({

                        "type":
                            "RESCHEDULED",

                        "student":
                            request[
                                "student_name"
                            ],

                        "company":
                            request[
                                "company_name"
                            ],

                        "old_day":
                            old["day"],

                        "old_time":
                            old["start_time"]
                            + " - "
                            + old["end_time"],

                        "old_room":
                            old["room_name"],

                        "new_day":
                            new_interview[
                                "day"
                            ],

                        "new_time":
                            new_interview[
                                "start_time"
                            ]
                            + " - "
                            + new_interview[
                                "end_time"
                            ],

                        "new_room":
                            new_interview[
                                "room_name"
                            ],

                        "new_panel":
                            new_interview[
                                "panel_id"
                            ]

                    })


                else:

                    changes.append({

                        "type":
                            "UNSCHEDULED",

                        "student":
                            request[
                                "student_name"
                            ],

                        "company":
                            request[
                                "company_name"
                            ],

                        "old_day":
                            old["day"],

                        "old_time":
                            old["start_time"]
                            + " - "
                            + old["end_time"],

                        "old_room":
                            old["room_name"],

                        "new_day":
                            "-",

                        "new_time":
                            "No feasible slot",

                        "new_room":
                            "-",

                        "new_panel":
                            "-"

                    })


            else:

                changes.append({

                    "type":
                        "UNSCHEDULED",

                    "student":
                        request[
                            "student_name"
                        ],

                    "company":
                        request[
                            "company_name"
                        ],

                    "old_day":
                        old["day"],

                    "old_time":
                        old["start_time"]
                        + " - "
                        + old["end_time"],

                    "old_room":
                        old["room_name"],

                    "new_day":
                        "-",

                    "new_time":
                        "No feasible slot",

                    "new_room":
                        "-",

                    "new_panel":
                        "-"

                })


        connection.commit()


        return {

            "success": True,

            "message":
                "Schedule replanned successfully.",

            "affected_count":
                len(affected),

            "changes":
                changes

        }


    except Exception as error:

        connection.rollback()


        print(
            "Replan error: "
            + str(error)
        )


        return {

            "success": False,

            "message":
                "Replan failed: "
                + str(error),

            "affected_count":
                0,

            "changes":
                []

        }


    finally:

        connection.close()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "\n========================================"
    )

    print(
        "REPLAN ENGINE TEST"
    )

    print(
        "========================================"
    )


    connection = get_connection()


    try:

        student = connection.execute(
            """
            SELECT DISTINCT

                interviews.student_id,

                students.student_code,

                students.name

            FROM interviews

            JOIN students
                ON students.id =
                   interviews.student_id

            WHERE interviews.status =
                  'SCHEDULED'

            ORDER BY
                interviews.student_id

            LIMIT 1
            """
        ).fetchone()


    finally:

        connection.close()


    if student is None:

        print(
            "No scheduled student interview was found."
        )

        print(
            "Run the scheduler first:"
        )

        print(
            "python -m scheduler.scheduler"
        )


    else:

        print(
            "Testing student withdrawal for:"
        )

        print(
            "Student ID   : "
            + str(
                student["student_id"]
            )
        )

        print(
            "Student Code : "
            + student["student_code"]
        )

        print(
            "Student Name : "
            + student["name"]
        )

        print(
            "\nRunning replan...\n"
        )


        result = replan(

            disruption_type=
                "student_withdrawal",

            student_id=
                student["student_id"]

        )


        print(
            "========================================"
        )

        print(
            "REPLAN RESULT"
        )

        print(
            "========================================"
        )

        print(
            "Success:",
            result["success"]
        )

        print(
            "Message:",
            result["message"]
        )

        print(
            "Affected interviews:",
            result.get(
                "affected_count",
                0
            )
        )


        for change in result.get(
            "changes",
            []
        ):

            print(
                "\nChange:"
            )


            for key, value in change.items():

                print(
                    "  "
                    + str(key)
                    + ": "
                    + str(value)
                )