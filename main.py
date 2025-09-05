# target is to get a nice little cli to to do some basic canvas
# tasks for work related stuffs
# search course, pull lists of students, grab and aggregate some grades across multiple
# instances of the same course. 
#
# maybe a toggle to set/unset a course favorite status?

from InquirerPy import inquirer

class Menu:
    def __init__(self):
        self.state = 'main'

    def run(self):
        while True:
            if self.state == 'main':
                self.main_menu()
            elif self.state == 'course_main_menu':
                self.course_main_menu()
            elif self.state == 'student_main_menu':
                self.student_main_menu()

    def main_menu(self):
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

    def course_main_menu(self):
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
        
    def student_main_menu(self):
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

if __name__ == '__main__':
    Menu().run()