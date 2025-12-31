#/backend/app/main.py
import csv
from datetime import date, timedelta, datetime
import io
from pathlib import Path
from typing import List, Optional
from fastapi.responses import FileResponse, StreamingResponse
from jose import jwt , JWTError
from fastapi import Body, FastAPI,APIRouter, Depends, Form, HTTPException, BackgroundTasks, Query, WebSocket, WebSocketDisconnect, status, UploadFile, File
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from . import models, schemas, crud
from .database import get_db, engine
from .email_service import send_password_reset_email, send_welcome_email
from .auth import add_to_blacklist, create_access_token, get_current_user, get_password_hash, oauth2_scheme # Add this import
from fastapi.security import OAuth2PasswordRequestForm
from .crud import authenticate_user 
from .config import settings
import cv2
import numpy as np
import os
from datetime import datetime
from sqlalchemy import and_, or_, func
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow GET, POST, etc.
    allow_headers=["*"],  # Allow all headers
)


@app.on_event("startup")
def startup_event():
    db: Session = next(get_db())
    admin = db.query(models.User).filter(models.User.role == "admin").first()
    if not admin:
        
        default_admin = models.User(
            id= "2020010001",
            full_name="admin",
            email="admin@campus.edu",
            hashed_password=get_password_hash("secret"),  # Use a hashed password in real apps
            role="admin",
            date_of_enrollment = date(2020, 5, 22),
            department_code = 00
        )
        db.add(default_admin)
        db.commit()
        print("✅ Default admin user created.")
    else:
        print("ℹ️ Admin user already exists.")

@app.post("/register")
async def register_user(
    background_tasks: BackgroundTasks,
    email: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    department_code: str = Form(...),
    date_of_enrollment: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        # Create the user data from the form data
        user_data = schemas.UserCreate(
            email=email,
            full_name=full_name,
            role=role,
            department_code=department_code,
            date_of_enrollment=date.fromisoformat(date_of_enrollment),
            image=image,  
        )
        
        # Now proceed to create the user
        response = crud.create_user(db=db,user=user_data, background_tasks=background_tasks)
        return response
    except ValueError as e:
        print(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Registration failed: {str(e)}"
        )

dept_router = APIRouter(prefix="/departments", tags=["departments"])

@dept_router.post("/", 
                 response_model=schemas.DepartmentOut,
                 status_code=status.HTTP_201_CREATED)
def create_department(
    department: schemas.DepartmentCreate, 
    db: Session = Depends(get_db)
):
    # Check if department exists
    db_department = crud.get_department(db, code=department.code)
    if db_department:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )
    return crud.create_department(db=db, department=department)

@dept_router.get("/", response_model=list[schemas.DepartmentOut])
def read_departments(db: Session = Depends(get_db)):
    return crud.get_all_departments(db)

@dept_router.get("/{code}", response_model=schemas.DepartmentOut)
def read_department(code: str, db: Session = Depends(get_db)):
    db_department = crud.get_department(db, code=code)
    if db_department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    return db_department
app.include_router(dept_router)


@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials",headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role,"id": user.id}  # Add role here
    )
    
    print(user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }



@app.get("/profile", response_model=schemas.UserOut)
async def read_users_me(
    current_user: models.User = Depends(get_current_user)
):
    print(f"current user: {current_user}")
    return current_user
