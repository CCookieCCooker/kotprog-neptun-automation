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
from getpass import getpass

from kotprog_neptun_automation.data_classes import ScheduleItem, Message


class AutomationWorker:
    def __init__(self, browser: WebDriver, timeout: int = 10):
        self._page_url = 'https://neptun.szte.hu/hallgato'
        self._login_failed_notification_id = 'validlogin_popupTable'

        self.browser = browser
        self.wait = WebDriverWait(self.browser, timeout)
        self.wait_one = WebDriverWait(self.browser, 1)

    # region Properties

    @property
    def page_url(self):
        return self._page_url

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
                self.wait.until(cond.any_of(cond.url_changes('https://neptun.szte.hu/hallgato/main.aspx')))
            except TimeoutException:
                print('A bejelentkezes sikertelen volt, mert hibas adatokat adott meg.\nProbalja ujra.')
            else:
                print('Sikeres bejelentkezes {} felhasznalokent.'.format(user))
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

        self.browser.find_element(By.ID, 'upFunction_c_common_timetable_upParent_tabOrarend_ctl00_up_timeTablePerson_upMaxLimit_personTimetable_upFilter_chklTimetableType_1').click()
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
