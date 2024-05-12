import csv
from datetime import datetime, timedelta, time
import time as tajm
from typing import Tuple

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as cond
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from getpass import getpass

from kotprog_neptun_automation.data_classes import ScheduleItem, Message, Course, Subcourse, SemesterAverages


class AutomationWorker:
    def __init__(self, browser: WebDriver, timeout: int = 10):
        self._page_url = 'https://neptun.szte.hu/hallgato'
        self.browser = browser
        self.wait = WebDriverWait(self.browser, timeout)
        self.wait_one = WebDriverWait(self.browser, 1)
        self._logged_in_user = None

    # region Properties

    @property
    def page_url(self):
        return self._page_url

    @property
    def logged_in_user(self):
        return self._logged_in_user

    @logged_in_user.setter
    def logged_in_user(self, user):
        self._logged_in_user = user

    # endregion Properties

    def login(self):
        self.browser.get(self.page_url)
        self.wait.until(cond.all_of(cond.presence_of_element_located((By.ID, 'user')),
                                    cond.presence_of_element_located((By.ID, 'pwd')),
                                    cond.presence_of_element_located((By.ID, 'btnSubmit'))))

        user_input = self.browser.find_element(By.ID, 'user')
        pwd_input = self.browser.find_element(By.ID, 'pwd')
        submit_input = self.browser.find_element(By.ID, 'btnSubmit')

        while True:
            user = input('Adja meg a Neptun bejelentkezesi azonositojat:\n-> ')
            user_input.clear()
            user_input.send_keys(user)

            pwd = getpass('Adja meg a Neptun bejelentkezesi jelszavat:\n-> ')
            pwd_input.clear()
            pwd_input.send_keys(pwd)

            submit_input.click()

            print('Bejelentkezes...')

            try:
                self.wait.until(cond.invisibility_of_element_located((By.ID, 'user')))
            except TimeoutException:
                print('A bejelentkezes sikertelen volt, mert hibas adatokat adott meg.\nProbalja ujra.')
            else:
                print('Sikeres bejelentkezes {} felhasznalokent.'.format(user))
                self.logged_in_user = user
                self.close_dialog()
                break

    def close_dialog(self):
        dialog_selector = '.ui-dialog.ui-widget.ui-widget-content.ui-corner-all.ui-front.ui-draggable.ui-resizable'
        close_selector = '{} .ui-dialog-titlebar-close'.format(dialog_selector)
        try:
            self.wait_one.until(cond.visibility_of_element_located((By.CSS_SELECTOR, dialog_selector)))
        except TimeoutException:
            return
        else:
            close_button = self.browser.find_element(By.CSS_SELECTOR, close_selector)
            close_button.click()

    def save_schedule(self):
        selected_day = input('Adjon meg egy napot eeee.hh.nn formatumban:\n(Az orarend arrol a hetrol fog keszulni, '
                             'amelybe ez a nap tartozik)\n(A mai nap hasznalatahoz irjon az "m" erteket adja meg)\n-> ')

        while not isinstance(selected_day, datetime):
            if selected_day == 'm':
                selected_day = datetime.now()
            else:
                try:
                    selected_day = datetime.strptime(selected_day, '%Y.%m.%d')
                except ValueError:
                    selected_day = input('Hiba, adjon meg egy helyes formatumu datumot:\n-> ')

        self.browser.find_element(By.ID, 'mb1_Tanulmanyok').click()
        self.browser.find_element(By.ID, 'mb1_Tanulmanyok_Órarend').click()

        self.wait.until(cond.visibility_of_element_located((By.CSS_SELECTOR, '#dvwkcontaienr th:nth-child(2)')))

        self.browser.find_element(By.ID,
                                  'upFunction_c_common_timetable_upParent_tabOrarend_ctl00_up_timeTablePerson_upMaxLimit_personTimetable_upFilter_chklTimetableType_1').click()
        tajm.sleep(0.5)
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'loadingpannel')))

        week_start, week_end = self.currently_displayed_week()

        while not (week_start <= selected_day <= week_end):
            print('start {}.{}.{}'.format(week_start.year, week_start.month, week_start.day))
            print('curr {}.{}.{}'.format(selected_day.year, selected_day.month, selected_day.day))
            print('end {}.{}.{}'.format(week_end.year, week_end.month, week_end.day))
            self.wait.until(cond.invisibility_of_element_located((By.ID, 'loadingpannel')))
            if week_start > selected_day:
                self.browser.find_element(By.ID, 'sfprevbtn').click()
            else:
                self.browser.find_element(By.ID, 'sfnextbtn').click()
            [week_start, week_end] = self.currently_displayed_week()

        tajm.sleep(0.5)
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'loadingpannel')))

        schedule_items = []
        day_divs = self.browser.find_elements(By.CLASS_NAME, 'tg-col-eventwrapper')
        for i in range(0, 7):
            schedule_item_divs = day_divs[i].find_elements(By.CLASS_NAME, 'chip')
            for schedule_item_div in schedule_item_divs:
                title_text = schedule_item_div.find_element(By.CSS_SELECTOR, 'dd > span').text
                type_title_code = title_text.split(']')
                item_type = type_title_code[0][1:]
                title_and_code = title_text.split(']')[1].split('-')[0]
                last_opening_bracket = title_and_code.rfind('(')
                title = title_and_code[:last_opening_bracket].strip()
                course_code = ''.join(c for c in title_and_code[last_opening_bracket:].strip() if c.isalnum())

                time_text = schedule_item_div.find_element(By.CSS_SELECTOR, 'dl > dt').text
                start_and_end = time_text.split('-')
                start_time = time.fromisoformat(start_and_end[0].strip())
                end_time = time.fromisoformat(start_and_end[1].strip())
                schedule_items.append(ScheduleItem(title, course_code, item_type, i, start_time, end_time))

        for schedule_item in schedule_items:
            print(''.join(str(v) for v in schedule_item.__dict__.values()))

        with open('schedule.csv', 'w') as file:
            writer = csv.writer(file, delimiter=',', lineterminator='\n')
            writer.writerow(['Kurzus neve', 'Kurzuskód', 'Esemény típusa', 'Hét napja', 'Kezdés', 'Befejezés'])
            for schedule_item in schedule_items:
                writer.writerow(schedule_item.to_csv_values())

    def currently_displayed_week(self) -> Tuple[datetime, datetime]:
        start_date_str = (self.browser.find_element(By.CSS_SELECTOR, '#dvwkcontaienr th:nth-child(2)')
                          .get_attribute('abbr'))

        start_date = datetime.strptime(start_date_str, '%Y/%m/%d')
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, microseconds=999999)

        return start_date, end_date

    def save_unread_messages(self):
        self.browser.find_element(By.ID, '_lnkInbox').click()
        self.wait.until(cond.visibility_of_element_located((By.CSS_SELECTOR,
                                                            '#c_messages_gridMessages_tablebottom .grid_RowCount')))

        page_size_select = Select(self.browser.find_element(By.ID, 'c_messages_gridMessages_ddlPageSize'))
        page_size_select.select_by_value('500')
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))

        while self.browser.find_element(By.CSS_SELECTOR, '.pagerlink_disabled').text != '1':
            self.browser.find_elements(By.CSS_SELECTOR, '.pagerlink')[0].click()
            self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))

        unread_messages = self.read_currently_displayed_unread_messages()

        while True:
            try:
                next_page_button = self.browser.find_element(By.CSS_SELECTOR, '.pagerlink_disabled + .pagerlink')
            except NoSuchElementException:
                break
            next_page_button.click()
            self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))
            unread_messages.extend(self.read_currently_displayed_unread_messages())

        with open('unread_messages.csv', 'w') as file:
            writer = csv.writer(file, delimiter=',', lineterminator='\n')
            writer.writerow(['Érkezés időpontja', 'Üzenet tárgya'])
            for unread_message in unread_messages:
                writer.writerow(unread_message.to_csv_values())

    def read_currently_displayed_unread_messages(self):
        unread_messages = []
        messages_table = self.browser.find_element(By.ID, 'c_messages_gridMessages_bodytable')
        message_rows = messages_table.find_elements(By.CSS_SELECTOR, 'tbody > tr.Row1_Bold')
        for message_row in message_rows:
            title = message_row.find_element(By.CSS_SELECTOR, 'span.link').text
            date = datetime.strptime(message_row.find_element(By.CSS_SELECTOR, 'td:last-child').text,
                                     '%Y. %m. %d. %H:%M:%S')
            unread_messages.append(Message(title, date))

        return unread_messages

    def course_registration(self):
        self.browser.find_element(By.ID, 'mb1_Targyak').click()
        self.browser.find_element(By.ID, 'mb1_Targyak_Targyfelvetel').click()

        semester_select = Select(self.browser.find_element(By.ID, 'upFilter_cmbTerms'))

        print('Valasszon felevet:')
        for i in range(0, len(semester_select.options)):
            print('{}: {}'.format(i, semester_select.options[i].text))

        while True:
            try:
                chosen_id = int(input('-> '))
                if chosen_id < 0 or chosen_id > len(semester_select.options) - 1:
                    raise ValueError
                break
            except ValueError:
                print('A megadott ertek nem helyes, probalja ujra')

        semester_select.select_by_visible_text(semester_select.options[chosen_id].text)
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'upFilter_h_addsubjects_searchpanel_animation')))
        self.browser.find_element(By.ID, 'upFilter_expandedsearchbutton').click()
        self.wait.until(cond.visibility_of_element_located((By.ID, 'h_addsubjects_gridSubjects_ddlPageSize')))
        page_size_select = Select(self.browser.find_element(By.ID, 'h_addsubjects_gridSubjects_ddlPageSize'))
        page_size_select.select_by_value('500')
        self.wait.until(cond.visibility_of_element_located((By.ID, 'imganimation')))
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))

        print('Kurzusok betoltese...')
        courses = self.read_currently_displayed_courses()

        while True:
            try:
                next_page_button = self.browser.find_element(By.CSS_SELECTOR, '.pagerlink_disabled + .pagerlink')
            except NoSuchElementException:
                break
            next_page_button.click()
            self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))
            courses.extend(self.read_currently_displayed_courses())

        for i in range(0, len(courses) - 1):
            print(f'[{i}] {courses[i].title} : {courses[i].subject_group} : {courses[i].credit_points} kredit : '
                  f'{"teljesített" if courses[i].completed else "még nem teljesített"}')

        input_str = 'a'
        while True:
            if input_str[0].isnumeric():
                try:
                    chosen_course_id = int(input_str)
                    break
                except ValueError:
                    print('Hibás formátum!')

            print('Válasszon kurzust a sorszáma megadásával, vagy adjon meg egy szöveget a kereséshez')
            input_str = input('-> ')
            for i in range(0, len(courses) - 1):
                if courses[i].title.lower().startswith(input_str.lower()):
                    print(
                        f'[{i}] {courses[i].title} : {courses[i].subject_group} : {courses[i].credit_points} kredit : '
                        f'{"teljesített" if courses[i].completed else "még nem teljesített"}')

        (self.browser.find_element(By.CSS_SELECTOR, f'#h_addsubjects_gridSubjects_bodytable > tbody > '
                                                    f'tr:nth-child({chosen_course_id}) > td:nth-child(12) > span')
         .click())

        self.wait.until(cond.visibility_of_element_located((By.ID, 'Addsubject_course1_gridCourses_bodytable')))

        subcourses = self.read_subcourses()

        if len(subcourses) > 1:
            print('A választott kurzushoz több időpont is tartozik:')
            for i in range(0, len(subcourses)):
                print(f'[{i}] {subcourses[i].title} : {subcourses[i].teachers} : '
                      f'{subcourses[i].timetable_info} : {subcourses[i].full}')
            while True:
                string = input('Válasszon az id megadásával\n-> ')
                try:
                    subcourse_id = int(string)
                    break
                except ValueError:
                    print('Hibás formátum!')
        else:
            subcourse_id = 0

        (self.browser.find_element(By.CSS_SELECTOR, f'#Addsubject_course1_gridCourses_bodytable > tbody > '
                                                    f'tr:nth-child({subcourse_id + 1}) > td:nth-child(14) > input')
         .click())

        self.browser.find_element(By.ID, 'function_update1').click()
        try:
            self.wait_one.until(cond.visibility_of_element_located((By.ID, '_imgError')))
            print('Hiba történt a kurzusfelvétel során!')
        except TimeoutException:
            print('A kurzusfelvétel sikeresen megtörtént!')

        self.wait.until(cond.visibility_of_element_located((By.CSS_SELECTOR, '.ui-dialog-footerbar.ui-widget-header'
                                                                             '.ui-corner-all.ui-helper-clearfix > '
                                                                             'input')))
        tajm.sleep(1)
        self.browser.execute_script('var dolgok = document.getElementsByClassName("ui-widget-overlay"); '
                                    'dolgok[0].remove();'
                                    'dolgok[0].remove();')

        self.browser.find_element(By.CSS_SELECTOR, '.ui-dialog-footerbar.ui-widget-header.ui-corner-all'
                                                   '.ui-helper-clearfix > input').click()

        self.browser.execute_script('document.getElementsByClassName("ui-dialog ui-widget ui-widget-content '
                                    'ui-corner-all ui-front ui-draggable ui-resizable")[0].remove()')

    def read_currently_displayed_courses(self):
        courses = []
        courses_table = self.browser.find_element(By.ID, 'h_addsubjects_gridSubjects_bodytable')
        course_rows = courses_table.find_elements(By.CSS_SELECTOR, 'tbody > tr')

        for course_row in course_rows:
            title = course_row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').text
            course_code = course_row.find_element(By.CSS_SELECTOR, 'td:nth-child(3)').text
            subject_group = course_row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text
            credit_points = int(course_row.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text)
            try:
                course_row.find_element(By.CSS_SELECTOR, 'td:nth-child(10) > img')
                completed = True
            except NoSuchElementException:
                completed = False

            courses.append(Course(
                title,
                course_code,
                subject_group,
                credit_points,
                completed
            ))

        return courses

    def read_subcourses(self):
        subcourses = []
        subcourses_table = self.browser.find_element(By.ID, 'Addsubject_course1_gridCourses_bodytable')
        subcourse_rows = subcourses_table.find_elements(By.CSS_SELECTOR, 'tbody > tr')

        for subcourse_row in subcourse_rows:
            code = subcourse_row.find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            if code == '':
                code = subcourse_row.find_element(By.CSS_SELECTOR, 'td:nth-child(2) > span').text
            applied_nums = subcourse_row.find_element(By.CSS_SELECTOR, 'td:nth-child(4)').text.split('/')
            full = applied_nums[0] >= applied_nums[2]
            timetable_info = subcourse_row.find_element(By.CSS_SELECTOR, 'td:nth-child(7)').text
            teachers = subcourse_row.find_element(By.CSS_SELECTOR, 'td:nth-child(8)').text

            subcourses.append(Subcourse(
                code,
                teachers,
                timetable_info,
                full
            ))

        return subcourses

    def save_averages(self):
        self.browser.find_element(By.ID, 'mb1_Tanulmanyok').click()
        self.browser.find_element(By.ID, 'mb1_Tanulmanyok_Tanulmanyiatlagok').click()

        # Varunk a betoltesre
        self.wait.until(cond.visibility_of_element_located((By.ID, 'imgcollapse_allsubrows')))

        # Lenyitunk minden felevet, ha ez meg nem tortent meg
        collapse_toggle = self.browser.find_element(By.ID, 'imgcollapse_allsubrows')
        if collapse_toggle.get_attribute('src').endswith('plus_2.gif'):
            self.browser.find_element(By.ID, 'imgcollapse_allsubrows').click()

        # Megvarjuk, hogy betoltse az osszes felev adatat
        self.wait.until(cond.invisibility_of_element_located((By.ID, 'imganimation')))

        table_body = self.browser.find_element(By.CSS_SELECTOR,
                                               '#h_officialnote_average_gridAverages_bodytable > tbody')
        semester_headers = self.browser.find_elements(By.CSS_SELECTOR, 'tr[hc="true"]')
        semester_subrows = self.browser.find_elements(By.CLASS_NAME, 'subrow')
        data = []

        for i in range(0, len(semester_headers) - 1):
            title = semester_headers[i].find_element(By.CSS_SELECTOR, 'td:nth-child(2)').text
            values = semester_subrows[i].find_elements(By.CSS_SELECTOR, 'strong')
            traditional_average = values[0].text
            credit_index = values[1].text
            adjusted_credit_index = values[2].text
            recognized_credits = values[3].text
            completed_credits = values[4].text
            summed_adjusted_credit_index = values[5].text
            summed_recognized_credits = values[6].text
            summed_completed_credits = values[7].text
            cummulated_completion = values[8].text
            two_semester_credits = values[9].text
            two_semester_weighted_average = values[10].text
            two_semester_adjusted_credit_index = values[11].text
            financial_study_group = values[12].text
            academic_study_group = values[13].text

            data.append(
                SemesterAverages(title, traditional_average, credit_index, adjusted_credit_index, recognized_credits,
                                 completed_credits, summed_adjusted_credit_index, summed_recognized_credits,
                                 summed_completed_credits,
                                 cummulated_completion, two_semester_credits, two_semester_weighted_average,
                                 two_semester_adjusted_credit_index, financial_study_group, academic_study_group))


        with open('averages.csv', 'w') as file:
            writer = csv.writer(file, delimiter=';', lineterminator='\n')
            writer.writerow(['Félév', 'Hagyományos átlag', 'Kreditindex', 'Korrigált kreditindex', 'Elismert kredit',
                             'Teljesített kredit', 'Göngyölt korr. kreditindex', 'Göngyölt elismert kredit',
                             'Göngyölt teljesítettt kredit', 'Kum.rel.össztelj.%', '2 féléves megsz.kredit',
                             '2 féléves súlyozott átlag', '2 féléves korr.kr.index', 'Pénzügyi tanuló csoport',
                             'Tanulmányi tanuló csoport'])
            for data_item in data:
                writer.writerow(data_item.to_csv_values())