@app.get("/image/{user_id}")
async def sendImage(user_id: str):
    base_dir = Path(__file__).parent.parent
    file_path = f"{base_dir}/uploaded_images/{user_id}.jpg"
    
    # Security check - prevent directory traversal
    try:
        file_path = Path(file_path).resolve()
        if not str(file_path).startswith(str(base_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
    except:
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if not os.path.exists(file_path):
        file_path = f"{base_dir}/send_images/person.jpg"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Default image not found")
    
    return FileResponse(
        file_path,
        media_type="image/jpeg",
        filename=f"{user_id}.jpg"
    )

@app.get("/teachers/search")
def search_teachers(
    department: str = Query(..., description="Department code"),
    query: str = Query(None),
    db: Session = Depends(get_db)
):
    teachers_query = db.query(
        models.User.id,
        models.User.full_name,
        models.User.email,
        models.User.department_code
    ).filter(
        models.User.role == "teacher",
        models.User.department_code == department
    )
    
    if query and len(query.strip()) >= 1:
        teachers_query = teachers_query.filter(
            models.User.full_name.ilike(f"%{query}%") | 
            models.User.id.ilike(f"%{query}%")
        )
    
    teachers = teachers_query.limit(20).all()
    
    # Convert to dictionary format
    return [{
        "id": t.id,
        "name": t.full_name,
        "email": t.email,
        "department_code": t.department_code
    } for t in teachers]

@app.get("/students/search")
def search_teachers(
    department: str = Query(..., description="Department code"),
    query: str = Query(None),
    db: Session = Depends(get_db)
):
    if (department!="-1"):
        students_query = db.query(
            models.User.id,
            models.User.full_name,
            models.User.email,
            models.User.department_code
        ).filter(
            models.User.role == "student",
            models.User.department_code == department
        )
    else:
        students_query = db.query(
            models.User.id,
            models.User.full_name,
            models.User.email,
            models.User.department_code
        ).filter(
            models.User.role == "student"
        )

    
    if query and len(query.strip()) >= 1:
        students_query = students_query.filter(
            models.User.full_name.ilike(f"%{query}%") | 
            models.User.id.ilike(f"%{query}%")
        )
    
    students = students_query.limit(20).all()
    
    # Convert to dictionary format
    return [{
        "id": s.id,
        "name": s.full_name,
        "email": s.email,
        "department_code": s.department_code
    } for s in students]

@app.get("/students/search-by-year")
def search_teachers(
    year: str = Query(..., description="year"),
    department: str = Query(None),
    db: Session = Depends(get_db)
):
    if (year!="-1"):
        students_query = db.query(
            models.User.id,
            models.User.full_name,
            models.User.email,
            
        ).filter(
            models.User.role == "student",
            models.User.department_code == department,
            models.User.id.ilike(f"%{year}%")
        )
    else:
        students_query = db.query(
            models.User.id,
            models.User.full_name,
            models.User.email,
            
        ).filter(
            models.User.role == "student",
            models.User.department_code == department
        )
    
    students = students_query.all()
    
    # Convert to dictionary format
    return [{
        "id": s.id,
        "name": s.full_name,
        "email": s.email,
    } for s in students]

course_router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)

@course_router.post("/createCouse", response_model=schemas.CourseOut)
def add_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
):
    try:
        return crud.create_course(db, course)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@course_router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: str,
    db: Session = Depends(get_db)
):
    # Check if course exists
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course with id {course_id} not found"
        )
    
    try:
        # Delete the course
        db.delete(db_course)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting course: {str(e)}"
        )
    
    return None  # 204 No Content response


@course_router.get("/getCourse", response_model=list[schemas.CourseOut])
def get_courses(db: Session = Depends(get_db)):
    courses = db.query(models.Course).all()  # Query the model class, not the schema
    return courses
@course_router.get("/getTeachersCourse/{teacher_id}", response_model=list[schemas.CourseOut])
def get_courses(teacher_id: str,db: Session = Depends(get_db)):
    courses = db.query(models.Course).filter(models.Course.teacher_id==teacher_id)  # Query the model class, not the schema
    return courses
@course_router.get("/getStudentsCourse/{student_id}", response_model=list[schemas.CourseOut])
def get_courses(student_id: str,db: Session = Depends(get_db)):
    course_ids = db.query(models.Enrollment.course_id).filter(
        models.Enrollment.student_id == student_id
    ).subquery()

    # Now query all Course objects with those IDs
    courses = db.query(models.Course).filter(models.Course.id.in_(course_ids)).all()
    return courses
@course_router.post("/common-courses", response_model=List[schemas.CourseOut])
def common_courses(data:schemas.StudentList, db: Session = Depends(get_db)):
    if not data.student_ids:
        return []

    # Get course_ids for each student
    course_sets = []
    for sid in data.student_ids:
        course_ids = db.query(models.Enrollment.course_id).filter(models.Enrollment.student_id == sid).all()
        course_ids = {cid[0] for cid in course_ids}
        course_sets.append(course_ids)

    # Find common course_ids
    common_ids = set.intersection(*course_sets) if course_sets else set()
    if not common_ids:
        return []

    # Fetch course details
    courses = db.query(models.Course).filter(models.Course.id.in_(common_ids)).all()
    return courses
app.include_router(course_router)


enrollment_router = APIRouter(
    prefix="/enrollments",
    tags=["enrollments"]
)

