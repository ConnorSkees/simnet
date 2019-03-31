#!/usr/bin/env python
"""
Manipulate SIMnet API endpoints to complete assignments through the command line

SIMnet is an easy-to-use online training and assessment solution for Microsoft
Office. It provides students with life-long access and unlimited practice on
Microsoft Word, Excel, Access and PowerPoint in addition to file management,
and operating systems content. With effective training modules as part ofSIMnet,
students can apply learning to course assignments and career opportunities.

https://www.mheducation.com/highered/simnet.html


What's the difference between a 'SIMpath exam' and a 'SIMnet exam'?
    SIMnet exams are the real deal and are often just called 'exam.'
    SIMpath exams are the pretest/lesson/posttest and
"""

import json
import random
from typing import Dict, Generator, List, Union
from urllib.parse import quote_plus, urlencode, urlparse

import requests


class SIMPathNotStartedError(Exception):
    """A SIMpath exam has not begun, so questions cannot be answered yet"""


class SIMNetExamNotStartedError(Exception):
    """A SIMnet exam has not begun, so questions cannot be answered yet"""


class LoginError(Exception):
    """An error related to logging in occurred"""


class CouldNotLoginError(LoginError):
    """Failed to login using credentials provided"""


class NotLoggedInError(LoginError):
    """User is not currently logged in"""


