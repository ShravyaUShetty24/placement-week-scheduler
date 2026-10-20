import sqlite3
from datetime import datetime

from config import DATABASE_PATH


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def time_to_minutes(time_string):
    """
    Convert HH:MM into minutes from midnight.
    Example:
        09:30 -> 570
    """

    hours, minutes = map(
        int,
        time_string.split(":")
    )

    return hours * 60 + minutes


def times_overlap(
    start1,
    end1,
    start2,
    end2
):
    """
    Check whether two time ranges overlap.
    """

    start1 = time_to_minutes(start1)
    end1 = time_to_minutes(end1)

    start2 = time_to_minutes(start2)
    end2 = time_to_minutes(end2)

    return (
        start1 < end2
        and start2 < end1
    )


def is_student_available(
    student_id,
    day,
    start_time,
    end_time,
    connection=None
):
    """
    Check whether a student already has
    another interview during this period.
    """

    own_connection = False

    if connection is None:
        connection = get_connection()
        own_connection = True

    try:

        interviews = connection.execute(
            """
            SELECT start_time, end_time
            FROM interviews
            WHERE student_id = ?
            AND day = ?
            AND status = 'SCHEDULED'
            """,
            (
                student_id,
                day
            )
        ).fetchall()

        for interview in interviews:

            if times_overlap(
                start_time,
                end_time,
                interview["start_time"],
                interview["end_time"]
            ):
                return False

        return True

    finally:

        if own_connection:
            connection.close()


def is_room_available(
    room_id,
    day,
    start_time,
    end_time,
    connection=None
):
    """
    Check whether a room is free.
    """

    own_connection = False

    if connection is None:
        connection = get_connection()
        own_connection = True

    try:

        room = connection.execute(
            """
            SELECT available
            FROM rooms
            WHERE id = ?
            """,
            (room_id,)
        ).fetchone()

        if room is None:
            return False

        if room["available"] == 0:
            return False

        interviews = connection.execute(
            """
            SELECT start_time, end_time
            FROM interviews
            WHERE room_id = ?
            AND day = ?
            AND status = 'SCHEDULED'
            """,
            (
                room_id,
                day
            )
        ).fetchall()

        for interview in interviews:

            if times_overlap(
                start_time,
                end_time,
                interview["start_time"],
                interview["end_time"]
            ):
                return False

        return True

    finally:

        if own_connection:
            connection.close()


def is_panel_available(
    company_id,
    panel_id,
    day,
    start_time,
    end_time,
    connection=None
):
    """
    Check whether a company's interview panel
    is available during the requested period.
    """

    own_connection = False

    if connection is None:
        connection = get_connection()
        own_connection = True

    try:

        interviews = connection.execute(
            """
            SELECT start_time, end_time
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

        for interview in interviews:

            if times_overlap(
                start_time,
                end_time,
                interview["start_time"],
                interview["end_time"]
            ):
                return False

        return True

    finally:

        if own_connection:
            connection.close()


def is_company_available(
    company_id,
    start_time,
    connection=None
):
    """
    Check whether the company has arrived
    before the interview begins.
    """

    own_connection = False

    if connection is None:
        connection = get_connection()
        own_connection = True

    try:

        company = connection.execute(
            """
            SELECT arrival_time
            FROM companies
            WHERE id = ?
            """,
            (company_id,)
        ).fetchone()

        if company is None:
            return False

        arrival_minutes = time_to_minutes(
            company["arrival_time"]
        )

        interview_start_minutes = time_to_minutes(
            start_time
        )

        return interview_start_minutes >= arrival_minutes

    finally:

        if own_connection:
            connection.close()


def can_schedule(
    student_id,
    company_id,
    room_id,
    panel_id,
    day,
    start_time,
    end_time,
    connection=None
):
    """
    Perform all hard-constraint checks.

    Returns:
        True  -> interview can be scheduled
        False -> at least one constraint fails
    """

    own_connection = False

    if connection is None:
        connection = get_connection()
        own_connection = True

    try:

        # 1. Student conflict
        if not is_student_available(
            student_id,
            day,
            start_time,
            end_time,
            connection
        ):
            return False

        # 2. Room conflict
        if not is_room_available(
            room_id,
            day,
            start_time,
            end_time,
            connection
        ):
            return False

        # 3. Panel conflict
        if not is_panel_available(
            company_id,
            panel_id,
            day,
            start_time,
            end_time,
            connection
        ):
            return False

        # 4. Company arrival
        if not is_company_available(
            company_id,
            start_time,
            connection
        ):
            return False

        return True

    finally:

        if own_connection:
            connection.close()