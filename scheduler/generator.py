import random
import sqlite3
from datetime import datetime, timedelta

from config import DATABASE_PATH


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

random.seed(42)

BRANCHES = [
    "CSE",
    "ISE",
    "ECE",
    "EEE",
    "ME",
    "AIML"
]

FIRST_NAMES = [
    "Aarav", "Aditya", "Akash", "Ananya", "Arjun",
    "Ashwin", "Bhavana", "Chaitra", "Deepak", "Divya",
    "Harish", "Kavya", "Kiran", "Manish", "Meghana",
    "Nandini", "Nikhil", "Pooja", "Pranav", "Rahul",
    "Rakesh", "Riya", "Rohit", "Sanjay", "Shreya",
    "Sneha", "Srinivas", "Tanvi", "Varun", "Vivek"
]

LAST_NAMES = [
    "Shetty", "Sharma", "Patil", "Rao", "Nair",
    "Reddy", "Kulkarni", "Bhat", "Gowda", "Joshi",
    "Iyer", "Menon", "Desai", "Naik", "Pillai"
]


# ---------------------------------------------------------
# Company definitions
# ---------------------------------------------------------

COMPANY_NAMES = [
    "TechNova Solutions",
    "CloudSphere Technologies",
    "DataBridge Systems",
    "NextGen Software",
    "InnoByte Technologies",
    "CodeCraft Solutions",
    "BluePeak Digital",
    "Vertex Systems",
    "QuantumSoft",
    "Nexora Technologies",
    "AlphaStack Solutions",
    "ByteWorks India",
    "LogicTree Technologies",
    "CoreVista Systems",
    "DigitalEdge Labs",
    "SoftMatrix Solutions",
    "AstraTech",
    "InfiniCode",
    "PrimeLogic Systems",
    "WebOrbit Technologies",
    "TechBridge Labs",
    "DataWave Solutions",
    "Skyline Software",
    "MindSpark Technologies",
    "AppVertex",
    "CodeSphere",
    "CloudMatrix",
    "Innovent Systems",
    "PixelStack Technologies",
    "RapidByte Solutions",
    "FutureGrid Labs",
    "SmartCore Technologies",
    "NetAxis Systems",
    "DevPoint Solutions",
    "StackVision Technologies"
]


# ---------------------------------------------------------
# Database connection
# ---------------------------------------------------------

def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ---------------------------------------------------------
# Generate companies
# ---------------------------------------------------------

def generate_companies(connection):

    cursor = connection.cursor()

    for index, company_name in enumerate(COMPANY_NAMES):

        # Create realistic priority distribution
        if index < 8:
            priority = "HIGH"
        elif index < 23:
            priority = "MEDIUM"
        else:
            priority = "LOW"

        cgpa_cutoff = random.choice([
            6.0,
            6.5,
            7.0,
            7.5,
            8.0
        ])

        interview_duration = random.choice([
            20,
            30,
            30,
            45,
            45,
            60
        ])

        panel_count = random.choice([1, 1, 2, 2, 3])

        # Companies arrive between 8:00 AM and 11:00 AM
        arrival_hour = random.choice([
            8,
            8,
            9,
            9,
            10,
            10,
            11
        ])

        arrival_time = f"{arrival_hour:02d}:00"

        cursor.execute(
            """
            INSERT INTO companies
            (
                name,
                priority,
                cgpa_cutoff,
                interview_duration,
                panel_count,
                arrival_time
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                company_name,
                priority,
                cgpa_cutoff,
                interview_duration,
                panel_count,
                arrival_time
            )
        )

    print("35 companies generated.")


# ---------------------------------------------------------
# Generate students
# ---------------------------------------------------------

def generate_students(connection):

    cursor = connection.cursor()

    for number in range(1, 801):

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        name = f"{first_name} {last_name}"

        cgpa = round(
            random.uniform(6.0, 9.8),
            2
        )

        branch = random.choice(BRANCHES)

        student_code = f"STU{number:03d}"

        cursor.execute(
            """
            INSERT INTO students
            (
                student_code,
                name,
                cgpa,
                branch
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                student_code,
                name,
                cgpa,
                branch
            )
        )

    print("800 students generated.")


