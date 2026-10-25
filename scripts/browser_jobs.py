"""Read a UI-launched job after the browser has rendered its terminal state."""


def ui_job_result(page, response, timeout=70000):
    if response.status != 202:
        return response.status, response.json()
    job_id = response.json()['id']
    page.wait_for_function("!document.querySelector('#analyze').disabled", timeout=timeout)
    job = page.request.get(response.url + '/' + job_id).json()
    assert job['status'] in {'completed', 'cancelled', 'failed'}, job
    if job['result'] is not None:
        return 200, job['result']
    return job['error']['status_code'], {'detail': job['error']['detail']}
