import datetime
from typing import Any
from urllib.parse import urlencode

from app.integrations.bamboo.utils import (
    RequestMethods,
    count_working_days,
    send_bamboo_request,
)


def get_time_off_requests(employee_id: str) -> dict[str, Any]:
    start_date = datetime.date.today().strftime("%Y-%m-%d")
    end_date = (datetime.date.today() + datetime.timedelta(days=365)).strftime(
        "%Y-%m-%d"
    )
    params = {"start": start_date, "end": end_date, "employeeId": employee_id}
    encoded_params = urlencode(params)
    res = send_bamboo_request(
        url_path=f"/time_off/requests/?{encoded_params}",
        method=RequestMethods.GET,
    )

    return res.json()


def add_time_off_requests(employee_id: str, start_date: str, end_date: str) -> str:
    #  Count number of working days between start and end date
    data = {
        "status": "requested",  # Options: "approved", "denied" (or "declined"), "requested"
        "start": start_date,
        "end": end_date,
        "amount": count_working_days(start_date, end_date)
        * 8,  # 8h per working day (units are given in hours)
        "timeOffTypeId": "78",  # Indicates vacation, see: https://documentation.bamboohr.com/reference/get-time-off-types
    }

    url_path = f"/employees/{employee_id}/time_off/request"
    res = send_bamboo_request(
        url_path=url_path,
        method=RequestMethods.POST,
        data=data,
    )

    request_id = res.headers["Location"].split("/")[-1]
    return request_id


def cancel_time_off_requests(request_id: str) -> None:
    url_path = f"time_off/requests/{request_id}/status"
    res = send_bamboo_request(
        url_path=url_path,
        method=RequestMethods.POST,
        data={"status": "canceled"},
    )

    if res.status_code != 200:
        raise Exception("Error cancelling time off request")
