# Nev: Bernatsky Marton
# Neptun: CVZJ6X
# h: h146635

from selenium import webdriver
from kotprog_neptun_automation.automation import AutomationWorker

ACTION_PROMPT = 'Valasszon muveletet:\no: orarend mentese | u: olvasatlan uzenetek mentese | x: kilepes\n-> '

if __name__ == '__main__':
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    with webdriver.Chrome(options) as browser:
        worker = AutomationWorker(browser)

        worker.login()

        action = input(ACTION_PROMPT)

        while action != 'x':
            match action:
                case 'o': worker.save_schedule()
                case 'u': worker.save_unread_messages()

            action = input(ACTION_PROMPT)
