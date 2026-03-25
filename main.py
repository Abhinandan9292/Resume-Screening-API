from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import fitz
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛑 PASTE YOUR SUPABASE URI HERE! 
DB_URL = "postgresql://postgres.htjggenkueuyhunjkksy:Abhinandan%409252@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def get_db():
    # RealDictCursor ensures the database returns dictionaries (JSON) instead of tuples
    conn = psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)
    return conn

# --- 🏗️ CLOUD POSTGRESQL SCHEMA (3NF) ---
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Core Students Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Students (
         "ID" SERIAL PRIMARY KEY, 
         "FName" TEXT, "LName" TEXT, "Email" TEXT UNIQUE, 
         "Password" TEXT, "CGPA" REAL, "Github" TEXT, 
         "Bio" TEXT, "Is_Placed" INTEGER DEFAULT 0)''')
         
    # 2. Master Skills Table
    cursor.execute('''CREATE TABLE IF NOT EXISTS Skills (
         "ID" SERIAL PRIMARY KEY, 
         "Name" TEXT UNIQUE)''')
         
    # 3. Junction Table (Many-to-Many)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Student_Skills (
         "Student_ID" INTEGER REFERENCES Students("ID"), 
         "Skill_ID" INTEGER REFERENCES Skills("ID"),
         PRIMARY KEY ("Student_ID", "Skill_ID"))''')
         
    conn.commit()
    conn.close()

init_db()

class StudentData(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    cgpa: float
    github_link: str
    skills: str
    bio: str

class LoginData(BaseModel):
    email: str
    password: str

@app.post("/ai_parse")
async def ai_parse(file: UploadFile = File(...)):
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    keywords = ["python", "cpp", "java", "sql", "react", "ml", "ai", "dsa", "aiml", "javascript"]
    found = [k for k in keywords if k in text.lower()]
    return {"suggested_skills": ", ".join(found), "bio_preview": text[:300]}

@app.post("/register_student")
def register(s: StudentData):
    conn = get_db()
    hashed_pw = pwd_context.hash(s.password)
    try:
        cursor = conn.cursor()
        
        # Insert Student & use RETURNING "ID" (Postgres equivalent of lastrowid)
        cursor.execute("""INSERT INTO Students ("FName", "LName", "Email", "Password", "CGPA", "Github", "Bio") 
                          VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING "ID" """, 
                       (s.first_name, s.last_name, s.email, hashed_pw, s.cgpa, s.github_link, s.bio))
        student_id = cursor.fetchone()['ID']
        
        # Process Skills
        skill_list = [skill.strip().lower() for skill in s.skills.split(',')]
        for skill_name in skill_list:
            if not skill_name: continue
            
            # ON CONFLICT DO NOTHING is Postgres for INSERT OR IGNORE
            cursor.execute('INSERT INTO Skills ("Name") VALUES (%s) ON CONFLICT ("Name") DO NOTHING', (skill_name,))
            cursor.execute('SELECT "ID" FROM Skills WHERE "Name" = %s', (skill_name,))
            skill_id = cursor.fetchone()['ID']
            
            cursor.execute('INSERT INTO Student_Skills ("Student_ID", "Skill_ID") VALUES (%s,%s) ON CONFLICT DO NOTHING', (student_id, skill_id))
            
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback() # Critical for Postgres error recovery
        return {"status": "error", "message": str(e)}
    finally: 
        conn.close()

@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT Students.*, STRING_AGG(Skills."Name", ', ') as "Skills" 
        FROM Students 
        LEFT JOIN Student_Skills ON Students."ID" = Student_Skills."Student_ID" 
        LEFT JOIN Skills ON Student_Skills."Skill_ID" = Skills."ID" 
        WHERE Students."Email" = %s
        GROUP BY Students."ID"
    """, (data.email,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        if pwd_context.verify(data.password, user['Password']):
            user_dict = dict(user)
            del user_dict['Password'] 
            return {"status": "success", "user": user_dict}
    return {"status": "error", "message": "Invalid Email or Password"}

@app.get("/search")
def search(skills: str = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if skills:
        cursor.execute("""
            SELECT Students.*, STRING_AGG(Skills."Name", ', ') as "Skills" 
            FROM Students 
            LEFT JOIN Student_Skills ON Students."ID" = Student_Skills."Student_ID" 
            LEFT JOIN Skills ON Student_Skills."Skill_ID" = Skills."ID" 
            WHERE Students."Is_Placed" = 0 AND Students."ID" IN (
                SELECT "Student_ID" FROM Student_Skills 
                JOIN Skills ON Student_Skills."Skill_ID" = Skills."ID" 
                WHERE Skills."Name" ILIKE %s
            )
            GROUP BY Students."ID"
        """, (f"%{skills.lower()}%",)) # ILIKE is Postgres for case-insensitive LIKE
    else:
        cursor.execute("""
            SELECT Students.*, STRING_AGG(Skills."Name", ', ') as "Skills" 
            FROM Students 
            LEFT JOIN Student_Skills ON Students."ID" = Student_Skills."Student_ID" 
            LEFT JOIN Skills ON Student_Skills."Skill_ID" = Skills."ID" 
            WHERE Students."Is_Placed" = 0
            GROUP BY Students."ID"
        """)
        
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.post("/mark_placed/{student_id}")
def mark_placed(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE Students SET "Is_Placed" = 1 WHERE "ID" = %s', (student_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}
