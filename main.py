from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import fitz
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DB_URL = "postgresql://postgres.htjggenkueuyhunjkksy:Abhinandan%409252@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def get_db():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
         id SERIAL PRIMARY KEY, 
         first_name TEXT, 
         middle_name TEXT,
         last_name TEXT, 
         email TEXT UNIQUE, 
         password TEXT, 
         cgpa REAL, 
         github TEXT, 
         bio TEXT, 
         is_placed INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS skills (
         id SERIAL PRIMARY KEY, 
         name TEXT UNIQUE)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS student_skills (
         student_id INTEGER REFERENCES students(id), 
         skill_id INTEGER REFERENCES skills(id),
         PRIMARY KEY (student_id, skill_id))''')
    conn.commit()
    conn.close()

init_db()

class StudentData(BaseModel):
    first_name: str
    middle_name: Optional[str] = None
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

class UpdateProfileData(BaseModel):
    student_id: int
    new_cgpa: float
    new_skills: str


class JobCreate(BaseModel):
    job_title: str
    company_name: str  # <-- ADDED
    salary: str        # <-- ADDED
    job_description: str
    required_exp: float
    location: str
    recruiter_id: int = 1# Hardcoded to 1 for the MVP

class RecruiterLogin(BaseModel):
    email: str
    access_code: str

class RecruiterCreate(BaseModel):
    company_name: str
    email: str
    access_code: str



@app.post("/ai_parse")
async def ai_parse(file: UploadFile = File(...)):
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    keywords = ["python", "cpp", "java", "sql", "react", "ml", "ai", "dsa", "javascript"]
    found = [k for k in keywords if k in text.lower()]
    return {"suggested_skills": ", ".join(found), "bio_preview": text[:300]}

@app.post("/register_student")
def register(s: StudentData):
    conn = get_db()
    hashed_pw = pwd_context.hash(s.password)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (first_name, middle_name, last_name, email, password, cgpa, github, bio)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (s.first_name, s.middle_name, s.last_name, s.email, hashed_pw, s.cgpa, s.github_link, s.bio))
        student_id = cursor.fetchone()['id']
        skill_list = [skill.strip().lower() for skill in s.skills.split(',') if skill.strip()]
        for skill_name in skill_list:
            cursor.execute('INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING', (skill_name,))
            cursor.execute('SELECT id FROM skills WHERE name = %s', (skill_name,))
            skill_id = cursor.fetchone()['id']
            cursor.execute('INSERT INTO student_skills (student_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (student_id, skill_id))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, STRING_AGG(sk.name, ', ') as skills 
        FROM students s
        LEFT JOIN student_skills ss ON s.id = ss.student_id 
        LEFT JOIN skills sk ON ss.skill_id = sk.id 
        WHERE s.email = %s
        GROUP BY s.id
    """, (data.email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        if pwd_context.verify(data.password, user['password']):
            user_dict = dict(user)
            del user_dict['password'] 
            return {"status": "success", "user": user_dict}
    return {"status": "error", "message": "Invalid Email or Password"}

@app.post("/update_profile")
def update_profile(data: UpdateProfileData):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE students SET cgpa = %s WHERE id = %s', (data.new_cgpa, data.student_id))
        cursor.execute('DELETE FROM student_skills WHERE student_id = %s', (data.student_id,))
        skill_list = [skill.strip().lower() for skill in data.new_skills.split(',') if skill.strip()]
        for skill_name in skill_list:
            cursor.execute('INSERT INTO skills (name) VALUES (%s) ON CONFLICT (name) DO NOTHING', (skill_name,))
            cursor.execute('SELECT id FROM skills WHERE name = %s', (skill_name,))
            skill_id = cursor.fetchone()['id']
            cursor.execute('INSERT INTO student_skills (student_id, skill_id) VALUES (%s, %s) ON CONFLICT DO NOTHING', (data.student_id, skill_id))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        conn.rollback()
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
    finally:
        conn.close()

@app.get("/admin/all_students")
def get_admin_students():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM admin_master_list ORDER BY is_placed ASC, id DESC')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results



# 4. Analytics: Get Recruitment Statistics
@app.get("/admin/stats")
def get_recruitment_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recruitment_statistics')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# 5. Security: Get Audit Logs
# 5. Security: Get Audit Logs
@app.get("/admin/audit_logs")
def get_audit_logs():
    conn = get_db()
    cursor = conn.cursor()
    # Join with students table and convert UTC server time to IST (Indian Standard Time)
    cursor.execute('''
        SELECT 
            l.log_id, 
            s.first_name, 
            s.last_name, 
            l.action, 
            TO_CHAR(l.action_timestamp AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'DD Mon YYYY, HH12:MI AM') || ' IST' as timestamp 
        FROM placement_audit_logs l
        JOIN students s ON l.student_id = s.id
        ORDER BY l.action_timestamp DESC 
        LIMIT 10
    ''')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# 1. For Recruiters (Only Active/Unplaced, with Match Scoring)
@app.get("/recruiter/candidates")
def get_recruiter_candidates(skills: str = None):
    conn = get_db()
    cursor = conn.cursor()
    
    if skills:
        # Pass the skills string twice: once for the SELECT, once for the WHERE
        cursor.execute('''
            SELECT *, calculate_skill_match(skills, %s) as match_score 
            FROM recruiter_candidates 
            WHERE calculate_skill_match(skills, %s) > 0
            ORDER BY match_score DESC, cgpa DESC
        ''', (skills, skills))
    else:
        # Default view when no search is active
        cursor.execute('SELECT *, 0 as match_score FROM recruiter_candidates ORDER BY cgpa DESC')
        
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.post("/admin/mark_placed/{student_id}")
def mark_placed(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE students SET is_placed = 1 WHERE id = %s', (student_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}


@app.post("/recruiter/jobs")
def create_job(job: JobCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Now it uses job.recruiter_id from the frontend, not 1!
        cursor.execute('''
            INSERT INTO jobs (job_title, company_name, salary, job_description, required_exp, location, recruiter_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING job_id
        ''', (job.job_title, job.company_name, job.salary, job.job_description, job.required_exp, job.location, job.recruiter_id))
        new_job_id = cursor.fetchone()['job_id']
        conn.commit()
        return {"status": "success", "job_id": new_job_id, "message": "Job posted successfully"}
    except Exception as e:
        conn.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()

# 7. Student/Public: Get All Active Jobs
@app.get("/jobs")
def get_jobs():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs ORDER BY job_id DESC')
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results



# 8. Student: Apply for a Job
# 8. Student: Apply for a Job (No more hardcoded ID!)
@app.post("/student/apply/{job_id}")
def apply_for_job(job_id: int, student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Now it strictly uses the ID passed from the frontend
        cursor.execute('''
            INSERT INTO job_applications (job_id, student_id, application_status)
            VALUES (%s, %s, 'Applied')
        ''', (job_id, student_id))
        conn.commit()
        return {"status": "success", "message": "Application submitted successfully!"}
    except Exception as e:
        conn.rollback()
        # Blocks them from applying twice
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            return {"status": "error", "message": "You have already applied for this job."}
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()
# 9. Recruiter: View Applicants for their jobs
# --- 9. Recruiter: Get Applicants (CRASH FIXED) ---
# --- 9. Recruiter: Get Applicants (WITH SKILLS FIXED) ---
@app.get("/recruiter/applicants")
def get_applicants(recruiter_id: int):
    conn = get_db()
    cursor = conn.cursor()
    # We use string_agg to combine multiple skills into one comma-separated line
    cursor.execute('''
        SELECT 
            j.job_title, s.first_name, s.last_name, s.email, s.cgpa, 
            COALESCE(string_agg(sk.skill_name, ', '), '') AS skills,
            TO_CHAR(a.applied_on AT TIME ZONE 'UTC' AT TIME ZONE 'Asia/Kolkata', 'Mon DD, HH12:MI AM') as apply_date
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.job_id
        JOIN students s ON a.student_id = s.id
        LEFT JOIN student_skills ss ON s.id = ss.student_id
        LEFT JOIN skills sk ON ss.skill_id = sk.skill_id
        WHERE j.recruiter_id = %s
        GROUP BY j.job_title, s.first_name, s.last_name, s.email, s.cgpa, a.applied_on
        ORDER BY a.applied_on DESC
    ''', (recruiter_id,)) 
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


# 11. Admin: Onboard a New Corporate Recruiter
@app.post("/admin/add_recruiter")
def add_recruiter(recruiter: RecruiterCreate):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO recruiters (company_name, email, access_code)
            VALUES (%s, %s, %s) RETURNING recruiter_id
        ''', (recruiter.company_name, recruiter.email, recruiter.access_code))
        conn.commit()
        return {"status": "success", "message": f"Successfully onboarded {recruiter.company_name}!"}
    except Exception as e:
        conn.rollback()
        # Prevent duplicate accounts
        if "unique constraint" in str(e).lower() or "duplicate key" in str(e).lower():
            return {"status": "error", "message": "A recruiter with this email already exists."}
        return {"status": "error", "message": str(e)}
    finally:
        conn.close()



# --- Recruiter Secure Login ---
@app.post("/recruiter/login")
def login_recruiter(login_data: RecruiterLogin):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recruiters WHERE email = %s AND access_code = %s", (login_data.email, login_data.access_code))
    recruiter = cursor.fetchone()
    conn.close()
    if recruiter:
        return {"status": "success", "recruiter": dict(recruiter)}
    return {"status": "error", "message": "Invalid email or access code."}

