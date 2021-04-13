from typing import List

import requests
from requests import Session

from auth.query import QueryFights
from data.fights import Fight
from utils import url_to_report_code


class WLogConnection:
    def __init__(self, client_id: str, client_secret: str):
        self._token_url = "https://www.warcraftlogs.com/oauth/token"
        self._api_url = "https://www.warcraftlogs.com/api/v2/client"

        self._session = Session()
        self._token = self._get_token(client_id, client_secret)

    @property
    def _headers(self):
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _get_token(self, client_id: str, client_secret: str) -> str:
        response = self._session.post(self._token_url, data={"grant_type": "client_credentials"},
                                      auth=(client_id, client_secret))
        # TODO: better handle status code
        if response.status_code != 200:
            raise ValueError(response.reason)

        return response.json()["access_token"]

    def get(self, **kwargs) -> requests.Response:
        return self._session.get(url=self._api_url, **kwargs)

    def post(self, **kwargs) -> requests.Response:
        return self._session.post(url=self._api_url, headers=self._headers, **kwargs)

    def get_fights(self, report_url: str) -> List[Fight]:
        code = url_to_report_code(url=report_url)
        query = QueryFights(code=code)
        response = query.execute(connection=self)
        response_json = response.json()

        fights = []
        for d_fight in response_json["data"]["reportData"]["report"]["fights"]:
            fight = Fight(**d_fight)

            if fight.difficulty in [3, 4, 5]:
                fights.append(fight)

        return fights


