from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS so Vercel can talk to Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def setup_database():
    conn = sqlite3.connect('recruitment.db', timeout=20)
    try:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS Students 
            (ID INTEGER PRIMARY KEY AUTOINCREMENT, FName TEXT, LName TEXT, Email TEXT UNIQUE, CGPA REAL, Github TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS Jobs 
            (Job_ID INTEGER PRIMARY KEY AUTOINCREMENT, Title TEXT, Min_CGPA REAL)''')
        
        cursor.execute("SELECT COUNT(*) FROM Jobs")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO Jobs (Title, Min_CGPA) VALUES ('Data Scientist', 8.0)")
            cursor.execute("INSERT INTO Jobs (Title, Min_CGPA) VALUES ('Frontend Dev', 7.0)")
        conn.commit()
    finally:
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
    conn = sqlite3.connect('recruitment.db', timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Students")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

@app.post("/add_student")
def add_student(student: Student):
    conn = sqlite3.connect('recruitment.db', timeout=20)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Students (FName, LName, Email, CGPA, Github) VALUES (?,?,?,?,?)",
                       (student.first_name, student.last_name, student.email, student.cgpa, student.github_link))
        conn.commit()
        return {"status": "success"}
    except sqlite3.IntegrityError:
        return {"status": "error", "message": "Email already exists!"}
    finally:
        conn.close()

@app.get("/match/{job_id}")
def match_students(job_id: int):
    conn = sqlite3.connect('recruitment.db', timeout=20)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Jobs WHERE Job_ID = ?", (job_id,))
        job = cursor.fetchone()
        if not job: return {"error": "Job not found"}
        
        cursor.execute("SELECT * FROM Students WHERE CGPA >= ? ORDER BY CGPA DESC", (job['Min_CGPA'],))
        return {"job_title": job['Title'], "candidates": [dict(m) for m in cursor.fetchall()]}
    finally:
        conn.close()