# ---------------------------------------------------------
# Generate rooms
# ---------------------------------------------------------

def generate_rooms(connection):

    cursor = connection.cursor()

    for number in range(1, 21):

        cursor.execute(
            """
            INSERT INTO rooms
            (
                name,
                capacity,
                available
            )
            VALUES (?, ?, ?)
            """,
            (
                f"Room {number}",
                1,
                1
            )
        )

    print("20 rooms generated.")


# ---------------------------------------------------------
# Generate student-company shortlists
# ---------------------------------------------------------
def generate_shortlists(connection):

    cursor = connection.cursor()

    students = cursor.execute(
        """
        SELECT id, cgpa, branch
        FROM students
        """
    ).fetchall()

    companies = cursor.execute(
        """
        SELECT
            id,
            priority,
            cgpa_cutoff
        FROM companies
        """
    ).fetchall()

    shortlist_count = 0

    for student in students:

        student_id = student[0]
        student_cgpa = student[1]
        student_branch = student[2]

        # -------------------------------------------------
        # Find companies for which the student is eligible
        # -------------------------------------------------

        eligible_companies = []

        for company in companies:

            company_id = company[0]
            priority = company[1]
            cutoff = company[2]

            if student_cgpa < cutoff:
                continue

            # Base selection weight
            if priority == "HIGH":
                weight = 3
            elif priority == "MEDIUM":
                weight = 2
            else:
                weight = 1

            # Technical branches get a small advantage
            if student_branch in ["CSE", "ISE", "AIML"]:
                weight += 1

            eligible_companies.append(
                (
                    company_id,
                    weight
                )
            )

        if not eligible_companies:
            continue

        # -------------------------------------------------
        # Each student gets 1-3 companies
        # -------------------------------------------------

        number_of_companies = random.choices(
            [1, 2, 3],
            weights=[0.25, 0.55, 0.20],
            k=1
        )[0]

        number_of_companies = min(
            number_of_companies,
            len(eligible_companies)
        )

        # -------------------------------------------------
        # Weighted company selection
        # -------------------------------------------------

        selected = []

        available = eligible_companies.copy()

        for _ in range(number_of_companies):

            if not available:
                break

            company_ids = [
                item[0]
                for item in available
            ]

            weights = [
                item[1]
                for item in available
            ]

            selected_company = random.choices(
                company_ids,
                weights=weights,
                k=1
            )[0]

            selected.append(
                selected_company
            )

            available = [
                item
                for item in available
                if item[0] != selected_company
            ]

        # -------------------------------------------------
        # Save shortlists
        # -------------------------------------------------

        for company_id in selected:

            cursor.execute(
                """
                INSERT OR IGNORE INTO shortlists
                (
                    student_id,
                    company_id
                )
                VALUES (?, ?)
                """,
                (
                    student_id,
                    company_id
                )
            )

            shortlist_count += 1

    print(
        f"{shortlist_count} student-company shortlists generated."
    )
def generate_all_data():

    connection = get_connection()

    try:

        print("\nStarting data generation...\n")

        # Clear existing generated data
        cursor = connection.cursor()

        cursor.execute("DELETE FROM interviews")
        cursor.execute("DELETE FROM shortlists")
        cursor.execute("DELETE FROM students")
        cursor.execute("DELETE FROM companies")
        cursor.execute("DELETE FROM rooms")
        cursor.execute("DELETE FROM disruptions")

        connection.commit()

        # Generate fresh data
        generate_companies(connection)

        generate_students(connection)

        generate_rooms(connection)

        generate_shortlists(connection)

        connection.commit()

        print("\n===================================")
        print("DATA GENERATION COMPLETED")
        print("===================================")

    except Exception as error:

        connection.rollback()

        print(
            f"Error while generating data: {error}"
        )

        raise

    finally:

        connection.close()


# ---------------------------------------------------------
# Run generator
# ---------------------------------------------------------

if __name__ == "__main__":
    generate_all_data()