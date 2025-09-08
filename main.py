# target is to get a nice little cli to to do some basic canvas
# tasks for work related stuffs
# search course, pull lists of students, grab and aggregate some grades across multiple
# instances of the same course. 
#
# maybe a toggle to set/unset a course favorite status?
from dataclasses import dataclass, field
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator as numVal
import requests, os

def init_auth(credentials='creds/token.crd'):
    try:
        os.path.isfile(credentials) and os.stat(credentials).st_size >= 10
        with open(credentials) as file:
            token = file.read().strip()
        return token
    except:
        print('Token missing! Cannot access Canvas LMS without it!')
        raise SystemExit

@dataclass
class Res:
    course_id: str = ''
    course_name: str = ''
    course_date: str = ''
    courses: list = field(default_factory=list)
    w_base_url: str = 'https://hv.instructure.com/api/v1'
    w_token: str = init_auth()
    w_header = {"Authorization":f"Bearer {w_token}"}

class Menu:
    def __init__(self):
        self.state = 'main'

    def run(self, res):
        while True:
            if self.state == 'main':
                self.main_menu(res)
            elif self.state == 'course_main_menu':
                self.course_main_menu(res)
            elif self.state == 'pick_course':
                self.pick_course_menu(res)
            elif self.state == 'submit_course_id':
                submit_course_id(res)
                self.state = 'course_main_menu'
            elif self.state == 'student_main_menu':
                self.student_main_menu(res)

    def main_menu(self, res):
        choice = inquirer.select(
            message='Select: ',
            choices=['Courses', 'Students', 'Quit'],
            default='Courses',
        ).execute()
        if choice == 'Courses':
            self.state = 'course_main_menu'
        elif choice == 'Students':
            self.state = 'student_main_menu'
        elif choice == 'Quit':
            raise SystemExit

    def course_main_menu(self, res):
        choice = inquirer.select(
            message='Select: ',
            choices=['Pick course', 'Enter ID', 'Back', 'Quit'],
            default='Pick course',
        ).execute()
        if choice == 'Pick course':
            self.state = 'pick_course'
        elif choice == 'Enter ID':
            self.state = 'submit_course_id'
        elif choice == 'Back':
            self.state = 'main'
        elif choice == 'Quit':
            raise SystemExit
        
    def pick_course_menu(self, res):
        choice = inquirer.select(
            message='Course category: ',
            choices=['All', 'Favorites', 'Back', 'Quit'],
            default='Favorites',
        ).execute()
        if choice == 'Back':
            self.state = 'main'
        elif choice == 'Quit':
            raise SystemExit
        else:
            res.courses = get_course_list(choice, res)
            print(res.courses)
        
    def student_main_menu(self, res):
        choice = inquirer.select(
            message='Select: ',
            choices=['Pick student', 'Enter ID', 'Back', 'Quit'],
            default='Pick student',
        ).execute()
        if choice == 'Pick student':
            self.state = 'pick_student'
        elif choice == 'Enter ID':
            self.state = 'submit_student_id'
        elif choice == 'Back':
            self.state = 'main'
        elif choice == 'Quit':
            raise SystemExit

def get_course_list(category, res):
    if category == 'All':
        # pull courses where the user has a teacher role
        url = f'{res.w_base_url}/courses/?page=1&per_page=200'
    elif category == 'Favorites':
        # pull only courses pinned to the users main page
        url = f'{res.w_base_url}/users/self/favorites/courses'
    course_json = requests.get(url, headers=res.w_header).json()
    
    courses = [
        f'{c["id"]}:{c["name"]}:{str(c["start_at"] or "")[:10]}'
        for c in course_json
        if c.get('enrollments') and c['enrollments'][0].get('type') == 'teacher'
    ]
    # sorts them so they show up in alphabetical order. Array is [courseid:name:date]
    courses.sort(key=lambda c: c.split(':')[1].strip())
    return courses

def submit_course_id(res):
    verified_course_code = False
    while not verified_course_code:
        _id = inquirer.text(
            message='Enter course ID: ',
            validate=numVal(),
        ).execute()

        # run a simple check against canvas to make sure its a valid code.
        response = requests.get(f'{res.w_base_url}/courses/{_id}', headers=res.w_header).json()
        if 'id' in response and int(_id) == int(response['id']):
            res.course_id = _id
            res.course_name = response['name']
            res.course_date = response['created_at']
            verified_course_code = True
            print(f'Course selected: {res.course_name}')
        else:
            print('Invalid course code. Try again!\n')

if __name__ == '__main__':
    Menu().run(Res())