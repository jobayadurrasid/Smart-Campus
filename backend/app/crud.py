#/backend/app/crud.py
import base64
import os
from sqlite3 import IntegrityError
from typing import List, Optional
import uuid
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from .email_service import send_welcome_email
from . import models, schemas,auth
from .utils import check_duplicate_face, generate_user_id
from .config import settings
from datetime import datetime, time, timedelta
import secrets
from deepface import DeepFace
import json


UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)



def authenticate_user(db: Session, email: str, password: str):
    """Add this if missing"""
    user = get_user_by_email(db, email=email)
    if not user or not auth.verify_password(password, user.hashed_password):
        return False
    return user
def get_user_by_email(db: Session, email: str):
    """Must exist for authentication"""
    return db.query(models.User).filter(models.User.email == email).first()



def create_user(db: Session, user: schemas.UserCreate, background_tasks: BackgroundTasks):
    try:
        if get_user_by_email(db, user.email):
            return JSONResponse(
                status_code=200, 
                content={
                    "status": "fail",
                    "message": "A user with this email already exists"
                    }
            )

        user_id = generate_user_id(
            enrollment_year=user.date_of_enrollment.year,
            department_code=user.department_code,
            role=user.role,
            db=db
        )

        image = user.image
        file_ext = image.filename.split(".")[-1]
        filename = f"{user_id}.{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(image.file.read())

        if check_duplicate_face(file_path, db):
            os.remove(file_path)  # Cleanup temp image
            return JSONResponse(
                status_code=200, 
                content={
                    "status": "fail",
                    "message": "A user with this face already exists"
                    }
            )
        # ➤ Extract face embedding
        representation = DeepFace.represent(
            img_path=file_path,
            model_name="VGG-Face",
            enforce_detection=True
        )[0]
        embedding = representation["embedding"]
        embedding_json = json.dumps(embedding)

        db_user = models.User(
            id=user_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            department_code=user.department_code,
            date_of_enrollment=user.date_of_enrollment,
            image_path=file_path,
            hashed_password=auth.get_password_hash("000000"),
            face_embedding=embedding_json
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        background_tasks.add_task(
            send_welcome_email,
            email=user.email,
            user_id=user_id,
            user_fullname=user.full_name,
            user_role=user.role
        )
        return JSONResponse(
                status_code=200, 
                content={
                    "status": "success",
                    "message": "Registration Successfull"
                    }
            )

    except Exception as e:
        db.rollback()
        raise e

    
    
def get_all_departments(db: Session):
    return db.query(models.Department).all()

def create_department(db: Session, department):
    db_department = models.Department(
        code=department.code,
        name=department.name,
        short_name=department.short_name
    )
    db.add(db_department)
    db.commit()
    db.refresh(db_department)
    return db_department

def get_department(db: Session, code: str):
    return db.query(models.Department).filter(models.Department.code == code).first()


def get_course(db: Session, course_id: str):
    return db.query(models.Course).filter(models.Course.id == course_id).first()


def create_course(db: Session, course: schemas.CourseCreate):
    # Generate course ID (e.g., CS-101)
    department = db.query(models.Department).filter(
        models.Department.code == course.department_code
    ).first()
    if not department:
        raise ValueError("Department not found")
    
    # Check for duplicates
    existing = db.query(models.Course).filter(
        models.Course.name == course.name,
        models.Course.semester == course.semester,
        models.Course.teacher_id == course.teacher_id
    ).first()
    if existing:
        raise ValueError("Course already exists with these parameters")

    # Get next course number
    max_num = db.query(func.max(models.Course.id)).filter(
        models.Course.department_code == course.department_code,
        models.Course.id.like(f"{department.short_name}-%")
    ).scalar()
    next_num = int(max_num.split('-')[1]) + 1 if max_num else 1
    course_id = f"{department.short_name}-{next_num:03d}"

    db_course = models.Course(
        id=course_id,
        **course.dict()
    )
    db.add(db_course)
    db.commit()
    return db_course



def create_schedule(db: Session, schedule: models.Schedule):
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule

def get_schedules(
    db: Session,
    academic_year: Optional[int] = None,
    semester: Optional[str] = None,
    teacher_id: Optional[str] = None,
    course_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    query = db.query(models.Schedule)
    
    if academic_year:
        query = query.filter(models.Schedule.academic_year_id == academic_year)
    if semester:
        query = query.filter(models.Schedule.semester == semester)
    if teacher_id:
        query = query.filter(models.Schedule.teacher_id == teacher_id)
    if course_id:
        query = query.filter(models.Schedule.course_id == course_id)
        
    return query.offset(skip).limit(limit).all()






def get_teacher_schedules(db: Session, teacher_id: str, academic_year: int, semester: str):
    return (
        db.query(models.Schedule)
        .join(models.Course, models.Schedule.course_id == models.Course.id)
        .filter(
            models.Course.teacher_id == teacher_id,
            models.Schedule.academic_year == academic_year,
            models.Schedule.semester == semester
        )
        .all()
    )

def get_student_schedules(db: Session, student_id: str, academic_year: int, semester: str):
    # Get the student record to find department_code
    student = db.query(models.User).filter(models.User.id == student_id).first()
    if not student:
        return []  # Student not found
    
    # Extract year (first 4 digits of student_id)
    year = student_id[:4]
    
    # Construct group_code as year + department_code
    group_code = f"{year}{student.department_code}"
    
    # Query schedules with this group_code, academic_year, and semester
    schedules = db.query(models.Schedule).filter(
        models.Schedule.group_code == group_code,
        models.Schedule.academic_year == academic_year,
        models.Schedule.semester == semester
    ).all()

    return schedules



def times_overlap(start1: time, end1: time, start2: time, end2: time) -> bool:
    return max(start1, start2) < min(end1, end2)



def update_group_schedule(
    db: Session,
    group_code: str,
    schedule_data: list,
    academic_year: int,
    semester: str
) -> bool:
    try:
        # Validate that the group_code is not empty (optional)
        if not group_code:
            return False

        # Fetch all courses related to this group by extracting year and dept from group_code
        # Assuming group_code format: "2025CSE"
        year = group_code[:4]
        dept_code = group_code[4:]

        # Find all students in this group
        students = db.query(models.User).filter(
            models.User.id.like(f"{year}%"),
            models.User.department_code == dept_code,
            models.User.role == "student"
        ).all()

        if not students:
            return False

        # Collect all enrolled course_ids for these students
        all_enrolled_course_ids = set()
        for student in students:
            all_enrolled_course_ids.update(e.course_id for e in student.enrollments)

        # Filter only schedule items for courses that all students are enrolled in
        valid_schedule_data = [
            item for item in schedule_data
            if item.course_id in all_enrolled_course_ids
        ]

        if not valid_schedule_data:
            return False

        for item in valid_schedule_data:
            course_id = item.course_id
            day = item.day_of_week
            start = item.start_time
            end = item.end_time
            course = db.query(models.Course).filter(models.Course.id == course_id).first()
            if not course or not course.teacher_id:
                raise ValueError(f"Invalid or unassigned course {course_id}")

            teacher_id = course.teacher_id

            # Check for teacher time conflict
            conflict = db.query(models.Schedule).join(models.Course).filter(
                models.Course.teacher_id == teacher_id,
                models.Schedule.academic_year == academic_year,
                models.Schedule.semester == semester,
                models.Schedule.day_of_week == day,
                models.Schedule.start_time < end,
                models.Schedule.end_time > start
            ).first()

            if conflict:
                day_name = schemas.DayOfWeek(conflict.day_of_week).name.capitalize()
                start_str = conflict.start_time.strftime("%H:%M").lstrip('0') or '0'
                end_str = conflict.end_time.strftime("%H:%M").lstrip('0') or '0'

                message = f"Teacher already has course at: {day_name} {start_str}-{end_str}"
                raise HTTPException(status_code=400, detail=message)
            # Check if an existing schedule needs to be updated
            existing = db.query(models.Schedule).filter_by(
                course_id=course_id,
                academic_year=academic_year,
                semester=semester,
                day_of_week=day,
                group_code=group_code
            ).first()

            if existing:
                existing.start_time = start
                existing.end_time = end
                db.add(existing)
            else:
                new_schedule = models.Schedule(
                    course_id=course_id,
                    academic_year=academic_year,
                    semester=semester,
                    day_of_week=day,
                    start_time=start,
                    end_time=end,
                    is_active=True,
                    group_code=group_code
                )
                db.add(new_schedule)

        db.commit()
        return True
    except HTTPException as http_exc:
        db.rollback()
        # re-raise without modification to preserve message but avoid nested status code
        raise http_exc
    except Exception as e:
        db.rollback()
        return False
        


def get_group_schedule(
    db: Session,
    group_code: str,
    academic_year: int,
    semester: str
) -> list[models.Schedule]:
    return db.query(models.Schedule).filter_by(
        group_code=group_code,
        academic_year=academic_year,
        semester=semester
    ).order_by(models.Schedule.day_of_week, models.Schedule.start_time).all()

