# client.py
import socket
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkFont
import matplotlib.pyplot as plt
import ast
from math import floor
from PIL import ImageTk, Image
import sqlite3
import requests
from bs4 import BeautifulSoup
from tkinter.scrolledtext import ScrolledText

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk
)


class Database:
    def __init__(self):
        self.create_tables()

    # init the tables
    def format_query(self, sql_query: str, values: tuple) -> list:
        if values:
            formatted_query = sql_query
            for value in values:
                for value1 in value:
                    formatted_query = formatted_query.replace('?', f"'{value1}'", 1)
            return formatted_query
        return sql_query

    def send_query(self, query, *args):
        query = self.format_query(query, args)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 65432))
        client_socket.sendall(query.encode())
        response = client_socket.recv(1024).decode()
        if response == '[]':
            return None
        if response[0] == "[":
            return ast.literal_eval(response)  # converts a string format return into a list of appropriate data
        return response

    def create_tables(self) -> None:
        self.send_query('''CREATE TABLE IF NOT EXISTS Users (
                                    ID INTEGER PRIMARY KEY,
                                    Username TEXT UNIQUE,
                                    Password TEXT,
                                    Privilege TEXT,
                                    DOB TEXT,
                                    Email TEXT,
                                    Phone TEXT,
                                    FName TEXT,
                                    LName TEXT
                                )''')

        self.send_query('''CREATE TABLE IF NOT EXISTS Courses (
                                    CourseID INTEGER PRIMARY KEY,
                                    CourseName TEXT,
                                    LOStudents INTEGER,
                                    Professor TEXT,
                                    RoomNumber TEXT
                                )''')

        self.send_query('''CREATE TABLE IF NOT EXISTS Assignments (
                                    AssignmentID INTEGER PRIMARY KEY,
                                    Name TEXT,
                                    Description TEXT,
                                    CourseID INTEGER,
                                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID)
                                )''')

        self.send_query('''CREATE TABLE IF NOT EXISTS Submissions (
                                    ID INTEGER PRIMARY KEY,
                                    AssignmentID INTEGER,
                                    SubmitterID INTEGER,
                                    Body TEXT,
                                    Grade INTEGER,
                                    FOREIGN KEY (AssignmentID) REFERENCES Assignments(AssignmentID),
                                    FOREIGN KEY (SubmitterID) REFERENCES Users(ID)
                                )''')

        self.send_query('''CREATE TABLE IF NOT EXISTS Enrollments (
                                    EnrollmentID INTEGER PRIMARY KEY,
                                    CourseID INTEGER,
                                    StudentID INTEGER,
                                    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID),
                                    FOREIGN KEY (StudentID) REFERENCES Users(ID)
                                )''')

    # add a user to the database
    def add_user(self, username: str, password: str, privilege: str, dob: str, email: str, phone: str, fname: str,
                 lname: str) -> None:
        self.send_query('''INSERT INTO Users (Username, Password, Privilege, DOB, Email, Phone, FName, LName)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (username, password, privilege, dob, email, phone, fname, lname))

    # Add a course to the database
    def add_course(self, course_name: str, professor: str, room_number: str) -> None:
        self.send_query('''INSERT INTO Courses (CourseName, Professor, RoomNumber) VALUES (?, ?, ?)''',
                        (course_name, professor, room_number))

    # return all courses for the given professor
    def get_courses_by_professor(self, professor: str) -> list:
        return self.send_query('''SELECT * FROM Courses WHERE Professor = ?''', (professor,))

    # add the given assignment into the assignments table
    def add_assignment(self, name: str, description: str, course_id: str) -> None:
        self.send_query('''INSERT INTO Assignments (Name, Description, CourseID) VALUES (?, ?, ?)''',
                        (name, description, course_id))

    # return all assignments for the course
    def get_assignments_by_course(self, course_id: str) -> list:
        return self.send_query('''SELECT * FROM Assignments WHERE CourseID = ?''', (course_id,))

    # add the given submission to the database
    def add_submission(self, assignment_id: str, submitter_id: str, body: str) -> None:
        self.send_query('''INSERT INTO Submissions (AssignmentID, SubmitterID, Body) VALUES (?, ?, ?)''',
                        (assignment_id, submitter_id, body))

    # return all submissions for the given assignment
    def get_submissions_by_assignment(self, assignment_id: str) -> list:
        return self.send_query('''SELECT * FROM Submissions WHERE AssignmentID = ?''', (assignment_id,))

    # return all submissions for the given student
    def get_student_submissions(self, student_username: str) -> list:
        return self.send_query('''SELECT * from SUBMISSIONS where SubmitterID = ?''', (student_username,))

    # enroll the student into the course
    def add_enrollment(self, course_id: str, student_id: str) -> None:
        self.send_query('''INSERT INTO Enrollments (CourseID, StudentID) VALUES (?, ?)''',
                        (course_id, student_id))

    # return all courses the given student is enrolled in
    def get_enrolled_courses_by_student(self, student: str) -> None:
        return self.send_query('''SELECT c.CourseID, c.CourseName FROM Courses c
                               JOIN Enrollments e ON c.CourseID = e.CourseID
                               JOIN Users u ON e.StudentID = u.ID
                               WHERE u.Username = ?''', (student,))

    # Fetch all students from the database
    def get_students(self) -> None:
        return self.send_query('''SELECT * FROM Users WHERE Privilege = "Student"''')

    # Get the ID of a course by its name
    def get_course_id_by_name(self, course_name: str) -> str:
        # Get the ID of a course by its name
        result = self.send_query('''SELECT CourseID FROM Courses WHERE CourseName = ?''', (course_name,))
        if result:
            return result[0]
        else:
            return None

    # set the grade of the given submission
    def grade_submission(self, submission_id: str, grade: int) -> None:
        # Update the grade of a submission
        self.send_query('''UPDATE Submissions SET Grade = ? WHERE ID = ?''', (grade, submission_id))

    # Get the ID of a user by their username
    def get_user_id_by_username(self, username: str) -> None:
        result = self.send_query('''SELECT ID FROM Users WHERE Username = ?''', (username,))

        if result:
            return result[0]
        else:
            return None

    # returns the username only if the username and password match
    def authenticate_user(self, username: str, password: str):

        user = self.send_query(
            """SELECT * FROM Users WHERE Username = ? AND Password = ?""",
            (username, password),
        )
        if user:
            return user
        else:
            return None

    def username_exists(self, username: str):
        user = self.send_query(
            '''SELECT * FROM Users WHERE Username = ?''',
            (username,))
        if user:
            return user
        else:
            return None

    # get the id for the given assignment by name
    def get_assignment_id_by_name(self, assignment_name: str) -> str:
        # Get the ID of an assignment by its name
        result = self.send_query('''SELECT AssignmentID FROM Assignments WHERE Name = ?''', (assignment_name,))

        if result:
            return result[0]
        else:
            return None

    def close_connection(self):
        self.conn.close()

    def get_student_grades(self, student_username):
        return self.send_query(
            '''SELECT Name, Grade FROM Submissions JOIN Assignments ON Submissions.AssignmentID = Assignments.AssignmentID WHERE SubmitterID = ?''',
            (student_username,))



class SystemGUIManager(tk.Tk):
    def __init__(self, db: Database):
        tk.Tk.__init__(self)
        self.db = db
        self.geometry("640x360")
        self.title('College Management System')
        self.frame = Frame(self)
        self.frame.place(anchor='nw')
        self.resizable(width=False, height=False)

        self.frames = {}
        for F in (LoginPage, RegisterPage):
            frame = F(self.frame, self, self.db)
            self.frames[F] = frame

        self.show_frame(LoginPage)

    def show_frame(self, frame):
        for f in self.frames.values():
            f.grid_forget()
        frame = self.frames[frame]
        frame.show()
        frame.grid(row=0,column=0)

    def reset_frame(self,F):
        frame = F(self.frame,self,self.db)
        self.frames[F] = frame


# create the login page
class LoginPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame,controller: Tk, db: Database) -> None:
        tk.Frame.__init__(self,parent)
        self.parent = parent
        self.controller = controller
        self.db = db
        ################################################


        # Setting up GUI
        self.img = ImageTk.PhotoImage(Image.open("shu_building.png"))
        self.img2 = ImageTk.PhotoImage(Image.open('sign-in_logo.png'))
        font = tkFont.Font(family='Arial',size=9,weight='bold')
        self.label = Label(self, image=self.img)
        self.label2 = Label(self, image=self.img2)
        self.username_label = Label(self, text="Username:",font=font)
        self.username_entry = tk.Entry(self,highlightthickness=2,highlightbackground='azure4')
        self.password_label = tk.Label(self, text="Password:",font=font)
        self.password_entry = tk.Entry(self, show="*",highlightthickness=2,highlightbackground='azure4') # hide password text
        self.login_button = tk.Button(self, text="Login", command=self.__login, bg='RoyalBlue', fg='white',font=font)
        self.login_button.config(width=15)
        self.register_button = tk.Button(self, text="Register", command=self.__register, bg='RoyalBlue',fg='White',font=font)
        self.register_button.config(width=15)
        self.viewstaff = tk.Button(self, text="View Staff", command=self.__viewStaff,bg='RoyalBlue',fg='White',font=font,width=15)


    def __viewStaff(self):
        ViewStaffPage(tk.Tk())

    # Purpose: To display all GUI widgets on to window
    def show(self) -> None:
        self.label.grid(row=0, rowspan=6,column=0)
        self.label2.grid(row=0,column=1,columnspan=2,sticky=N,padx=18, pady = (50,10))
        self.username_label.grid(row=1, column=1, sticky="es")
        self.username_entry.grid(row=1, column=2,sticky='s')
        self.password_label.grid(row=2, column=1, sticky="en", pady= (10,0))
        self.password_entry.grid(row=2, column=2, sticky='n', pady = (10,0))
        self.login_button.grid(row=3, column = 1,columnspan=2,stick='n')#, sticky='s')
        self.register_button.grid(row=4,column = 1, columnspan=2, sticky='n')#pady=(10,40))
        self.viewstaff.grid(row=5, column=1,columnspan=2,sticky='n')


    # Purpose: Determine whether to open the student or teacher page
    def __login(self) -> None:
        username = self.username_entry.get()
        password = self.password_entry.get()

        user = self.db.authenticate_user(username, password) # Checks if user and pass entries match a user in database
        if user:
            # Checks if user is a student or teacher
            if user[0][3] == "Student":
                self.controller.frames[StudentPage] = StudentPage(self.parent,self.controller,self.db,username)
                self.controller.show_frame(StudentPage)
                self.controller.reset_frame(LoginPage)
            else:
                self.controller.frames[TeacherPage] = TeacherPage(self.parent,self.controller,self.db,username)
                self.controller.show_frame(TeacherPage)
                self.controller.reset_frame(LoginPage)
        else:
            tk.messagebox.showerror("Error", "Invalid username or password") # Error case

    # Purpose: To open the register page
    def __register(self) -> None:
        self.controller.show_frame(RegisterPage)
        self.controller.reset_frame(LoginPage)


# Registration page
class RegisterPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame,controller: Tk,db: Database) -> None:
        tk.Frame.__init__(self,parent,bg='white')
        self.parent=parent
        self.controller = controller
        self.db = db
        ################################################

        # Setting up GUI
        self.img = ImageTk.PhotoImage(Image.open('sign-in_logo.png'))
        font = tkFont.Font(family='Arial',size=9,weight='bold')
        self.space = tk.Frame(self,width=220,bg='gray94',height=370)
        self.space2 = tk.Frame(self,width=220,bg='gray94',height=370)
        self.space3 = tk.Frame(self,width=220,bg='gray94',height=17)
        self.space4 = tk.Frame(self,width=220,bg='gray94',height=20)
        self.label = Label(self, image=self.img,bg='white')
        self.username_label = tk.Label(self, text="Username:",bg='white',font=font)
        self.username_entry = tk.Entry(self,bg='light grey')
        self.password_label = tk.Label(self, text="Password:",bg='white',font=font)
        self.password_entry = tk.Entry(self, show="*",bg='light grey')
        self.privilege_label = tk.Label(self, text="Privilege:",font=font,bg='white')
        self.privilege_var = tk.StringVar(self)  # global variable for tkinter
        self.privilege_var.set("Student")
        self.privilege_menu = ttk.OptionMenu(
            self, self.privilege_var, "Student", "Student", "Teacher"
        )  # dropdown
        self.privilege_menu['menu'].config(bg ='lightgrey')
        self.dob_label = tk.Label(self, text="DOB:",bg='white',font=font)
        self.dob_entry = tk.Entry(self,bg='light grey')
        self.email_label = tk.Label(self, text="Email:",bg='white',font=font)
        self.email_entry = tk.Entry(self,bg='light grey')
        self.phone_label = tk.Label(self, text="Phone:",bg='white',font=font)
        self.phone_entry = tk.Entry(self,bg='light grey')
        self.fname_label = tk.Label(self, text="First Name:",bg='white',font=font)
        self.fname_entry = tk.Entry(self,bg='light grey')
        self.lname_label = tk.Label(self, text="Last Name:",bg='white',font=font)
        self.lname_entry = tk.Entry(self,bg='light grey')
        self.back_button = tk.Button(self, text="Back", command=self.__back, bg='Black', fg='white',font=font)
        self.back_button.config(width=7)
        self.register_button = tk.Button(self, text="Register", command=self.__register,font=font,bg='RoyalBlue',fg='white')
        self.register_button.config(width=7)

    # Purpose: To display all GUI widgets on to window
    def show(self):
        self.space.grid(column=0,rowspan=13,row=0)
        self.space2.grid(column=3,row=0,rowspan=13)
        self.space3.grid(column=1,row=0,columnspan=2)
        self.space4.grid(column=1,row=12,columnspan=2)
        self.label.grid(row=1,column=1,columnspan=2,sticky='e',padx=(10,10),pady=(10,10))
        self.username_label.grid(row=2, column=1, sticky="e")#
        self.username_entry.grid(row=2, column=2,sticky='w')
        self.password_label.grid(row=3, column=1, sticky="e")
        self.password_entry.grid(row=3, column=2,sticky='w')
        self.privilege_label.grid(row=4, column=1, sticky="e")
        self.privilege_menu.grid(row=4, column=2,sticky='w')
        self.dob_label.grid(row=5, column=1, sticky="e")
        self.dob_entry.grid(row=5, column=2,stick='w')
        self.email_label.grid(row=6, column=1, sticky="e")
        self.email_entry.grid(row=6, column=2,sticky='w')
        self.phone_label.grid(row=7, column=1, sticky="e")
        self.phone_entry.grid(row=7, column=2,sticky='w')
        self.fname_label.grid(row=8, column=1, sticky="e")
        self.fname_entry.grid(row=8, column=2,sticky='w')
        self.lname_label.grid(row=9, column=1, sticky="e")
        self.lname_entry.grid(row=9, column=2,sticky='w')
        self.register_button.grid(row=10, column=2,sticky='w')
        self.back_button.grid(row=11,column=2,sticky='w')

    # Purpose: To return to the previous page
    def __back(self) -> None:
        self.controller.show_frame(LoginPage)
        self.controller.reset_frame(RegisterPage)

    # Purpose: To register user
    def __register(self) -> None:
        username = self.username_entry.get().replace(' ','')
        password = self.password_entry.get()
        privilege = self.privilege_var.get()
        dob = self.dob_entry.get()
        email = self.email_entry.get()
        phone = self.phone_entry.get()
        fname = self.fname_entry.get()
        lname = self.lname_entry.get()

        if username == '' or password == '':
            tk.messagebox.showerror("Error", "Username and Password field cannot be empty")
        else:
            user = self.db.username_exists(username)
            if user:
                tk.messagebox.showerror("Error", "Username already exists")
            else:
                self.db.add_user(username, password, privilege, dob, email, phone, fname, lname)
                tk.messagebox.showinfo("Success", "Registration successful")
                self.controller.show_frame(LoginPage)
                self.controller.reset_frame(RegisterPage)


# teacher's landing page
class TeacherPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame,controller: Tk,db: Database,professor: str) -> None:
        tk.Frame.__init__(self, parent,bg='white')
        self.parent = parent
        self.controller = controller
        self.db = db
        self.professor = professor

        # Setting up GUI
        font = tkFont.Font(family='Arial', size=12, weight='bold')
        font2 = tkFont.Font(family='Arial', size=9, weight='bold')
        self.space = tk.Frame(self, width=220, bg='gray94', height=370)
        self.space2 = tk.Frame(self, width=220, bg='gray94', height=370)
        self.space3 = tk.Frame(self, width=220, bg='gray94', height=20)
        self.space4 = tk.Frame(self, width=220, bg='gray94', height=20)
        self.label = tk.Label(self, text=f"Welcome, {self.professor}!",bg='white',font=font)
        self.create_course_button = tk.Button(self, text="Create Class", command=self.__create_course,width=24,
                                              bg='RoyalBlue',fg='white',font=font2)
        self.course_label = tk.Label(self, text="Select Class:",bg='white',font=font2)
        self.selected_course = tk.StringVar()
        self.course_combo = ttk.Combobox(self, textvariable=self.selected_course,width=15)  # remember which course is selected
        self.add_assignment_button = tk.Button(self, text="Add Assignment", command=self.__add_assignment,width=24,
                                               bg='RoyalBlue',fg='white',font=font2)
        self.view_submissions_button = tk.Button(self, text="View Submissions", command=self.__view_submissions,width=24,
                                                 bg='RoyalBlue',fg='white',font=font2)
        self.add_student_label = tk.Label(self, text="Add Student:",bg='white',font=font2)
        self.selected_student = tk.StringVar()
        self.student_combo = ttk.Combobox(self, textvariable=self.selected_student, width=15)
        self.add_student_button = tk.Button(self, text="Add Student to Class", command=self.__add_student_to_class,width=24,
                                            bg='RoyalBlue',fg='white',font=font2)
        self.logout_button = tk.Button(self, text="Logout", command=self.__logout,width=12,bg='Black',fg='white',font=font2)

    # Purpose: To show widgets on window
    def show(self):
        self.space.grid(row=0,column=0,rowspan=10)
        self.space2.grid(row=0,column=3,rowspan=10)
        self.space3.grid(row=0,column=1,columnspan=2,sticky='n')
        self.space4.grid(row=9,column=1,columnspan=2)
        self.label.grid(row=1, column=1, columnspan=2)
        self.create_course_button.grid(row=2, column=1, columnspan=2)
        self.course_label.grid(row=3, column=1, sticky='e')
        self.course_combo.grid(row=3, column=2, sticky="w")
        self.add_assignment_button.grid(row=4, column=1, columnspan=2)
        self.view_submissions_button.grid(row=5, column=1, columnspan=2)
        self.add_student_label.grid(row=6, column=1, sticky="e")
        self.student_combo.grid(row=6, column=2, sticky="w")
        self.add_student_button.grid(row=7, column=1, columnspan=2)
        self.logout_button.grid(row=8,column=1,columnspan=2)

        self.__populate_courses()
        self.__populate_students()

    # Purpose: To list all the courses
    def __populate_courses(self) -> None:
        courses = self.db.get_courses_by_professor(self.professor)
        if courses is not None:
            course_names = [course[1] for course in courses]
            self.course_combo['values'] = course_names

    # Purpose: To create a new course
    def __create_course(self) -> None:
        self.controller.frames[CreateCoursePage] = CreateCoursePage(self.parent,self.controller,self.db,self.professor)
        self.controller.show_frame(CreateCoursePage)

    # Purpose: To add a new assignment
    def __add_assignment(self) -> None:
        course_name = self.selected_course.get()
        if not course_name:
            tk.messagebox.showerror("Error", "Please select a class.")
            return

        course_id = self.db.get_courses_by_professor(self.professor)[self.course_combo.current()][0]
        self.controller.frames[AddAssignmentPage] = AddAssignmentPage(self.parent,self.controller,self.db,self.professor,
                                                                      course_id)
        self.controller.show_frame(AddAssignmentPage)

    # Purpose: To view the submissions
    def __view_submissions(self) -> None:
        course_name = self.selected_course.get()
        if not course_name:
            tk.messagebox.showerror("Error", "Please select a class.")
            return

        course_id = self.db.get_courses_by_professor(self.professor)[self.course_combo.current()][0]
        assignments = self.db.get_assignments_by_course(course_id)
        if assignments is not None:
            self.controller.frames[ViewSubmissionsPage] = ViewSubmissionsPage(self.parent,self.controller,self.db,self.professor,
                                                                          course_id)
            self.controller.show_frame(ViewSubmissionsPage)
        else:
            tk.messagebox.showerror("Error", "Selected Class has no current assignments.")
            self.selected_course.set('')

    # Purpose: To list all students in the class
    def __populate_students(self) -> None:
        # Fetch all students from the database using db object
        students = self.db.get_students()
        if students is not None:

            student_usernames = [student[1] for student in students]
            self.student_combo['values'] = student_usernames

    # Purpose: add a student ot the class
    def __add_student_to_class(self) -> None:
        course_name = self.selected_course.get()
        student_username = self.selected_student.get()

        if not course_name or not student_username:
            tk.messagebox.showerror("Error", "Please select a class and a student.")
            return

        # Get course ID
        course_id = self.db.get_course_id_by_name(course_name)[0]

        # Get student ID
        student_id = self.db.get_user_id_by_username(student_username)[0]
        # Add enrollment
        self.db.add_enrollment(course_id, student_id)
        tk.messagebox.showinfo("Success", f"{student_username} added to class {course_name}.")

    # Purpose: To return to the login page
    def __logout(self) -> None:
        self.controller.show_frame(LoginPage)
        self.controller.frames.pop(TeacherPage)

# student's langing page
class StudentPage(tk.Frame):
    def __init__(self, parent,controller,db,student) -> None:
        self.controller = controller
        self.db = db
        self.student = student
        self.parent = parent
        tk.Frame.__init__(self, parent)
        self.space = tk.Frame(self, width=640)
        font = tkFont.Font(family='Arial', size=12, weight='bold')
        self.font2 = tkFont.Font(family='Arial', size=9, weight='bold')

        self.label = tk.Label(self, text=f"Welcome, {self.student}!",bg = 'RoyalBlue', fg='White', font=font)

        self.enrolled_courses_label = tk.Label(self, text="Enrolled Classes:",bg='black',fg='white',font=font,height=1)

        self.view_submissions_button = tk.Button(self, text="View Submissions", command=self.view_submissions,font=self.font2,height=1,width=20)

        self.view_grades_button = tk.Button(self, text="View Grades Graph", command=self.view_grades,font=self.font2,height=1,width=20)

        self.logout_button = tk.Button(self, text="Logout", command=self.logout,width=20,bg='black',fg='white',font=self.font2)

    def show(self):
        self.space.grid(row=0,column=0,columnspan=8,sticky='ew')
        self.label.grid(row=1, column=0, columnspan=8, sticky='ew')
        self.enrolled_courses_label.grid(row=2, column=4, columnspan=4,sticky='ew')
        self.view_submissions_button.grid(row=2, column=0, columnspan=2,stick='e')
        self.view_grades_button.grid(row=2, column=2, columnspan=2,sticky='w')
        self.logout_button.grid(row=3,column=1,columnspan=2,stick='ew')
        self.populate_enrolled_courses()

    def logout(self) -> None:
        self.controller.show_frame(LoginPage)
        self.controller.frames.pop(StudentPage)

    # view the student's submissions and grades
    def view_submissions(self):
        submissions = self.db.get_student_submissions(self.student)

        if not submissions:
            tk.messagebox.showinfo("Submissions", "You have no submissions.")
            return

        submission_window = tk.Toplevel(self)
        submission_window.title("Your Submissions")

        cat1 = tk.Label(submission_window, text='Assignment ID:',font=self.font2,width=20,highlightbackground='black',highlightthickness='2',bg='grey',fg='white')
        cat2 = tk.Label(submission_window,text='Submission:',font=self.font2,width=20,highlightbackground='black',highlightthickness='2',bg='grey',fg='white')
        cat3 = tk.Label(submission_window,text='Grade:',font=self.font2,width=20,highlightbackground='black',highlightthickness='2',bg='grey',fg='white')
        cat1.grid(column=0,row=0,sticky='ew')
        cat2.grid(column=1,row=0,sticky='ew')
        cat3.grid(column=2,row=0,sticky='ew')


        for index, submission in enumerate(submissions, start=1):
            tk.Label(submission_window, text=f"{submission[1]}",font=self.font2,highlightbackground='black',highlightthickness='2').grid(row=index, column=0,sticky='nesw')
            tk.Label(submission_window, text=f"{submission[3]}",font=self.font2,highlightbackground='black',highlightthickness='2').grid(row=index, column=1,sticky='nesw')
            tk.Label(submission_window, text=f"{submission[4]}",font=self.font2,highlightbackground='black',highlightthickness='2').grid(row=index, column=2,sticky='nesw')

    # list the courses this student is in
    def populate_enrolled_courses(self) -> None:
        courses = self.db.get_enrolled_courses_by_student(self.student)
        if not courses:
            tk.Label(self, text="You are not enrolled in any classes.").grid(row=3, column=4, columnspan=4)
            return

        for index, course in enumerate(courses, start=3):
            course_name = course[1]
            tk.Button(self, text=course_name, command=lambda name=course_name: self.open_class(name),font=self.font2,bg='white').grid(
                row=index, column=4, columnspan=4,sticky='ew')

    # open the landing page for the class
    def open_class(self, course_name):
        self.controller.frames[ClassPage] = ClassPage(self.parent,self.controller,self.db,self.student,course_name)
        self.controller.show_frame(ClassPage)

    def view_grades(self):
        # filter ungraded assignments to show as 0s for now
        def filter_grade(grade) -> int:
            if grade == None:
                return 0
            return grade

        grades = self.db.get_student_grades(self.student)
        if not grades:
            messagebox.showinfo("Grades", "You have no grades.")
            return
        # selecting assignment names and grades
        assignment_names = [grade[0] for grade in grades]
        assignment_grades = [filter_grade(grade[1]) for grade in grades]
        # Plotting grades
        plot_window = tk.Toplevel(self)
        plot_window.title("Your Grades")


        figure = Figure(figsize=(5,5))#, dpi=100)
        figure_canvas = FigureCanvasTkAgg(figure,plot_window)
        NavigationToolbar2Tk(figure_canvas, plot_window)
        axes = figure.add_subplot()
        axes.bar(assignment_names, assignment_grades, color ='red')
        axes.set_title('Your Grades')
        axes.set_ylabel('Grades')
        axes.set_xlabel('Assignments')
        #axes.xticks(rotations=45,ha='right')

        figure_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)



# landing page for making a course
class CreateCoursePage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame, controller: Tk, db: Database, professor: str) -> None:
        tk.Frame.__init__(self,parent,bg='white')
        self.parent = parent
        self.controller = controller
        self.db = db
        self.professor = professor

        # Setting up GUI
        font = tkFont.Font(family='Arial', size=9, weight='bold')
        self.space = tk.Frame(self, width=175, bg='gray94', height=370)
        self.space2 = tk.Frame(self, width=175, bg='gray94', height=370)
        self.space3 = tk.Frame(self,  bg='gray94', height=75)
        self.space4 = tk.Frame(self,  bg='gray94', height=75)
        self.course_name_label = tk.Label(self, text="Class Name:",font=font,bg='white')
        self.course_name_entry = tk.Entry(self,highlightthickness=2,highlightbackground='azure4')
        self.room_number_label = tk.Label(self, text="Room Number:",font=font,bg='white')
        self.room_number_entry = tk.Entry(self,highlightthickness=2,highlightbackground='azure4')
        self.create_button = tk.Button(self, text="Create", command=self.__create_course,width=12,bg='RoyalBlue',fg='white',font=font)
        self.back_button = tk.Button(self, text="Cancel",command=self.__back,width=12,bg='Black',fg='white',font=font)

    # Purpose: To display widgets on window
    def show(self):
        self.space.grid(row=0, column=0, rowspan=6,sticky='e')
        self.space2.grid(row=0, column=3, rowspan=6,sticky='w')
        self.space3.grid(row=0, column=1, columnspan=2, sticky='new')
        self.space4.grid(row=5, column=1, columnspan=2,sticky='sew')
        self.course_name_label.grid(row=1, column=1, sticky="e")#, pady=(80,0))
        self.course_name_entry.grid(row=1, column=2, sticky='w')#, pady=(80,0))
        self.room_number_label.grid(row=2, column=1, sticky="e")
        self.room_number_entry.grid(row=2, column=2,sticky='w')
        self.create_button.grid(row=3, column=1,columnspan=2)
        self.back_button.grid(row=4,column=1,columnspan=2,sticky='n')
        self.columnconfigure([1,2],pad=40)

    # Purpose: To create the course
    def __create_course(self):
        course_name = self.course_name_entry.get()
        room_number = self.room_number_entry.get()

        if not course_name or not room_number:
            tk.messagebox.showerror("Error", "Please fill in all fields.")
            return

        self.db.add_course(course_name, self.professor, room_number)
        tk.messagebox.showinfo("Success", "Class created successfully.")
        self.controller.show_frame(TeacherPage)

    # Purpose: To return to the Teacher Page
    def __back(self):
        self.controller.show_frame(TeacherPage)
        self.controller.frames.pop(CreateCoursePage)


# add assignment page
class AddAssignmentPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame, controller: Tk, db: Database, professor: str, course_id):
        tk.Frame.__init__(self,parent,bg='white')
        self.parent = parent
        self.controller = controller
        self.db = db
        self.professor = professor
        self.course_id = course_id

        # Setting up GUI
        font = tkFont.Font(family='Arial', size=9, weight='bold')
        self.space = tk.Frame(self, width=130, bg='gray94', height=370)
        self.space2 = tk.Frame(self, width=130, bg='gray94', height=370)
        self.space3 = tk.Frame(self, bg='gray94', height=75)
        self.space4 = tk.Frame(self, bg='gray94', height=75)
        self.assignment_name_label = tk.Label(self, text="Assignment Name:",font=font,bg='white')
        self.assignment_name_entry = tk.Entry(self, width = 40,bg='light grey')
        self.description_label = tk.Label(self, text="Description:",font=font,bg='white')
        self.description_entry = tk.Text(self, width=30, height=5,bg='light grey')
        self.add_button = tk.Button(self, text="Add", command=self.__add_assignment,width=12,bg='RoyalBlue',fg='white',
                                    font=font)
        self.back_button = tk.Button(self, text="Cancel",command=self.__back,width=12,bg='Black',fg='white',font=font)

    # Purpose: To display widgets on window screen
    def show(self):
        self.space.grid(row=0, column=0, rowspan=6, sticky='w')
        self.space2.grid(row=0, column=3, rowspan=6, sticky='e')
        self.space3.grid(row=0, column=1, columnspan=2, sticky='new')
        self.space4.grid(row=5, column=1, columnspan=2, sticky='sew')
        self.assignment_name_label.grid(row=1, column=1, sticky="e")
        self.assignment_name_entry.grid(row=1, column=2,sticky='w')
        self.description_label.grid(row=2, column=1, sticky="e")
        self.description_entry.grid(row=2, column=2, sticky='w')
        self.add_button.grid(row=3,column=1, columnspan=2)
        self.back_button.grid(row=4,column=1,columnspan=2)
        self.columnconfigure([1,2],pad=20)

    # Purpose: To return to previous page
    def __back(self):
        self.controller.show_frame(TeacherPage)
        self.controller.frames.pop(AddAssignmentPage)

    # Purpose: add assignment action
    def __add_assignment(self) -> None:
        name = self.assignment_name_entry.get()
        description = self.description_entry.get("1.0", tk.END)

        if not name or not description:
            tk.messagebox.showerror("Error", "Please fill in all fields.")
            return

        self.db.add_assignment(name, description, self.course_id)
        tk.messagebox.showinfo("Success", "Assignment added successfully.")
        self.controller.show_frame(TeacherPage)


# page for viewing submissions
class ViewSubmissionsPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame, controller: Tk, db: Database,professor: str,course_id) -> None:
        tk.Frame.__init__(self,parent)
        self.parent = parent
        self.controller = controller
        self.db = db
        self.professor = professor
        self.course_id = course_id

        # Setting up GUI
        self.space = tk.Frame(self, width=640)
        font = tkFont.Font(family='Arial', size=15, weight='bold')
        self.font2 = tkFont.Font(family='Arial',size=9,weight='bold')
        self.submissions_label = tk.Label(self, text="Submissions:",bg='RoyalBlue',fg='White',font=font)
        self.exit_button = tk.Button(self, text="Exit",command=self.__exit,width=12,bg='Red',fg='white',font=self.font2)

    # Purpose: To display widgets on window screen
    def show(self):
        self.space.grid(row=0,column=0,columnspan=8,sticky='ew')
        self.submissions_label.grid(row=1, column=0, columnspan=8,sticky='ew')
        self.exit_button.grid(row=2,column=0, columnspan=8,stick='ew')
        self.__populate_submissions()

    # Purpose: To exit and return to Teacher Page
    def __exit(self):
        self.controller.show_frame(TeacherPage)
        self.controller.frames.pop(ViewSubmissionsPage)

    # Purpose: To fill the submissions into the page
    def __populate_submissions(self) -> None:
        assignments = self.db.get_assignments_by_course(self.course_id)
        index = 3
        for assignment in assignments:

            assignment_name = assignment[1]
            tk.Label(self, text=f"{assignment_name} Submissions:",bg='white',font=self.font2).grid(row=index, column=0,
                                                                                                   columnspan=8,sticky='ew')
            submissions = self.db.get_submissions_by_assignment(assignment[0])

            if submissions is not None:

                for sub_index, submission in enumerate(submissions, start=index + 1):
                    tk.Label(self, text=f"Student: {submission[2]}, Submission: {submission[3]}",font=self.font2).grid(
                        row=sub_index,
                        column=0,
                        columnspan=6,
                        sticky='ew')
                    grade_entry = tk.Entry(self, width=5)
                    grade_entry.grid(row=sub_index, column=6,sticky='ew')
                    grade_entry.insert(0, str(submission[4]))  # Corrected the insert method call
                    update_button = tk.Button(self, text="Update Grade", bg='RoyalBlue',fg='White',font=self.font2,
                                              command=lambda submission_id=submission[0],
                                                             grade_entry = grade_entry: self.__update_grade(
                        submission_id, grade_entry))
                    update_button.grid(row=sub_index, column=7,sticky='ew')
                index = sub_index + 1

            else:
                tk.Label(self, text="No submissions yet",font=self.font2).grid(row=index + 1, column=0, columnspan=8,
                                                                               sticky='ew')


    # Purpose: To update the new grade with error checks
    def __update_grade(self, submission_id, grade_entry):
        new_grade = grade_entry.get()
        try:
            new_grade = int(new_grade)
        except ValueError:
            tk.messagebox.showerror("Error", "Grade must be an integer.")
            return

        if new_grade < 0 or new_grade > 100:
            tk.messagebox.showerror("Error", "Grade must be between 0 and 100.")
            return

        self.db.grade_submission(submission_id, new_grade)
        tk.messagebox.showinfo("Success", "Grade updated successfully.")


# landing page for a class
class ClassPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame, controller: Tk, db: Database,student: str,course_name: str) -> None:
        tk.Frame.__init__(self,parent)#,bg='white')
        self.parent = parent
        self.controller = controller
        self.db = db
        self.student = student
        self.course_name = course_name

        # Setting up GUI
        font = tkFont.Font(family='Arial', size=12, weight='bold')
        self.font2 = tkFont.Font(family='Arial', size=9, weight='bold')
        self.space = tk.Frame(self, width=640)
        self.assignment_label = tk.Label(self, text="Assignments:",bg='RoyalBlue', fg='White', font=font)
        self.exit_button = tk.Button(self, text="Exit",command=self.__exit,bg='Red',fg='white',font=self.font2)


    # Purpose: To display widgets on window screen
    def show(self) -> None:
        self.space.grid(row=0, column=0, columnspan=8,sticky='ew')
        self.assignment_label.grid(row=1, column=2, columnspan=4,sticky='ew')
        self.exit_button.grid(row=1,column=0,sticky='ew')
        self.__populate_assignments()

    # Purpose: To exit and return to Student Page
    def __exit(self):
        self.controller.show_frame(StudentPage)
        self.controller.frames.pop(ClassPage)

    # Purpose: To fill in the assignments
    def __populate_assignments(self):
        course_id = self.db.get_course_id_by_name(self.course_name)[0]
        assignments = [self.db.get_assignments_by_course(course_id)]
        # for index, assignment in enumerate(assignments, start=1):
        bgs = ['White','Black']
        for a in assignments:
            for index, assignment in enumerate(a, start=2):
                assignment_name = assignment[1]
                assignment_desc = assignment[2]
                tk.Button(self, text=assignment_name,
                          command=lambda name=assignment_name, desc=assignment_desc: self.__submit_assignment(name, desc),
                          font=self.font2,bg=bgs[index % 2],fg=bgs[(index + 1)%2]).grid(
                    row=index, column=2, columnspan=4, sticky='ew')

    # Purpose: To open submission page
    def __submit_assignment(self, assignment_name, desc):
        self.controller.frames[SubmitAssignmentPage] = SubmitAssignmentPage(self.parent,self.controller,self.db,self.student,
                                                                            assignment_name,desc)
        self.controller.show_frame(SubmitAssignmentPage)


# page for submitting assignments
class SubmitAssignmentPage(tk.Frame):
    # Constructor
    def __init__(self, parent: Frame, controller: Tk, db: Database,student: str,assignment_name: str,desc: str) -> None:
        tk.Frame.__init__(self,parent,bg='white')
        self.parent = parent
        self.controller = controller
        self.db = db
        self.student = student
        self.assignment_name = assignment_name
        self.desc=desc

        # Setting up GUI
        font = tkFont.Font(family='Arial', size=9, weight='bold')
        self.space = tk.Frame(self, width=145, bg='gray94', height=370)
        self.space2 = tk.Frame(self, width=145, bg='gray94', height=370)
        self.space3 = tk.Frame(self, bg='gray94', height=75)
        self.space4 = tk.Frame(self, bg='gray94', height=75)

        self.desc_label = tk.Label(self, text="Description:",bg='white')
        self.desc_label2 = tk.Label(self,text=self.desc,bg='white')
        self.body_label = tk.Label(self, text="Submission:",bg='white')
        self.body_entry = tk.Text(self, width=30, height=5,bg='light grey')

        self.submit_button = tk.Button(self, text="Submit", command=self.__submit, font=font,width=12,bg='RoyalBlue',fg='white')
        self.back_button = tk.Button(self, text="Cancel",command=self.__back,width=12,bg='Black',fg='white',font=font)

    # Purpose: To display widgets on Window screen
    def show(self):
        self.space.grid(row=0, column=0, rowspan=6, sticky='w')
        self.space2.grid(row=0, column=3, rowspan=6, sticky='e')
        self.space3.grid(row=0, column=1, columnspan=2, sticky='new')
        self.space4.grid(row=5, column=1, columnspan=2, sticky='sew')
        self.desc_label.grid(row=1, column=1, sticky="e")
        self.desc_label2.grid(row=1,column=2,sticky='w')
        self.body_label.grid(row=2, column=1, sticky="e")
        self.body_entry.grid(row=2, column=2)
        self.submit_button.grid(row=3, column=1,columnspan=2)
        self.back_button.grid(row=4,column=1,columnspan=2)
        self.columnconfigure([1,2],pad=20)

    # Purpose: To return to previous page
    def __back(self):
        self.controller.show_frame(ClassPage)
        self.controller.frames.pop(SubmitAssignmentPage)

    # Purpose: To upload the submission
    def __submit(self):
        body = self.body_entry.get("1.0", tk.END)

        if not body:
            tk.messagebox.showerror("Error", "Please enter your submission.")
            return

        assignment_id = self.db.get_assignment_id_by_name(self.assignment_name)[0]
        self.db.add_submission(assignment_id, self.student, body)
        tk.messagebox.showinfo("Success", "Submission successful.")
        self.controller.show_frame(StudentPage)

class ViewStaffPage:
    def __init__(self, master):
        self.master = master
        self.master.title("Student Options")

        self.option_var = tk.StringVar()
        self.option_var.set("")  # Set default option

        self.option_label = tk.Label(master, text="Select an option:")
        self.option_label.pack()

        self.options = [
                "Business",
                "Arts and Sciences",
                "Diplomacy",
                "Health",
                "Nursing",
                "Human Development and Culture",
                "Theology"
            ]

        self.option_menu = tk.OptionMenu(master, self.option_var, *self.options)
        self.option_menu.pack()

        self.select_button = tk.Button(master, text="Select", command=self.show_message)
        self.select_button.pack()

        # Show a message as a scrollable popup
    def show_scrollable_message(self, message: str) -> None:
        top = tk.Toplevel(self.master)
        top.title("Message")
        text = ScrolledText(top, width=80, height=10)
        text.pack()
        text.insert(tk.END, message)
        text.configure(state='disabled')

    # generate the message to show by scraping the appropriate shu.edu subpage
    def show_message(self):
        selected_option = self.option_var.get()
        choose = {
                "Business": "https://www.shu.edu/business/faculty.html",
                "Arts and Sciences": "https://www.shu.edu/arts-sciences/faculty.html",
                "Diplomacy": "https://www.shu.edu/diplomacy/faculty.html",
                "Health": "https://www.shu.edu/health/faculty.html",
                "Nursing": "https://www.shu.edu/nursing/faculty.html",
                "Human Development and Culture": "https://www.shu.edu/human-development-culture-media/faculty.html",
                "Theology": "https://www.shu.edu/theology/faculty.html"
            }
        # HTTP GET Request
        page = requests.get(choose[selected_option], headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36'})
        facultylist = []
        # Parse HTML data
        soup = BeautifulSoup(page.text, 'html.parser')
        # Find all <strong> tag objects of the title class
        data = soup.findAll('strong', {"class": "title"})
        # find each <a> tag object and extract the text from that
        for i in data:
            faculty = i.find('a')
            if faculty:
                facultylist.append(faculty.text)
            # add each item of the list to the string on a newline
        facultystring = '\n'.join(str(x) for x in facultylist)

        self.show_scrollable_message(f"Here is a list of faculty members for {selected_option}:\n" + facultystring)

def reset_system():
    conn = sqlite3.connect('collegeMGMTsystem.db')
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM Users''')
    conn.commit()
    cursor.execute('''DELETE FROM Courses''')
    conn.commit()
    cursor.execute('''DELETE FROM Assignments''')
    conn.commit()
    cursor.execute('''DELETE FROM Submissions''')
    conn.commit()
    cursor.execute('''DELETE FROM Enrollments''')
    conn.commit()
    conn.close()




if __name__ == "__main__":
    db = Database()

    # Example registration (can be modified or removed)
    # db.add_user("teacher", "password", "Teacher", "01/01/1990", "teacher@example.com", "1234567890", "John", "Doe")
    # db.add_user("student", "password", "Student", "01/01/1995", "student@example.com", "0987654321", "Jane", "Doe")
    #reset_system()

    app = SystemGUIManager(db)

    app.mainloop()