@enrollment_router.post("/")
async def create_enrollment(
    enrollment: schemas.EnrollmentCreate,
    db: Session = Depends(get_db)    
):

    
    # Check if already enrolled
    existing =db.query(models.Enrollment.id).filter(
            models.Enrollment.course_id == enrollment.course_id ,
            models.Enrollment.student_id == enrollment.student_id
        ).first()
    if existing:
        return {
        "check": "faild",
        "massage": "Student already enrolled"}
    db_enrollment = models.Enrollment(
        student_id = enrollment.student_id,
        course_id = enrollment.course_id
    )
    try:
        db.add(db_enrollment)
        db.commit()
    except:
        return {
        "check": "faild",
        "massage": "Enrollment Faild"}
    return {
        "check": "success",
        "massage": "Enrollment Successfull"}

@enrollment_router.post("/bulk", response_model=dict)
async def bulk_enroll(
    bulk_data: schemas.BulkEnrollmentCreate,
    db: Session = Depends(get_db)  
):
    
    enrolled = 0
    errors = []
    
    for student_id in bulk_data.student_ids:
        try:
                        
            # Check if already enrolled
            existing = db.query(models.Enrollment.id).filter(
                models.Enrollment.course_id == bulk_data.course_id,
                models.Enrollment.student_id == student_id).first()
            if existing:
                errors.append(f"Student {student_id} already enrolled")
                continue
            
            # Create enrollment
            db_enrollment = models.Enrollment(
                student_id = student_id,
                course_id = bulk_data.course_id
            )
            db.add(db_enrollment)
            db.commit()
            enrolled += 1
            
        except Exception as e:
            errors.append(f"Error enrolling {student_id}: {str(e)}")
    
    return {
        "message": f"Successfully enrolled {enrolled} students",
        "enrolled_count": enrolled,
        "errors": errors
    }

app.include_router(enrollment_router)


schedule_router = APIRouter(
    prefix="/schedules",
    tags=["schedules"]
)

@schedule_router.post("/group", response_model=List[schemas.Schedule])
def get_common_group_schedule(
    group_request: schemas.GroupScheduleRequest,
    db: Session = Depends(get_db)
):
    # Get common schedule for all students in the group
    schedules = crud.get_common_group_schedule(
        db,
        student_ids=group_request.student_ids,
        academic_year=group_request.academic_year,
        semester=group_request.semester
    )
    return schedules


@schedule_router.put("/group", status_code=200)
def update_group_schedule(
    group_request: schemas.GroupScheduleUpdate,
    db: Session = Depends(get_db)
):
    updated = crud.update_group_schedule(
        db,
        group_code=group_request.group_code,
        schedule_data=group_request.schedule,
        academic_year=group_request.academic_year,
        semester=group_request.semester
    )
    if not updated:
        raise HTTPException(status_code=400, detail="Failed to update group schedule")
    return {"message": "Group schedule updated successfully"}
@schedule_router.get("/group/{group_code}")
def fetch_group_schedule(
    group_code: str,
    academic_year: int,
    semester: str,
    db: Session = Depends(get_db)
):
    schedules = crud.get_group_schedule(db, group_code, academic_year, semester)
    return schedules
@schedule_router.get("/teacher/{teacher_id}", response_model=List[schemas.Schedule])
def get_teacher_schedule(
    teacher_id: str ,
    academic_year: int = Query(),
    semester: str = Query(),
    db: Session = Depends(get_db)
):
    schedules = crud.get_teacher_schedules(
        db,
        teacher_id=teacher_id,
        academic_year=academic_year,
        semester=semester
    )
    return schedules


@schedule_router.get("/student/{student_id}", response_model=List[schemas.Schedule])
def get_student_schedule(
    student_id: str,
    academic_year: int,
    semester: str,
    db: Session = Depends(get_db)
):
    schedules = crud.get_student_schedules(
        db,
        student_id=student_id,
        academic_year=academic_year,
        semester=semester
    )
    return schedules


app.include_router(schedule_router)


