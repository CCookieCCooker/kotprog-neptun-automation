import datetime
from datetime import time


DAYS_OF_WEEK = ['Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat', 'Vasárnap']

class DataItem:
    def __init__(self, title: str):
        self.title = title


class ScheduleItem(DataItem):
    def __init__(self, title: str, course_code: str, item_type: str, day_of_week: int, start_time: time, end_time: time):
        super().__init__(title)
        self.course_code = course_code
        self.item_type = item_type
        self.day_of_week = day_of_week
        self.start_time = start_time
        self.end_time = end_time

    def to_csv_values(self) -> [str]:
        return [
            self.title,
            self.course_code,
            self.item_type,
            DAYS_OF_WEEK[self.day_of_week],
            self.start_time.strftime('%H:%M'),
            self.end_time.strftime('%H:%M')
        ]


class Message(DataItem):
    def __init__(self, title: str, date: datetime.datetime):
        super().__init__(title)
        self.date = date

    def to_csv_values(self) -> [str]:
        return [
            self.date.strftime('%Y.%m.%d. %H:%M:%S'),
            self.title
        ]