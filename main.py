# target is to get a nice little cli to to do some basic canvas
# tasks for work related stuffs
# search course, pull lists of students, grab and aggregate some grades across multiple
# instances of the same course. 
#
# maybe a toggle to set/unset a course favorite status?
from dataclasses import dataclass, field
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator as numVal
import requests, os, time

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
    course_name: str = 'Ingen vald'
    course_date: str = ''
    course_assignments: dict = field(default_factory=dict)
    all_courses: list = field(default_factory=list)
    favorite_courses: list = field(default_factory=list)
    student_id: str = ''
    student_name: str = 'Ingen vald'
    student_email: str = ''
    all_students: list = field(default_factory=list)
    w_base_url: str = 'https://hv.instructure.com/api/v1'
    w_token: str = init_auth()
    w_header = {"Authorization":f"Bearer {w_token}"}
    term_size = os.get_terminal_size()
    term_clear = 'cls' if os.name == 'nt' else 'clear'
    ctx: str = 'main'

class Menu:
    def __init__(self):
        self.state = 'main'

    def run(self, res):
        mmap = {
            'main': self.main_menu,
            'course_main_menu': self.course_main_menu,
            'pick_course': self.pick_course_menu,
            'student_main_menu': self.student_main_menu,
            'pick_student': self.pick_student_menu,
            'submit_course_id': submit_course_id,
            'submit_student_id': submit_student_id,
            'get_student_grades': get_student_grades,
            'get_course_assignments': get_course_assignments
        }
        
        while True:
            if self.state == 'quit': raise SystemExit
            if res.ctx == 'main': 
                self.state = 'main'
                res.ctx = ''
            self.render_status(res)
            menu_option = mmap[self.state]
            menu_option(res)

    def render_status(self, res):
        #os.system(res.term_clear)
        name_len = len(res.course_name)
        name_len += len(res.student_name)
        cols = name_len + 20

        print(f'\n╓{"─" * cols}╖')
        print(f'║ Kurs: {res.course_name} ║ Student: {res.student_name} ║')
        print(f'╙{"─" * cols}╜')
        print(f'{"█" * (res.term_size[0] - 8)}▓▓▓▒▒░\n')


    def main_menu(self, res):
        options = ['Courses','Get course assignments']
        if res.course_name != 'Ingen vald':
            options.append('Students')
        if res.course_name != 'Ingen vald' and res.student_name != 'Ingen vald':
            options.append('Get student grades')
        options.append('Quit')
        
        choice = inquirer.select(
            message='Select: ', choices=options,
        ).execute()

        mmap = {
            'Courses': 'course_main_menu',
            'Students': 'student_main_menu',
            'Get student grades': 'get_student_grades',
            'Get course assignments': 'get_course_assignments',
            'Quit': 'quit'
            }
        
        self.state = mmap[choice]

    def course_main_menu(self, res):
        choice = inquirer.select(
            message='Select: ', choices=['Pick course', 'Enter ID', 'Back', 'Quit'],
            default='Pick course',
        ).execute()
        
        mmap = {
            'Pick course': 'pick_course',
            'Enter ID': 'submit_course_id',
            'Back': 'main',
            'Quit': 'quit'
        }

        self.state = mmap[choice]
        
    def pick_course_menu(self, res):
        choice = inquirer.select(
            message='Course category: ', choices=['All', 'Favorites', 'Back', 'Quit'],
            default='Favorites',
        ).execute()

        if choice == 'Back':
            self.state = 'main'
            return
        elif choice == 'Quit':
            raise SystemExit
        
        courses = get_course_list(choice, res) or []
        if not courses:
            self.state = 'main'
            return

        choice = choice.lower()
        choice = 'all_courses' if choice == 'all' else 'favorite_courses'
        setattr(res, choice, list(courses))

        course = inquirer.select(
            message='Select Course: ',
            choices=courses,
            default=courses[0],
        ).execute()
    
        res.course_id, res.course_name, res.course_date = course.split(':')
        self.state = 'main'

    def pick_student_menu(self, res):
        users = get_student_list(res) or []
        if not users:
            self.state = 'main'
            return

        choice = inquirer.select(
            message='Student: ', choices=users + ['Back', 'Quit'],
        ).execute()

        if choice == 'Back':
            self.state = 'main'
            return
        elif choice == 'Quit':
            raise SystemExit

        res.student_name, res.student_id, res.student_email = choice.split(',')
        print(choice)
        self.state = 'main'
        
    def student_main_menu(self, res):
        if res.course_name == 'Ingen vald':
            print('Kan inte välja student utan kurs!')
            self.state = 'main'
            return
        
        choice = inquirer.select(
            message='Select: ', choices=['Pick student', 'Enter ID', 'Back', 'Quit'],
            default='Pick student',
        ).execute()

        mmap = {
            'Pick student': 'pick_student',
            'Enter ID': 'submit_student_id',
            'Back': 'main',
            'Quit': 'quit'
        }
        
        self.state = mmap[choice]

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