class SIMNet:
    """
    Base class for making requests to SIMnet API
    """
    def __init__(self, school: str, api_key: str) -> None:
        """
        Args:
            school: str Name of school (e.g. sonoma)
            api_key: str X-ApiKey found in request headers. Matches [a-zA-Z0-9]{64}
        """
        self.school = school.lower()

        self.base_url = f"http://{self.school}.simnetonline.com"
        self.headers = {
            "Host": f"{self.school}.simnetonline.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "X-ApiKey": api_key,
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "close",
        }

        self.logged_in = False
        self.is_in_simpath = False
        self.is_in_exam = False
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        """
        Login to SIMnet

        Args:
            username: str SIMnet username
            password: str SIMnet password

        Raises:
            CouldNotLoginError if login request is anything other than 200

        Returns:
            none
        """
        login_headers = self.headers.copy()
        login_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"https://{self.school}.simnetonline.com/sp/",
            "Content-Type": "application/json",
            "Content-Length": "28",
        })

        login_data = {
            "u": username,
            "p": password,
        }

        req = self.session.post(
            f"{self.base_url}/api/users/signin",
            json=login_data,
            headers=login_headers,
        )

        if not req.ok:
            raise CouldNotLoginError(
                "\n\n"
                f"HTTP Response: {req}\n"
                f"Reason: {req.reason}\n"
                f"Username: {username}\n"
                f"Password: {password}\n"
                f"Response: {req.text}\n"
            )
        self.logged_in = True

    def login_required(func):
        """Require that the user has already logged in before continuting"""
        def _login_required(self, *args, **kwargs):
            if not self.logged_in:
                raise NotLoggedInError("You are not logged in.")
            return func(self, *args, **kwargs)
        return _login_required

    def simpath_started_required(func):
        """Require that a SIMpath exam has started before continuting"""
        def _simpath_started_required(self, *args, **kwargs):
            if not self.is_in_simpath:
                raise SIMPathNotStartedError("You have not started a SIMpath exam.")
            return func(self, *args, **kwargs)
        return _simpath_started_required

    def exam_started_required(func):
        """Require that a SIMnet exam has started before continuting"""
        def _exam_started_required(self, *args, **kwargs):
            if not self.is_in_exam:
                raise SIMNetExamNotStartedError("You have not started a SIMpath exam.")
            return func(self, *args, **kwargs)
        return _exam_started_required

    @login_required
    def complete_simbook_assignment_from_url(
            self,
            url: str,
            task_complete_id: int = 362745216
        ) -> bool:
        """
        Complete a single simbook assignment from url given

        Args:
            url: str Assignment url. Should look something like this:
                     http://{school}.simnetonline.com/sb/?
                     l=1744&
                     a=4100478&
                     t=5&
                     redirect_uri=https%3A%2F%{school}.simnetonline.com%2Fsp%2F%23bo%2F4100478
                     #ex16_sk_01_01
            task_complete_id: int Task specific id. Matches \\d{9}
                              Successful completion does not depend on this value.

        Returns:
            bool Whether or not the assignment was successfully completed
        """
        assignment_headers = self.headers.copy()
        assignment_headers.update({
            "Referer": url,
        })

        assignment_data = {
            "lessonType": "SIMbookLesson",
            "isComplete": True,
            "timeSpent": random.randint(30, 230),
        }

        parsed_url = urlparse(url)

        # both `assignment_id` and `loid` identify workbook chapters
        # though, I am not totally sure of the difference
        # `assignment_id` has a length of 7 integers and `loid` has a length of 4
        loid, assignment_id, _, _ = parsed_url.query.split("&")
        page_slug = parsed_url.fragment

        loid = loid.replace('l=', '')
        assignment_id = assignment_id.replace('a=', '')

        url = f"/api/simbooks/{loid}/save/{assignment_id}/{task_complete_id}/{page_slug}"

        req = self.session.get(
            f"{self.base_url}{url}",
            params=assignment_data,
            headers=assignment_headers,
        )
        return req.ok

    @login_required
    def complete_simbook_assignment_from_dict(self, assignment_dict: Dict[str, Union[str, int]]) -> bool:
        """
        Complete a single simbook assignment from dictionary generated by
        `get_simbook_assignments()`

        Args:
            assignment_dict: dict[str, str] Dictionary generated by `get_simbook_assignments()`
                                            Contains 'loid'
                                                     'assignment_id'
                                                     'task_complete_id'
                                                     'page_slug'

        Returns:
            bool Whether or not the assignment was successfully completed
        """
        loid = assignment_dict["loid"]
        assignment_id = assignment_dict["assignment_id"]
        task_complete_id = assignment_dict["task_complete_id"]
        page_slug = assignment_dict["page_slug"]

        assignment_headers = self.headers.copy()
        assignment_headers.update({
            "Referer": f"http://{self.school}.simnetonline.com/sb/?l={loid}&a={assignment_id}&t=5&redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23bo%2F{assignment_id}",
        })

        assignment_data = {
            "lessonType": "SIMbookLesson",
            "isComplete": True,
            "timeSpent": random.randint(30, 230),
        }

        url = f"/api/simbooks/{loid}/save/{assignment_id}/{task_complete_id}/{page_slug}"

        req = self.session.get(
            f"{self.base_url}{url}",
            params=assignment_data,
            headers=assignment_headers,
        )
        return req.ok

    @login_required
    def get_simbook_assignments(
            self,
            assignment_id: str
        ) -> Generator[Dict[str, str], None, None]:
        """
        Args:
            assignment_id: str Assignment ID matching \\d{7}

        Yields:
            dict[str, str] Information necessary to create request
        """
        simbook_assignment_headers = self.headers.copy()
        simbook_assignment_headers.update({
            "Referer": f"https://{self.school}.simnetonline.com/sp/"
        })

        req = self.session.get(
            f"{self.base_url}/api/assignments/simbooks/{assignment_id}/details",
            params={"lessonType": "0"},
            headers=simbook_assignment_headers,
        )

        results = json.loads(req.text)["results"][0]
        assignment_id = results["assignmentID"]
        loid = results["loid"]
        for task in results["tasks"]:
            task_complete_id = task["taskCompleteID"]
            page_slug = task["pageSlug"]
            is_completed = task["timesCompleted"] > 0

            # url = f"/api/simbooks/{loid}/save/{assignment_id}/{task_complete_id}/{page_slug}"
            yield ({
                "loid": loid,
                "assignment_id": assignment_id,
                "task_complete_id": task_complete_id,
                "page_slug": page_slug,
                "is_completed": is_completed
            })

    @login_required
    def complete_simpath_exam(self, assignment_id: int) -> None:
        """
        Complete a SIMpath exam

        assignment_id: int Length of 7. Probably starts with `4`
                           Can be found in url
        """
        simpath_headers = self.headers.copy()
        simpath_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"http://{self.school}.simnetonline.com/sp/?redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23pa%2F{assignment_id}",
        })

        # loid: int Length of 6. Probably starts with `1`
        loid = json.loads(self.session.get(
            f"{self.base_url}/api/assignments/simpaths/{assignment_id}/details?lessonType=4"
        ).text)["loid"]

        question_dicts: List[Dict[str, Union[int, str]]] = []

        req = self.session.get(
            f"{self.base_url}/api/simpathexams/{loid}/init/{assignment_id}/1"
        )

        j = json.loads(req.text)
        seconds_remaining = 600_000
        assignment_id = j["assignmentID"]
        loid = j["loid"]
        content_version = j["contentVersion"]
        for question in j["questions"]:
            question_id = question["id"]
            readable_answer = question["hint"]
            attempt = question["attempts"] + 1
            seconds_spent = random.randint(23, 200)
            seconds_remaining -= seconds_spent
            question_dicts.append({
                "assignment_id": assignment_id,
                "loid": loid,
                "question_id": question_id,
                "readable_answer": readable_answer,
                "attempt": attempt,
                "content_version": content_version,
                "seconds_spent": seconds_spent,
                "seconds_remaining": seconds_remaining
            })

        # start exam
        self.session.get(
            f"{self.base_url}/api/simpathexams/{loid}/start/{assignment_id}/1"
        )

        self.is_in_simpath = True

        for question in question_dicts:
            self.complete_simpath_question(**question)

        # end exam
        self.session.get(
            f"{self.base_url}/api/simpathexams/{loid}/end/{assignment_id}/1?seconds={seconds_remaining}"
        )

        self.is_in_simpath = False

    @login_required
    @simpath_started_required
    def _complete_simpath_question(
            self,
            *,
            loid: int,
            assignment_id: int,
            question_id: str,
            seconds_spent: int,
            seconds_remaining: int,
            readable_answer: str,
            content_version: str = "V3",
            attempt: int = 1,
        ):
        """
        Complete a single question during a SIMpath exam
            Keyword arguments are forced because the integers are too similar

        loid: int Length of 6. Probably starts with `1`
        assignment_id: int Length of 7. Probably starts with `4`
        question_id: str Question specific id. (e.g. ex16_sk_02_01_01_p_01)
        seconds_spent: int Amount of time spent working on the question
        content_version: str SIMnet specific versioning system.
                             Will likely be "V3"
        attempt: int Current number of attempts + 1
        readable_answer: str List of steps taken. For example, if the question
                             is 'Copy the selected text,' this parameter would
                             be <span class="username">You</span> clicked
                             <b>Ctrl + C</b>.
        """
        simpath_headers = self.headers.copy()
        simpath_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"http://{self.school}.simnetonline.com/sp/?redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23pa%2F{assignment_id}",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })
        simpath_data = {
            "contentVersion": content_version,
            "questionID": question_id, #ex16_sk_02_01_01_p_01
            "attempt": attempt,
            "answer": {},
            "readableAnswer": quote_plus(readable_answer),
            "secondsRemaining": min(seconds_remaining, 600_000-seconds_spent),
            "secondsSpent": seconds_spent,
            "isCorrect": True,
            "lessonType": 4
        }

        simpath_headers.update({"Content-Length": str(len(urlencode(simpath_data)))})

        self.session.post(
            f"{self.base_url}/api/simpathexams/{loid}/saveanswer/{assignment_id}/1",
            headers=simpath_headers,
            params=simpath_data
        )

    @login_required
    def complete_exam(self, assignment_id: int) -> None:
        """
        Complete a SIMnet exam

        assignment_id: int Length of 7. Probably starts with `4`
                           Can be found in url
        """
        simpath_headers = self.headers.copy()
        simpath_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"http://{self.school}.simnetonline.com/sp/?redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23pa%2F{assignment_id}",
        })

        # loid: int Length of 6. Probably starts with `1`
        loid = json.loads(self.session.get(
            f"{self.base_url}/api/assignments/exams/{assignment_id}/details"
        ).text)["loid"]

        question_dicts: List[Dict[str, Union[int, str]]] = []

        req = self.session.get(
            f"{self.base_url}/api/simnetexams/{loid}/init/{assignment_id}/1"
        )

        j = json.loads(req.text)
        seconds_remaining = 600_000
        assignment_id = j["assignmentID"]
        loid = j["loid"]
        content_version = j["contentVersion"]
        for question in j["questions"]:
            question_id = question["id"]
            readable_answer = question["hint"]
            attempt = question["attempts"] + 1
            seconds_spent = random.randint(23, 200)
            seconds_remaining -= seconds_spent
            question_dicts.append({
                "assignment_id": assignment_id,
                "loid": loid,
                "question_id": question_id,
                "readable_answer": readable_answer,
                "attempt": attempt,
                "content_version": content_version,
                "seconds_spent": seconds_spent,
                "seconds_remaining": seconds_remaining
            })

        # start exam
        self.session.get(
            f"{self.base_url}/api/simnetexams/{loid}/start/{assignment_id}/1"
        )

        self.is_in_exam = True

        for question in question_dicts:
            time.sleep(question["seconds_spent"])
            self._complete_exam_question(**question)

        # end exam
        self.session.get(
            f"{self.base_url}/api/simnetexams/{loid}/end/{assignment_id}/1?seconds={seconds_remaining}"
        )

        self.is_in_exam = False

    @login_required
    @exam_started_required
    def _complete_exam_question(
            self,
            *,
            loid: int,
            assignment_id: int,
            question_id: str,
            seconds_spent: int,
            seconds_remaining: int,
            readable_answer: str,
            content_version: str = "V3",
            attempt: int = 1,
        ) -> None:
        """
        Complete a single question during a SIMnet exam
            Keyword arguments are forced because the integers are too similar

        loid: int Length of 6. Probably starts with `1`
        assignment_id: int Length of 7. Probably starts with `4`
        question_id: str Question specific id. (e.g. ex16_sk_02_01_01_p_01)
        seconds_spent: int Amount of time spent working on the question
        content_version: str SIMnet specific versioning system.
                             Will likely be "V3"
        attempt: int Current number of attempts + 1
        readable_answer: str List of steps taken. For example, if the question
                             is 'Copy the selected text,' this parameter would
                             be <span class="username">You</span> clicked
                             <b>Ctrl + C</b>.
        """
        exam_headers = self.headers.copy()
        exam_headers.update({
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"http://{self.school}.simnetonline.com/sp/?redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23se%2F{assignment_id}%2Fresult%2F1",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        })

        exam_data = {
            "contentVersion": content_version,
            "questionID": question_id, #ex16_sk_02_01_01_p_01
            "attempt": attempt,
            "answer": {},
            "readableAnswer": quote_plus(readable_answer),
            "secondsRemaining": min(seconds_remaining, 600_000-seconds_spent),
            "secondsSpent": seconds_spent,
            "isCorrect": True,
        }

        exam_headers.update({"Content-Length": str(len(urlencode(exam_data)))})

        self.session.post(
            f"/api/simnetexams/{loid}/saveanswer/{assignment_id}/1",
            headers=exam_headers,
            params=exam_data
        )


if __name__ == "__main__":
    with open("test_config.json", mode="r", encoding="utf-8") as config_file:
        CONFIG = json.load(config_file)
        USERNAME = CONFIG["username"]
        PASSWORD = CONFIG["password"]
        SCHOOL = CONFIG["school"]
        API_KEY = CONFIG["apiKey"]
    S = SIMNet(SCHOOL, API_KEY)
    S.login(USERNAME, PASSWORD)






































# I like to scroll :)
