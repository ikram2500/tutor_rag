from fastapi import APIRouter, HTTPException, Depends 
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from  .model import StudentUser, TeacherUser 
from config.db import users_collection 
from .hash_utils import hash_password, verify_password


router = APIRouter()
security=HTTPBasic()



def authenticate(credentials:HTTPBasicCredentials=Depends(security)):
    """Authenticates a user using HTTP Basic Auth"""
    user_record=users_collection.find_one({"username":credentials.username})
    if not user_record or not verify_password(credentials.password, user_record["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {
        "username": user_record["username"],
        "fullname": user_record["fullname"],
        "email": user_record["email"],
        "role": user_record["role"],
    }



@router.post("/signup/student")
def signup_student(req: StudentUser):
    """Handles a student signup request."""
# Check if the username already exists in the database 
    if users_collection.find_one({"username": req.username}):
        raise HTTPException(status_code=400, detail="Username already exists") 
    #
    # hash the password before storing 
    hashed_password = hash_password(req.password)
    users_collection.insert_one({
            "fullname": req.fullname,
            "email": req.email,
            "username": req.username,
            "password": hashed_password,
            "role": "Student",
            "grade": req.grade,
            "school":req.school,
     })
    return{ "message": "Student user created successfully" }


@router.post("/signup/teacher")
def signup_teacher(req: TeacherUser):
    """Handles a teacher signup request."""
# Check if the username already exists in the database 
    if users_collection.find_one({"username": req.username}):
        raise HTTPException(status_code=400, detail="Username already exists") 
    
    # hash the password before storing 
    hashed_password = hash_password(req.password)
    users_collection.insert_one({
            "fullname": req.fullname,
            "email": req.email,
            "username": req.username, 
            "password": hashed_password,
            "role": "Teacher",
            "school":req.school    
     })
    return{ "message": "Teacher user created successfully" }


@router.get("/login")
def login(user:str=Depends(authenticate)):
    """Handles user login"""
    return {"message": f"welcome, {user}!"}