def get_student_list(res):
    url = f'{res.w_base_url}/courses/{res.course_id}/users?enrollment_type=student&per_page=100'
    response = requests.get(url, headers=res.w_header)
    data = response.json()

    while response.links.get('next') is not None:
        url = response.links['next']['url']
        response = requests.get(url, headers=res.w_header)
        data.extend(response.json())
    data.sort(key=lambda u: u['sortable_name'].split(',')[0].strip())
    
    users = []
    for user in data:
        last, first = user["sortable_name"].split(',')
        first = first.lstrip()
        print(f'{first} {last},{user["login_id"]},{user["email"]}')
        users.append(f'{first} {last},{user["login_id"]},{user["email"]}')
    
    return users

def submit_course_id(res):
    verified_course_id = False
    while not verified_course_id:
        _id = inquirer.text(
            message='Enter course ID: ',
            validate=numVal(),
        ).execute()

        # run a simple check against canvas to make sure its a valid course ID.
        response = requests.get(f'{res.w_base_url}/courses/{_id}', headers=res.w_header).json()
        if 'id' in response and int(_id) == int(response['id']):
            res.course_id = _id
            res.course_name = response['name']
            res.course_date = response['created_at']
            verified_course_id = True
            print(f'Course selected: {res.course_name}')
        else:
            print('Invalid course code. Try again!\n')

def submit_student_id(res):
    verified_student_id = False
    while not verified_student_id:
        login_id = inquirer.text(
            message='Enter student ID: ',
        ).execute()

        # run a simple check against canvas to make sure its a valid student ID
        url = f'{res.w_base_url}/courses/{res.course_id}/users?search_term={login_id}'
        print(url)
        response = requests.get(url, headers=res.w_header).json()
        if len(response) > 0 and response[0]['login_id'] == login_id: # result on search
            name = response[0]['sortable_name']
            email = response[0]['email']
            id = response[0]['id']
            verified_student_id = True
        else:
            print(f'\n!! Unable to verify id: {login_id} !!\n')
    
    res.student_name = name
    res.student_login = login_id
    res.student_id = id
    res.student_email = email
    res.ctx = 'main'

def get_student_grades(res):
    get_course_assignments(res)
    time.sleep(0.25)
    url = f'{res.w_base_url}/courses/{res.course_id}/students/submissions'
    modifiers = f'?student_ids[]={res.student_id}&response_fields[]=score&response_fields[]=assignment_id&exclude_response_fields[]=preview_url'

    print(url+modifiers)
    response = requests.get(url + modifiers, headers=res.w_header).json()
    print(response)
    
    scores = {assignment['assignment_id']: assignment['score'] for assignment in response}

    table_headers = ['Student'] + [res.course_assignments[_id]['name'] for _id in res.course_assignments]
    print('\t'.join(table_headers))

    row = [res.student_name]
    for _id in res.course_assignments:
        score = scores.get(_id, None)
        if score is None:
            row.append('-')
        else:
            max_points = res.course_assignments[_id]['points_possible']
            row.append(f'{int(score)}/{int(max_points)}')
    
    print('\t'.join(row))
    
    res.ctx = 'main'

def get_course_assignments(res):
    res.course_assignments = {}
    url = f'{res.w_base_url}/courses/{res.course_id}/assignments'
    modifiers = f'?response_fields[]=id&response_fields[]=name&response_fields[]=points_possible'
    response = requests.get(url + modifiers, headers=res.w_header).json()
    
    for assignment in response:
        _id = assignment['id']
        _name = assignment['name']
        _points_possible = assignment['points_possible']
        res.course_assignments[_id] = {'name': _name, 'points_possible': _points_possible}

if __name__ == '__main__':
    Menu().run(Res())