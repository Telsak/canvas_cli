# target is to get a nice little cli to to do some basic canvas
# tasks for work related stuffs
# search course, pull lists of students, grab and aggregate some grades across multiple
# instances of the same course. 
#
# maybe a toggle to set/unset a course favorite status?
from dataclasses import dataclass, field
from InquirerPy import inquirer
import requests

@dataclass
class Res:
    course_id: str = ''
    course_name: str = ''
    course_date: str = ''
    courses: list = field(default_factory=list)

class Menu:
    def __init__(self):
        self.state = 'main'

    def run(self, res):
        while True:
            if self.state == 'main':
                self.main_menu(res)
            elif self.state == 'course_main_menu':
                self.course_main_menu(res)
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

def get_course_list(category):
    courses = []
    if category == 'all':
        # pull courses where the user has a teacher role
        url = f'{base_url}/courses/?page=1&per_page=200'
    elif category == 'favorites':
        # pull only courses pinned to the users main page
        url = f'{base_url}/users/self/favorites/courses'
    course_json = requests.get(url, headers=header).json()
    
    courses = [
        f'{c["id"]}:{c["name"]}:{str(c["start_at"] or "")[:10]}'
        for c in course_json
        if c.get('enrollments') and c['enrollments'][0].get('type') == 'teacher'
    ]
    # sorts them so they show up in alphabetical order. Array is [courseid:name:date]
    courses.sort(key=lambda c: c.split(':')[1].strip())
    return courses



if __name__ == '__main__':
    with open('creds/token.crd') as file:
        token = file.read().strip()
    base_url = 'https://hv.instructure.com/api/v1'
    header = {"Authorization":f"Bearer {token}"}

    stuff = get_course_list('favorites')
    print(stuff)
    Menu().run(Res())