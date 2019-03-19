#!/usr/bin/env python
"""
Manipulate SIMnet API endpoints to complete assignments through the command line

SIMnet is an easy-to-use online training and assessment solution for Microsoft
Office. It provides students with life-long access and unlimited practice on
Microsoft Word, Excel, Access and PowerPoint in addition to file management,
and operating systems content. With effective training modules as part ofSIMnet,
students can apply learning to course assignments and career opportunities.

https://www.mheducation.com/highered/simnet.html
"""

import json
import random
from typing import Dict, Generator
from urllib.parse import urlparse

import requests


class LoginError(Exception):
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
        self.session = requests.Session()

    def login(self, username: str, password: str) -> None:
        """
        Login to SIMnet

        Args:
            username: str SIMnet username
            password: str SIMnet password

        Raises:
            LoginError if login request is anything other than 200

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
            raise LoginError(
                "\n\n"
                f"HTTP Response: {req}\n"
                f"Reason: {req.reason}\n"
                f"Username: {username}\n"
                f"Password: {password}\n"
                f"Response: {req.text}\n"
            )
        self.logged_in = True

    def login_required(func):
        def _login_required(self, *args, **kwargs):
            if not self.logged_in:
                raise NotLoggedInError("You are not logged in.")
            func(self, *args, **kwargs)
        return _login_required

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
    def complete_simbook_assignment_from_dict(self, assignment_dict: Dict[str, str]):
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
    def complete_simpath_question(
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

        simpath_headers.update({"Content-Length": len(urlencode(simpath_data))})

        self.session.post(
            f"{self.base_url}/api/simpathexams/{loid}/saveanswer/{assignment_id}/1",
            headers=simpath_headers,
            params=simpath_data
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
