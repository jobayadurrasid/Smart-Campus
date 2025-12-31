# 🎓 Smart Campus Management System – Backend

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Academic-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

A modern, scalable backend system for university campus management built with **FastAPI**. Features JWT authentication, role-based access control, and comprehensive RESTful APIs for academic operations.

# 🌐 Complete System Overview

### 🧭 System Overview (Conceptual)
```bash
                            +--------------------+
                            |      Users         |
                            |--------------------|
                            | Admin              |
                            | Teacher            |
                            | Student            |
                            +---------+----------+
                                      |
                                      | HTTP Requests (Login, Data, Actions)
                                      v
                            +-----------------------------+
                            |        Frontend (Vue.js)    |
                            |-----------------------------|
                            | - Login & Dashboard         |
                            | - Role-based UI             |
                            | - API Calls (Axios)         |
                            +-------------+---------------+
                                          |
                                          | REST API (JSON)
                                          v
                            +------------------------------------+
                            |        Backend (FastAPI)            |
                            |------------------------------------|
                            | - Authentication (JWT)              |
                            | - Role-Based Access Control         |
                            | - Business Logic                    |
                            | - API Endpoints                     |
                            +-------------+----------------------+
                                          |
                                          | ORM (SQLAlchemy)
                                          v
                            +-----------------------------+
                            |        Database (SQLite)    |
                            |-----------------------------|
                            | - Users                     |
                            | - Courses                   |
                            | - Enrollments               |
                            | - Schedules                 |
                            +-----------------------------+
        
```

### 🧠 System Overview (Technical / Developer View)
```bash
                    Client (Browser)
                        |
                        | 1. Login / API Request
                        |    Authorization: Bearer <JWT>
                        v
                    Frontend (Vue.js)
                        |
                        | 2. Axios HTTP Requests
                        v
                    FastAPI Application
                        |
                        |-- Auth Layer
                        |     - Password Hashing
                        |     - JWT Token Generation
                        |     - Token Validation
                        |
                        |-- API Layer
                        |     - Admin Routes
                        |     - Teacher Routes
                        |     - Student Routes
                        |
                        |-- Business Logic
                        |     - Course Management
                        |     - Schedule Management
                        |
                        |-- Data Access Layer
                        |     - CRUD Operations
                        |
                        v
                    Database (SQLite)

```


## ✨ Features

- **🔐 Secure Authentication**: JWT-based auth with bcrypt password hashing
- **👥 Role-Based Access**: Admin, Faculty, Student, and Staff roles
- **📊 Academic Management**: Courses, enrollments, grades, and schedules
- **🏢 Campus Operations**: Resource management and announcements
- **📱 RESTful API**: Well-documented endpoints with Swagger UI
- **💾 Database Ready**: SQLAlchemy ORM with SQLite (dev) / PostgreSQL (prod)
- **🌐 CORS Enabled**: Seamless integration with Vue.js frontend

## 🛠️ Technology Stack

