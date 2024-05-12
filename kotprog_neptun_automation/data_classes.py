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


class Course(DataItem):
    def __init__(self, title: str, course_code: str, subject_group: str, credit_points: int, completed: bool):
        super().__init__(title)
        self.course_code = course_code
        self.subject_group = subject_group
        self.credit_points = credit_points
        self.completed = completed


class Subcourse(DataItem):
    def __init__(self, title: str, teachers: str, timetable_info: str, full: bool):
        super().__init__(title)
        self.teachers = teachers
        self.timetable_info = timetable_info
        self.full = full

class SemesterAverages(DataItem):
    def __init__(self, title: str, traditional_average, credit_index, adjusted_credit_index, recognized_credits,
                 completed_credits, summed_adjusted_credit_index, summed_recognized_credits, summed_completed_credits,
                 cummulated_completion, two_semester_credits, two_semester_weighted_average,
                 two_semester_adjusted_credit_index, financial_study_group, academic_study_group):
        super().__init__(title)
        self.traditional_average = traditional_average
        self.credit_index = credit_index
        self.adjusted_credit_index = adjusted_credit_index
        self.recognized_credits = recognized_credits
        self.completed_credits = completed_credits
        self.summed_adjusted_credit_index = summed_adjusted_credit_index
        self.summed_recognized_credits = summed_recognized_credits
        self.summed_completed_credits = summed_completed_credits
        self.cummulated_completion = cummulated_completion
        self.two_semester_credits = two_semester_credits
        self.two_semester_weighted_average = two_semester_weighted_average
        self.two_semester_adjusted_credit_index = two_semester_adjusted_credit_index
        self.financial_study_group = financial_study_group
        self.academic_study_group = academic_study_group

    def to_csv_values(self) -> [str]:
        return [
            self.title,
            self.traditional_average,
            self.credit_index,
            self.adjusted_credit_index,
            self.recognized_credits,
            self.completed_credits,
            self.summed_adjusted_credit_index,
            self.summed_recognized_credits,
            self.summed_completed_credits,
            self.cummulated_completion,
            self.two_semester_credits,
            self.two_semester_weighted_average,
            self.two_semester_adjusted_credit_index,
            self.financial_study_group,
            self.academic_study_group
        ]
