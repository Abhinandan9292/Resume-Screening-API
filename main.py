from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def setup_database():
    conn = sqlite3.connect('recruitment.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Students (
            Student_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            First_Name TEXT NOT NULL,
            Last_Name TEXT NOT NULL,
            Email TEXT UNIQUE NOT NULL,
            CGPA REAL NOT NULL,
            Github_Link TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM Students")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO Students (First_Name, Last_Name, Email, CGPA, Github_Link)
            VALUES ('Abhinandan', 'Wadhwa', 'abhinandan@example.com', 8.5, 'github.com/abhinandan92')
        ''')
    conn.commit()
    conn.close()

setup_database()

class Student(BaseModel):
    first_name: str
    last_name: str
    email: str
    cgpa: float
    github_link: str

@app.get("/")
def read_root():
    return {"message": "API is ALIVE! Database connected."}

@app.get("/students")
def get_students():
    conn = sqlite3.connect('recruitment.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/add_student")
def add_student(student: Student):
    try:
        conn = sqlite3.connect('recruitment.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO Students (First_Name, Last_Name, Email, CGPA, Github_Link)
            VALUES (?, ?, ?, ?, ?)
        ''', (student.first_name, student.last_name, student.email, student.cgpa, student.github_link))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"{student.first_name} added to the database!"}
    except sqlite3.IntegrityError:
        return {"status": "error", "message": "A student with this email already exists."}
    except Exception as e:
        return {"status": "error", "message": str(e)}