| Component | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **Language** | Python 3.10+ |
| **Database** | SQLite (Development) |
| **ORM** | SQLAlchemy 2.0 |
| **Authentication** | JWT (PyJWT) + Passlib (bcrypt) |
| **Validation** | Pydantic v2 |
| **Environment** | python-dotenv |
| **CORS** | FastAPI CORS Middleware |

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/smart-campus-backend.git
    cd backend
    ```


2. **Environment setup**
    ```bash
    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate
    
    # Windows
    python -m venv venv
    venv\Scripts\activate
    ```
3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Start backend server**
    ```bash
    uvicorn main:app --reload
    ```

5. **Frontend setup**
    ```bash
    # Navigate to frontend directory (in a new terminal)
    cd ../frontend
    
    # Install Node.js dependencies
    npm install
    
    # Start frontend development server
    npm run dev
    ```
    
## 🔐 Authentication Overview

### 🔒 **Authentication Flow**
- Users authenticate using **username or email** and **password**
- Passwords are **securely hashed** using bcrypt algorithm before storage
- **JWT (JSON Web Tokens)** access tokens are issued after successful login
- Tokens are **validated on every protected request** via Authorization header
- **Role-based access control (RBAC)** is enforced at the API level

### 🛡️ **Security Features**
- **Password Security**: Passwords are hashed with bcrypt (salt + pepper)
- **Token Security**: JWT tokens are signed with HS256 algorithm
- **Token Expiry**: Access tokens expire (configurable, default: 30 minutes)
- **Refresh Tokens**: Long-lived refresh tokens for seamless re-authentication
- **Input Validation**: All user inputs are validated using Pydantic schemas

### 👮 **Role-Based Access Control**
| Role | Permissions | Access Level |
|------|-------------|--------------|
| **Admin** | Full system access, user management, configuration | Highest |
| **Faculty** | Course management, grading, student view | High |
| **Student** | Course enrollment, grade viewing, profile management | Medium |
| **Staff** | Administrative tasks, resource management | Medium |

---

## 🚀 Important Notes

### 🗄️ **Database Configuration**
- **SQLite** is used **only for development and testing**
- For production, use **PostgreSQL** or **MySQL**
- Database connection string should be configured in environment variables

### ⚙️ **Environment Configuration**
- Environment variables **should be configured** in a `.env` file
- **Never commit** `.env` files to version control
- Use `.env.example` as a template for required variables

### 🔧 **Development Mode**
- The server runs in **auto-reload mode** during development
- Changes to code are **automatically detected** and server restarts
- **Debug mode** is enabled for detailed error messages
- **CORS** is configured to allow frontend development server origins

### 🎯 **Development Best Practices**
1. **Always use virtual environments** for dependency isolation
2. **Follow PEP 8** coding standards for Python code
3. **Write comprehensive tests** for all endpoints
4. **Use Git** for version control with meaningful commit messages
5. **Document your code** with docstrings and comments

### ⚠️ **Security Considerations**
1. **Never expose** `.env` files or secret keys
2. **Validate all inputs** on both frontend and backend
3. **Implement rate limiting** for authentication endpoints
4. **Use HTTPS** in production environments
5. **Regularly update** dependencies for security patches

---



### 🔬 **Academic Focus**
- Software Engineering & System Design
- Web Application Development
- Database Management Systems
- Cybersecurity & Authentication Systems
- Full-Stack Development

### 🎯 **Project Goals**
This project demonstrates practical implementation of:
- RESTful API design with FastAPI
- Secure authentication systems
- Database modeling with SQLAlchemy
- Role-based access control
- Professional software development practices

---

## 📄 License

### 📜 **Usage Rights**
This project is developed **for educational and academic purposes only**.

### ⚖️ **License Terms**
1. **Academic Use**: Free to use for educational and research purposes
2. **Commercial Use**: Not permitted without explicit authorization
3. **Modification**: Allowed for learning and academic projects
4. **Distribution**: Allowed with proper attribution
5. **Attribution**: Required for any derivative works

### 📚 **Academic Integrity**
- This project should be used as a **learning resource**
- **Do not submit** this work as your own without significant modification
- **Always cite** the original source when using code
- **Respect** your institution's academic integrity policies


---

## 🤝 **Acknowledgments**

### 🙏 **Special Thanks**
- **FastAPI** community for excellent documentation and support
- University faculty and mentors for guidance
- Open source contributors whose work made this project possible
- Peer reviewers and testers for valuable feedback

### 📚 **Learning Resources**
This project was built with reference to:
- FastAPI official documentation
- OWASP security guidelines
- REST API best practices
- Software engineering principles

---




### 🎓 **Happy Coding & Best Wishes for Your Academic Journey!**

*"Education is the most powerful weapon which you can use to change the world." - Nelson Mandela*


---
## 👨‍💻 Author

**Jobayadur Rasid**

---
