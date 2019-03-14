#!/usr/bin/env python
"""

"""

from pprint import pprint
import json
import random

import requests

# GET /api/simbooks/1753/save/4100480/362745223/ex16_sk_01_15_01?lessonType=SIMbookLesson&isComplete=true&timeSpent=11
# GET /api/simbooks/1753/save/4100480/362745216/ex16_sk_01_08_01?lessonType=SIMbookLesson&isComplete=true&timeSpent=33

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
        print(req.text)

    def complete_simbook_assignment(self, assignment_number: float, assignment_type: str = "ex"):
        """
        Complete a single simbook assignment

        Args:
            assignment_number: float Assignment number (e.g. 1.8, 2.4)
            assignment_type: str Type of assignment. Options include
                                                        excel 2016 ('ex16'),
        """
        assignment_headers = self.headers.copy()
        assignment_headers.update({
            "Referer": f"http://{self.school}.simnetonline.com/sb/?l=1753&a=4100480&t=5&redirect_uri=https%3A%2F%2F{self.school}.simnetonline.com%2Fsp%2F%23bo%2F4100480",
        })
        assignment_data = {
            "lessonType": "SIMbookLesson",
            "isComplete": True,
            "timeSpent": random.randint(30, 230),
        }
        # ex16_sk_01_08_01
        # excel 2016 skills 1.8 _01
        assignment = f"{assignment_type}"
        # url = f"/api/simbooks/{1753}/save/{4100480}/{362745216}/{}"
        #
        # req = self.session.get(
        #     f"{self.base_url}{url}",
        #     data=assignment_data,
        #     headers=assignment_headers,
        # )

if __name__ == "__main__":
    with open("config.json", mode="r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        username = config["username"]
        password = config["password"]
        school = config["school"]
        api_key = config["apiKey"]






































# I like to scroll :)
