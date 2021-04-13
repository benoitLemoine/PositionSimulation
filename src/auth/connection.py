from typing import List

import requests
from requests import Session

from data.fights import Fight


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

    @staticmethod
    def _get_code_from_url(url: str):
        return url.split('https://www.warcraftlogs.com/reports/')[1].split("#")[0]

    def get_fights(self, report_url: str) -> List[Fight]:
        query = """
            query ($code: String!){
                reportData {
                    report(code: $code){
                        fights(killType:Kills){
                            name 
                            difficulty
                            startTime 
                            endTime 
                            encounterID
                  }
                }
              }
            }
        """

        variables = {
            "code": self._get_code_from_url(url=report_url)
        }

        response = requests.post(self._api_url, headers=self._headers, json={"query": query, "variables": variables})
        response_json = response.json()

        fights = []
        for d_fight in response_json["data"]["reportData"]["report"]["fights"]:
            fight = Fight(**d_fight)

            if fight.difficulty == 5:
                fights.append(fight)

        return fights
