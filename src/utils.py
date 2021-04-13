def url_to_report_code(url: str) -> str:
    return url.split('https://www.warcraftlogs.com/reports/')[1].split("#")[0]
