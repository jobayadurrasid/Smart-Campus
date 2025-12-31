from datetime import date, time
from enum import Enum
from typing import Any, Dict, Optional, List

from fastapi import File, UploadFile
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class Semester(str, Enum):
    FALL = "fall"
    SPRING = "spring"
    
    @classmethod
    def _missing_(cls, value):
        value_lower = value.lower()
        for member in cls:
            if member.value == value_lower:
                return member
        return None

class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# Enhanced User schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    department_code: str
    date_of_enrollment: date
    image:UploadFile = File(...) 

    class Config:
        orm_mode = True

class UserOut(UserBase):
    id: str
    role: UserRole
    department_code: str
    date_of_enrollment: date
    class Config:
        from_attributes = True

class DepartmentBase(BaseModel):
    code: str
    name: str
    short_name: str

class DepartmentCreate(BaseModel):
    code: str
    name: str

    @field_validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('Department code must be numeric')
        if len(v) != 3:
            raise ValueError('Department code must be 3 digits')
        return v
class DepartmentOut(BaseModel):
    code: str
    name: str

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str  # New field
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    token_type: str | None = None  # To distinguish token types

class CourseBase(BaseModel):
    name: str
    credits: int 
    department_code: str
    semester: Semester
    teacher_id: str | None = None


class CourseCreate(BaseModel):
    name: str
    credits: int
    department_code: str
    semester: str
    teacher_id: Optional[str] = None

class CourseOut(BaseModel):
    id: str
    name: str
    credits: int
    department_code: str
    semester: str
    teacher_id: Optional[str]
    
    class Config:
        from_attributes = True


class EnrollmentCreate(BaseModel):
    course_id: str
    student_id: str

class BulkEnrollmentCreate(BaseModel):
    course_id: str
    student_ids: List[str]


class DayOfWeek(str, Enum):
    monday = "0"
    tuesday = "1"
    wednesday = "2"
    thursday = "3"
    friday = "4"


class ScheduleBase(BaseModel):
    course_id: str
    academic_year: int
    semester: str
    day_of_week: str
    start_time: time  # Change from str to time
    end_time: time    # Change from str to time

class ScheduleCreate(ScheduleBase):
    pass

class Schedule(ScheduleBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True
        json_encoders = {
            time: lambda t: t.strftime("%H:%M")
        }


class GroupScheduleRequest(BaseModel):
    student_ids: List[str]
    academic_year: int
    semester: str

class GroupScheduleUpdate(BaseModel):
    group_code: str
    schedule: List[ScheduleCreate]
    academic_year: int
    semester: str

class ScheduleUpdate(BaseModel):
    schedule: List[ScheduleCreate]
    academic_year: int
    semester: str

class StudentList(BaseModel):
    student_ids: List[str]


class DepartmentDistribution(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]

class EnrollmentTrend(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]

class CourseDistribution(BaseModel):
    labels: List[str]
    datasets: List[Dict[str, Any]]

class RecentEnrollment(BaseModel):
    student_name: str
    course_name: str
    department: str
    enrollment_date: str

class UpcomingSchedule(BaseModel):
    course_name: str
    teacher_name: str
    day_of_week: int
    start_time: str
    end_time: str

class StatsResponse(BaseModel):
    totalStudents: int
    totalTeachers: int
    activeCourses: int
    currentEnrollments: int
    departmentDistribution: DepartmentDistribution
    enrollmentTrend: EnrollmentTrend
    courseDistribution: CourseDistribution
    recentEnrollments: List[RecentEnrollment]
    upcomingSchedules: List[UpcomingSchedule]