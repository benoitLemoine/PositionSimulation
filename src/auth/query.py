from abc import ABC, abstractmethod
from typing import Dict

import requests


class WLogQuery(ABC):
    """Query interface made to separate GraphQL (long) queries from WLogConnection and keep it cleaner
    Note that type hinting will cause circular import"""

    @property
    @abstractmethod
    def raw_query(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def variables(self) -> Dict:
        raise NotImplementedError

    def execute(self, connection) -> requests.Response:
        return connection.post(json={"query": self.raw_query, "variables": self.variables})


class QueryFights(WLogQuery):
    raw_query = """
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

    def __init__(self, code: str):
        self._code = code

    @property
    def variables(self) -> Dict:
        return {"code": self._code}