@app.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    try:
        # Total counts
        total_students = db.query(func.count(models.User.id)).filter(
            models.User.role == "student"
        ).scalar()
        
        total_teachers = db.query(func.count(models.User.id)).filter(
            models.User.role == "teacher"
        ).scalar()
        
        active_courses = db.query(func.count(models.Course.id)).join(
            models.Schedule
        ).filter(
            models.Schedule.is_active == True
        ).scalar()
        
        # For current enrollments, we'll use all enrollments
        # or filter by recent date if needed
        current_enrollments = db.query(func.count(models.Enrollment.id)).scalar()
        
        # Department distribution
        dept_data = db.query(
            models.Department.short_name,
            func.count(models.User.id).label("count")
        ).join(
            models.User, models.Department.code == models.User.department_code
        ).filter(
            models.User.role == "student"
        ).group_by(
            models.Department.short_name
        ).all()
        
        # Enrollment trend (last 6 months)
        six_months_ago = datetime.now() - timedelta(days=180)
        trend_data = db.query(
            extract('month', models.Enrollment.enrollment_date).label("month"),
            func.count(models.Enrollment.id).label("count")
        ).filter(
            models.Enrollment.enrollment_date >= six_months_ago
        ).group_by(
            extract('month', models.Enrollment.enrollment_date)
        ).order_by(
            extract('month', models.Enrollment.enrollment_date)
        ).all()
        
        # Course distribution
        course_data = db.query(
            models.Department.short_name,
            func.count(models.Course.id).label("count")
        ).join(
            models.Course, models.Department.code == models.Course.department_code
        ).group_by(
            models.Department.short_name
        ).all()
        
        # Recent enrollments (last 10)
        recent_enrolls = db.query(
            models.User.full_name.label("student_name"),
            models.Course.name.label("course_name"),
            models.Department.short_name.label("department"),
            models.Enrollment.enrollment_date
        ).select_from(
            models.Enrollment
        ).join(
            models.User, models.Enrollment.student_id == models.User.id
        ).join(
            models.Course, models.Enrollment.course_id == models.Course.id
        ).join(
            models.Department, models.Course.department_code == models.Department.code
        ).order_by(
            models.Enrollment.enrollment_date.desc()
        ).limit(10).all()
        
        # Upcoming schedules (active ones)


        today = datetime.now().weekday()  # 0=Monday, ..., 6=Sunday

        if today >= 5:  # Saturday or Sunday
            # Show schedules starting Monday to Friday (0 to 4)
            upcoming_days = [str(i) for i in range(0, 5)]
        else:
            # Show schedules from tomorrow till Friday (if today is Friday, no upcoming)
            upcoming_days = [str(i) for i in range(today + 1, 5)]

        # Now query with filter:
        upcoming_scheds = db.query(
            models.Course.name.label("course_name"),
            models.User.full_name.label("teacher_name"),
            models.Schedule.day_of_week,
            models.Schedule.start_time,
            models.Schedule.end_time
        ).join(
            models.Course, models.Schedule.course_id == models.Course.id
        ).join(
            models.User, models.Course.teacher_id == models.User.id
        ).filter(
            models.Schedule.is_active == True,
            models.Schedule.day_of_week.in_(upcoming_days)
        ).order_by(
            models.Schedule.day_of_week,
            models.Schedule.start_time
        ).limit(10).all()

        print(upcoming_scheds)
        return {
            "totalStudents": total_students or 0,
            "totalTeachers": total_teachers or 0,
            "activeCourses": active_courses or 0,
            "currentEnrollments": current_enrollments or 0,
            "departmentDistribution": {
                "labels": [dept.short_name for dept in dept_data],
                "datasets": [{
                    "label": "Students by Department",
                    "data": [dept.count for dept in dept_data],
                    "backgroundColor": [
                        '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e'
                    ]
                }]
            },
            "enrollmentTrend": {
                "labels": [f"Month {int(trend.month)}" for trend in trend_data],
                "datasets": [{
                    "label": "Enrollments",
                    "data": [trend.count for trend in trend_data],
                    "borderColor": '#10b981',
                    "backgroundColor": '#a7f3d0',
                    "tension": 0.3
                }]
            },
            "courseDistribution": {
                "labels": [course.short_name for course in course_data],
                "datasets": [{
                    "data": [course.count for course in course_data],
                    "backgroundColor": [
                        '#3b82f6', '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e'
                    ]
                }]
            },
            "recentEnrollments": [
                {
                    "student_name": enroll.student_name,
                    "course_name": enroll.course_name,
                    "department": enroll.department,
                    "enrollment_date": enroll.enrollment_date.isoformat()
                } for enroll in recent_enrolls
            ],
            "upcomingSchedules": [
                {
                    "course_name": sched.course_name,
                    "teacher_name": sched.teacher_name,
                    "day_of_week": sched.day_of_week,
                    "start_time": sched.start_time.strftime("%H:%M:%S"),
                    "end_time": sched.end_time.strftime("%H:%M:%S")
                } for sched in upcoming_scheds
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#==========================================================================================================
@app.get("/")
def home():
    return {"message": "Smart Campus API"}
