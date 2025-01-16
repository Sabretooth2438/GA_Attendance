# GA-Attendance
# Say Bye-Bye! For The Old Way OF Takeing Attendance📝 With GA-Attendance You Well Be Able To Take Attendance In Our App In Less Than A Minute 

##  Overview

**Student Management:** Add, edit, and manage student details including names, IDs, and classes.

**Attendance Tracking:** Mark attendance for each class/session in real-time or retroactively.

**Reports and Analytics:**

* Daily, weekly, and monthly attendance reports.

* Individual and class-wide attendance statistics.

* Export reports to PDF or CSV.

**Notifications:** Notify students or guardians about attendance updates via email or SMS.

**Multi-User Roles:**

* Administrator: Manage users, settings, and reports.

* Educator: Track attendance for assigned classes.

* Student/Parent: View attendance records.

**Integration:** Sync data with existing Learning Management Systems (LMS)

## Installation

### Requirements

**Server:**

**Python (v3.8 or later)**

**Django (v4.0 or later)**

**PostgreSQL (or any preferred database)**

##  Steps

**1. Clone the repository:**

  **git clone**
  [GA_Attendance](https://github.com/Sabretooth2438/GA_Attendance)

**2.  Navigate to the project directory:**
```
cd attendance-app
```
**3. Set up a virtual environment:**
```
python3 -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
```
**4. Install dependencies:**
```
pip install -r requirements.txt
```
**5. Set up environment variables:**
```
SECRET_KEY=your_secret_key
DEBUG=True
DATABASE_URL=postgres://user:password@localhost:5432/attendance
```
**6. Apply migrations:**
```
python manage.py migrate
```
**7. Create a superuser:**
```
python manage.py createsuperuser
```
**8. Start the development server:**
```
python manage.py runserver
```
9. Access the application in your browser at http://127.0.0.1:8000.

##  Usage
**1. Admin Setup:**

* Log in as an administrator and configure user roles.

* Add classes and student data.

**2. Educators:**

* Log in to track and manage attendance for their assigned classes.

* Generate and export attendance reports.

**3. Students/Parents:**
*   View attendance records and receive notifications.