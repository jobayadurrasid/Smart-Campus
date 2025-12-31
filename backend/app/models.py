# /backend/app/model.py
from datetime import datetime
from pydantic import validator
from sqlalchemy import (
    JSON, Boolean, CheckConstraint, Column, DateTime, String, 
    Date, Integer, ForeignKey, Enum, Text, Time, UniqueConstraint
)
from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
from enum import Enum as PyEnum

class DayOfWeek(PyEnum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4


class SemesterType(PyEnum):
    FALL = "fall"
    SPRING = "spring"


class User(Base):
    __tablename__ = "users"
    
    id = Column(String(11), primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)
    department_code = Column(String(3), ForeignKey("departments.code"))
    date_of_enrollment = Column(Date)
    image_path = Column(String)
    face_embedding = Column(Text, nullable=True)
    
    # Relationships
    department = relationship("Department", back_populates="users")
    
    # Teaching relationship (for teachers)
    teaching_courses = relationship(
        "Course", 
        back_populates="teacher",
        foreign_keys="Course.teacher_id"
    )
    
    # Enrollment relationship (for students)
    enrollments = relationship("Enrollment", back_populates="student")


class Department(Base):
    __tablename__ = "departments"
    
    code = Column(String(5), primary_key=True)
    name = Column(String(50), unique=True)
    short_name = Column(String(5))
   
    users = relationship("User", back_populates="department")
    courses = relationship("Course", back_populates="department")


class Course(Base):
    __tablename__ = "courses"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String(100))
    credits = Column(Integer)
    department_code = Column(String(3), ForeignKey("departments.code"))
    semester = Column(String)
    teacher_id = Column(String, ForeignKey("users.id"))

    schedules = relationship("Schedule", back_populates="course")
    
    teacher = relationship(
        "User", 
        back_populates="teaching_courses",
        foreign_keys=[teacher_id]
    )
    
    enrollments = relationship("Enrollment", back_populates="course")
    department = relationship("Department", back_populates="courses")


class Enrollment(Base):
    __tablename__ = "enrollments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String, ForeignKey("users.id"))
    course_id = Column(String, ForeignKey("courses.id"))
    enrollment_date = Column(DateTime, default=datetime.now)
    
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")




class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    
    academic_year = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)
    day_of_week = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    # New column: group code for linking multiple schedule entries together
    group_code = Column(String(36), index=True, nullable=True)  # UUID recommended
    
    # Relationships
    course = relationship("Course", back_populates="schedules")
    
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_time_slot'),
        UniqueConstraint(
            'course_id', 'academic_year', 'semester', 'day_of_week', 'start_time',
            name='_course_schedule_unique'
        ),
    )



