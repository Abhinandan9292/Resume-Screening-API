from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import sqlite3
import fitz  # PyMuPDF for AI Parsing
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- CORS MIDDLEWARE (The Handshake Fix) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE HELPER ---
def get_db():
    # This connects Python to your SQLite database file
    conn = sqlite3.connect('recruitment.db', timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

# --- DATABASE INITIALIZATION ---
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # Updated Table with Skills, Bio, and Is_Placed
    cursor.execute('''CREATE TABLE IF NOT EXISTS Students 
        (ID INTEGER PRIMARY KEY AUTOINCREMENT, FName TEXT, LName TEXT, Email TEXT UNIQUE, 
         Password TEXT, CGPA REAL, Github TEXT, Skills TEXT, Bio TEXT, Is_Placed BOOLEAN DEFAULT 0)''')
    conn.commit()
    conn.close()

# Run the DB initialization on startup
init_db()

# --- DATA MODELS ---
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

# --- ENDPOINTS ---

@app.post("/ai_parse")
async def ai_parse(file: UploadFile = File(...)):
    contents = await file.read()
    doc = fitz.open(stream=contents, filetype="pdf")
    text = "".join([page.get_text() for page in doc])
    # Keyword extraction logic
    keywords = ["python", "cpp", "java", "sql", "react", "ml", "ai", "dsa", "aiml"]
    found = [k for k in keywords if k in text.lower()]
    return {"suggested_skills": ", ".join(found), "bio_preview": text[:200]}

@app.post("/register_student")
def register(s: StudentData):
    conn = get_db()
    hashed_pw = pwd_context.hash(s.password)
    try:
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO Students (FName, LName, Email, Password, CGPA, Github, Skills, Bio) 
                          VALUES (?,?,?,?,?,?,?,?)""", 
                       (s.first_name, s.last_name, s.email, hashed_pw, s.cgpa, s.github_link, s.skills, s.bio))
        conn.commit()
        return {"status": "success"}
    except Exception as e:
        # If the email already exists, it will show this error!
        return {"status": "error", "message": str(e)}
    finally: 
        conn.close()

@app.post("/login")
def login(data: LoginData):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Students WHERE Email = ?", (data.email,))
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
        cursor.execute("SELECT * FROM Students WHERE Is_Placed = 0 AND Skills LIKE ?", (f"%{skills}%",))
    else:
        cursor.execute("SELECT * FROM Students WHERE Is_Placed = 0")
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results

@app.post("/mark_placed/{student_id}")
def mark_placed(student_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE Students SET Is_Placed = 1 WHERE ID = ?", (student_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}