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
from urllib.parse import urlparse

import requests


class LoginError(Exception):
    """Failed to login using credentials provided"""

class SIMNet:
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

    def complete_simbook_assignment(self, url: str, assignment_id: int = 362745216) -> bool:
        """
        Complete a single simbook assignment

        Args:
            url: str Assignment url. Should look something like this:
                     http://{school}.simnetonline.com/sb/?
                     l=1744&
                     a=4100478&
                     t=5&
                     redirect_uri=https%3A%2F%{school}.simnetonline.com%2Fsp%2F%23bo%2F4100478
                     #ex16_sk_01_01
            assignment_id: int Assignment specific id. Length of 9 characters.
                               Successful completion does not depend on this value.
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

        # both `a` and `l` identify workbook chapters
        # `a` is used to identify more than the SIMbook
        # `a` has a length of 7 integers and `l` has a length of 4
        l, a, t, redirect_uri = parsed_url.query.split("&")
        assignment = parsed_url.fragment


        # url = f"/api/simbooks/{l}/save/{a}/{362745210}/{assignment}"
        url = f"/api/simbooks/{l.replace('l=', '')}/save/{a.replace('a=', '')}/{assignment_id}/{assignment}"
        print(url)

        req = self.session.get(
            f"{self.base_url}{url}",
            params=assignment_data,
            headers=assignment_headers,
        )
        return req.ok

if __name__ == "__main__":
    with open("config.json", mode="r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        username = config["username"]
        password = config["password"]
        school = config["school"]
        api_key = config["apiKey"]






































# I like to scroll :)
