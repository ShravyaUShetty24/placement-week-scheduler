from flask import (
    Flask,
    render_template,
    request,
    jsonify
)

from config import SECRET_KEY
from database.db import initialize_database, get_connection

from scheduler.replan import replan


app = Flask(__name__)

app.config["SECRET_KEY"] = SECRET_KEY


# ============================================================
# DATABASE
# ============================================================

initialize_database()


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    connection = get_connection()

    try:

        companies = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM companies
            """
        ).fetchone()["count"]


        students = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM students
            """
        ).fetchone()["count"]


        rooms = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM rooms
            """
        ).fetchone()["count"]


        total_requests = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM shortlists
            """
        ).fetchone()["count"]


        scheduled = connection.execute(
            """
            SELECT COUNT(*) AS count
            FROM interviews
            WHERE status = 'SCHEDULED'
            """
        ).fetchone()["count"]


        unscheduled = (
            total_requests - scheduled
        )


        if total_requests > 0:

            scheduling_percentage = (
                scheduled / total_requests
            ) * 100

        else:

            scheduling_percentage = 0


        return render_template(
            "dashboard.html",

            companies=companies,

            students=students,

            rooms=rooms,

            total_requests=total_requests,

            scheduled=scheduled,

            unscheduled=unscheduled,

            scheduling_percentage=round(
                scheduling_percentage,
                2
            )
        )

    finally:

        connection.close()


# ============================================================
# SCHEDULE
# ============================================================

@app.route("/schedule")
def schedule():

    connection = get_connection()

    try:

        interviews = connection.execute(
            """
            SELECT

                interviews.id,

                interviews.day,

                interviews.start_time,

                interviews.end_time,

                interviews.panel_id,

                students.student_code,

                students.name AS student_name,

                students.cgpa,

                students.branch,

                companies.name AS company_name,

                companies.priority,

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

                interviews.start_time,

                interviews.room_id
            """
        ).fetchall()


        return render_template(
            "schedule.html",
            interviews=interviews
        )

    finally:

        connection.close()


# ============================================================
# DISRUPTIONS PAGE
# ============================================================

@app.route("/disruptions")
def disruptions():

    connection = get_connection()

    try:

        companies = connection.execute(
            """
            SELECT
                id,
                name,
                panel_count
            FROM companies
            ORDER BY name
            """
        ).fetchall()


        students = connection.execute(
            """
            SELECT
                id,
                student_code,
                name
            FROM students
            ORDER BY student_code
            """
        ).fetchall()


        rooms = connection.execute(
            """
            SELECT
                id,
                name
            FROM rooms
            ORDER BY id
            """
        ).fetchall()


        return render_template(
            "disruptions.html",

            companies=companies,

            students=students,

            rooms=rooms
        )

    finally:

        connection.close()


# ============================================================
# REPLAN API
# ============================================================

@app.route(
    "/api/replan",
    methods=["POST"]
)
def api_replan():

    try:

        data = request.get_json()


        if not data:

            return jsonify({
                "success": False,
                "message":
                    "No disruption data received."
            }), 400


        disruption_type = data.get(
            "disruption_type"
        )


        company_id = data.get(
            "company_id"
        )


        panel_id = data.get(
            "panel_id"
        )


        student_id = data.get(
            "student_id"
        )


        room_id = data.get(
            "room_id"
        )


        new_arrival_time = data.get(
            "new_arrival_time"
        )


        # ----------------------------------------------------
        # Convert IDs
        # ----------------------------------------------------

        if company_id:

            company_id = int(company_id)


        if panel_id:

            panel_id = int(panel_id)


        if student_id:

            student_id = int(student_id)


        if room_id:

            room_id = int(room_id)


        # ----------------------------------------------------
        # Allowed disruption types
        # ----------------------------------------------------

        allowed_types = [

            "company_late",

            "panel_dropped",

            "student_withdrawal",

            "room_unavailable"

        ]


        if disruption_type not in allowed_types:

            return jsonify({

                "success": False,

                "message":
                    "Invalid disruption type."

            }), 400


        # ----------------------------------------------------
        # Validate company late
        # ----------------------------------------------------

        if (
            disruption_type ==
            "company_late"
            and not company_id
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please select a company."

            }), 400


        # ----------------------------------------------------
        # Validate panel dropped
        # ----------------------------------------------------

        if (
            disruption_type ==
            "panel_dropped"
            and (
                not company_id
                or not panel_id
            )
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please select a panel."

            }), 400


        # ----------------------------------------------------
        # Validate student withdrawal
        # ----------------------------------------------------

        if (
            disruption_type ==
            "student_withdrawal"
            and not student_id
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please select a student."

            }), 400


        # ----------------------------------------------------
        # Validate room unavailable
        # ----------------------------------------------------

        if (
            disruption_type ==
            "room_unavailable"
            and not room_id
        ):

            return jsonify({

                "success": False,

                "message":
                    "Please select a room."

            }), 400


        # ----------------------------------------------------
        # Run replan
        # ----------------------------------------------------

        result = replan(

            disruption_type=
                disruption_type,

            company_id=
                company_id,

            panel_id=
                panel_id,

            student_id=
                student_id,

            room_id=
                room_id,

            new_arrival_time=
                new_arrival_time

        )


        return jsonify(result)


    except ValueError:

        return jsonify({

            "success": False,

            "message":
                "Invalid ID value received."

        }), 400


    except Exception as error:

        return jsonify({

            "success": False,

            "message":
                "Server error: " +
                str(error)

        }), 500


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )