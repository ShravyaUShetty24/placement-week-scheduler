import sqlite3

from config import DATABASE_PATH


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def time_to_minutes(time_string):
    hours, minutes = map(int, time_string.split(":"))
    return hours * 60 + minutes


def intervals_overlap(start1, end1, start2, end2):
    start1 = time_to_minutes(start1)
    end1 = time_to_minutes(end1)

    start2 = time_to_minutes(start2)
    end2 = time_to_minutes(end2)

    return start1 < end2 and start2 < end1


def check_student_conflicts(connection):
    conflicts = []

    rows = connection.execute(
        """
        SELECT
            student_id,
            day,
            start_time,
            end_time,
            id
        FROM interviews
        WHERE status = 'SCHEDULED'
        ORDER BY student_id, day, start_time
        """
    ).fetchall()

    for i in range(len(rows)):
        current = rows[i]

        for j in range(i + 1, len(rows)):
            other = rows[j]

            if current["student_id"] != other["student_id"]:
                break

            if current["day"] != other["day"]:
                continue

            if intervals_overlap(
                current["start_time"],
                current["end_time"],
                other["start_time"],
                other["end_time"]
            ):
                conflicts.append(
                    (
                        current["id"],
                        other["id"]
                    )
                )

    return conflicts


def check_room_conflicts(connection):
    conflicts = []

    rows = connection.execute(
        """
        SELECT
            room_id,
            day,
            start_time,
            end_time,
            id
        FROM interviews
        WHERE status = 'SCHEDULED'
        ORDER BY room_id, day, start_time
        """
    ).fetchall()

    for i in range(len(rows)):
        current = rows[i]

        for j in range(i + 1, len(rows)):
            other = rows[j]

            if current["room_id"] != other["room_id"]:
                break

            if current["day"] != other["day"]:
                continue

            if intervals_overlap(
                current["start_time"],
                current["end_time"],
                other["start_time"],
                other["end_time"]
            ):
                conflicts.append(
                    (
                        current["id"],
                        other["id"]
                    )
                )

    return conflicts


def check_panel_conflicts(connection):
    conflicts = []

    rows = connection.execute(
        """
        SELECT
            company_id,
            panel_id,
            day,
            start_time,
            end_time,
            id
        FROM interviews
        WHERE status = 'SCHEDULED'
        ORDER BY company_id, panel_id, day, start_time
        """
    ).fetchall()

    for i in range(len(rows)):
        current = rows[i]

        for j in range(i + 1, len(rows)):
            other = rows[j]

            if current["company_id"] != other["company_id"]:
                break

            if current["panel_id"] != other["panel_id"]:
                continue

            if current["day"] != other["day"]:
                continue

            if intervals_overlap(
                current["start_time"],
                current["end_time"],
                other["start_time"],
                other["end_time"]
            ):
                conflicts.append(
                    (
                        current["id"],
                        other["id"]
                    )
                )

    return conflicts


def calculate_metrics():
    connection = get_connection()

    try:
        total_shortlists = connection.execute(
            "SELECT COUNT(*) AS count FROM shortlists"
        ).fetchone()["count"]

        scheduled_interviews = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM interviews
            WHERE status = 'SCHEDULED'
            """
        ).fetchone()["count"]

        unscheduled = (
            total_shortlists - scheduled_interviews
        )

        if total_shortlists > 0:
            scheduling_percentage = (
                scheduled_interviews
                / total_shortlists
            ) * 100
        else:
            scheduling_percentage = 0

        student_conflicts = check_student_conflicts(
            connection
        )

        room_conflicts = check_room_conflicts(
            connection
        )

        panel_conflicts = check_panel_conflicts(
            connection
        )

        print("\n========================================")
        print("SCHEDULE VERIFICATION")
        print("========================================")

        print(
            f"Total interview requests : {total_shortlists}"
        )

        print(
            f"Scheduled interviews     : {scheduled_interviews}"
        )

        print(
            f"Unscheduled interviews   : {unscheduled}"
        )

        print(
            f"Scheduling percentage    : "
            f"{scheduling_percentage:.2f}%"
        )

        print("\nHARD CONSTRAINT CHECKS")

        print(
            f"Student conflicts        : "
            f"{len(student_conflicts)}"
        )

        print(
            f"Room conflicts           : "
            f"{len(room_conflicts)}"
        )

        print(
            f"Panel conflicts          : "
            f"{len(panel_conflicts)}"
        )

        print("========================================")

        if (
            len(student_conflicts) == 0
            and len(room_conflicts) == 0
            and len(panel_conflicts) == 0
        ):
            print(
                "\nSUCCESS: No hard constraint conflicts found!"
            )
        else:
            print(
                "\nWARNING: Conflicts were detected."
            )

        print("========================================\n")

        return {
            "total": total_shortlists,
            "scheduled": scheduled_interviews,
            "unscheduled": unscheduled,
            "scheduling_percentage": scheduling_percentage,
            "student_conflicts": len(student_conflicts),
            "room_conflicts": len(room_conflicts),
            "panel_conflicts": len(panel_conflicts)
        }

    finally:
        connection.close()


if __name__ == "__main__":
    calculate_metrics()