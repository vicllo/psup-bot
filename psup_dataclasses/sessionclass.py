from psup_dataclasses import *
from PySide6.QtCore import QDateTime, Qt

from constants import *

class Session:
    def __init__(self, course_file_name, event_file_name, courses=None):
        if courses is None:
            courses = {}

        self.course_file_name = course_file_name
        self.event_file_name = event_file_name
        self.courses = courses
        self.course_lines_read = 0
        self.event_lines_read = 0
        self.possible_events = {"Accepted": AcceptEvent,
                                "UserRefused": UserRefuseEvent,
                                "SchoolRefused": SchoolRefuseEvent,
                                "Waiting": WaitingListEvent,
                                "Proposition": PropositionEvent}

    def add_course(self, new_course):
        if new_course.name in self.courses.keys():
            return 0
        else:
            self.courses[new_course.name] = new_course
            return new_course

    def add_event(self, course, event):
        if course.name in self.courses:  # TODO : Check si le in renvoie la clé ou la valeur
            self.courses[course.name].add_event(event)
        else:
            self.add_course(course)
            self.courses[course.name].add_event(event)

    def read(self):
        with open(self.course_file_name, "r") as reading_file:
            read = reading_file.read()
        for raw_event in read.split("\n"):
            if raw_event:
                self.course_lines_read += 1
                selectivity = [None, None]
                name, selectivity[0], selectivity[1] = raw_event.split(",")
                selectivity = Selectivity(selectivity[0], selectivity[1])
                course = Course(name, selectivity)
                if not name in self.courses.values():
                    self.add_course(course)

        with open(self.event_file_name, "r") as reading_file:
            read = reading_file.read()
        for raw_event in read.split("\n"):
            if raw_event:
                self.event_lines_read += 1
                date, name, event_type, place = raw_event.split(",")
                date = QDateTime.fromString(date, Qt.DateFormat.ISODate)

                if name in self.courses:
                    course = self.courses[name]
                else:
                    raise ValueError("Course not found")
                if event_type == "Waiting":
                    event = all_event_kinds[event_type](date, course, place)
                else:
                    event = all_event_kinds[event_type](date, course)
                self.add_event(course, event)

    def write(self):
        events = []
        lines_to_write = [str(course) for course in self.courses.values()]
        if len(lines_to_write) >= self.course_lines_read:
            with open(self.course_file_name, "w") as writing_file:
                for line_to_write in lines_to_write:
                    writing_file.write(str(line_to_write) + "\n")
        else:
            raise MemoryError("The writing output smaller then the input. Check the logfiles if it is still complete")

        for course in self.courses.values():
            for event in course.events:
                events.append([event.date, event])
        lines_to_write = [x[1] for x in sorted(events, key=lambda x:x[0])]
        if self.event_lines_read <= len(lines_to_write):
            with open(self.event_file_name, "w") as writing_file:
                for line_to_write in lines_to_write:
                    writing_file.write(str(line_to_write)+"\n")
        else:
            print(self.event_lines_read, len(lines_to_write))
            raise MemoryError("The writing output smaller then the input. Check the logfiles if it is still complete")


class Course:
    def __init__(self, name, selectivity, events = []):
        self.name = name
        self.selectivity = selectivity
        self.events = []
        self.last_event = None
        if self.events:
            self.last_event = sorted(self.events, key=lambda x: x.date)[0]

    def __str__(self):
        return ",".join([self.name, str(self.selectivity)])

    def add_event(self, event):
        self.events.append(event)
        self.last_event = sorted(self.events, key=lambda x: x.date)[0]


class Selectivity:
    def __init__(self, places_available, previous_last_entry):
        self.places_available = places_available
        self.previous_last_entry = previous_last_entry

    def __str__(self):
        return str(self.places_available)+","+str(self.previous_last_entry)
