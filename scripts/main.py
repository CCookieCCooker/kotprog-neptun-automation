# Nev: Bernatsky Marton
# Neptun: CVZJ6X
# h: h146635

from selenium import webdriver
from kotprog_neptun_automation.automation import AutomationWorker

ACTION_PROMPT = ('Válasszon műveletet:\n'
                 'o: Órarend mentése | u: Olvasatlan üzenetek mentése | k: Kurzusfelvétel | a: Tanulámyi átlagok mentése\n'
                 'x: Kilépés\n-> ')

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    with webdriver.Chrome(options) as browser:
        worker = AutomationWorker(browser)

        worker.login()

        action = input(ACTION_PROMPT).lower()

        while action != 'x':
            match action:
                case 'o': worker.save_schedule()
                case 'u': worker.save_unread_messages()
                case 'k': worker.course_registration()
                case 'a': worker.save_averages()

            action = input(ACTION_PROMPT)
