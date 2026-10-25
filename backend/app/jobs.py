"""Single active local analysis, cooperative cancellation and bounded in-memory results."""

from copy import deepcopy
from threading import Event, Lock, Thread
from time import monotonic
from uuid import uuid4


TERMINAL = {'completed', 'cancelled', 'failed'}


class JobBusy(RuntimeError):
    pass


class Control:
    def __init__(self, job, lock):
        self.job = job
        self.lock = lock
        self.cancel_event = job['cancel_event']

    def update(self, **values):
        with self.lock:
            self.job['progress'].update(values)
            if self.cancel_event.is_set():
                self.job['progress']['phase'] = 'cancelling'


class AnalysisJobs:
    def __init__(self):
        self.lock = Lock()
        self.jobs = {}

    def start(self, payload, worker):
        with self.lock:
            if any(j['status'] not in TERMINAL for j in self.jobs.values()):
                raise JobBusy('다른 분석이 실행 중입니다. 완료하거나 중단한 후 다시 실행해 주세요.')
            while len(self.jobs) >= 20:
                self.jobs.pop(next(iter(self.jobs)))
            job_id = uuid4().hex
            job = dict(id=job_id, status='running', started=monotonic(), ended=None,
                       cancel_event=Event(), result=None, error=None,
                       request=payload.model_dump(), progress=dict(
                           phase='starting', current_url=payload.url, collected_documents=0,
                           analyzed_documents=0, failed_documents=0, pending_documents=1))
            self.jobs[job_id] = job
        def execute():
            try:
                result = worker(payload, Control(job, self.lock))
                with self.lock:
                    job['result'] = result.model_dump()
                    job['status'] = 'cancelled' if job['cancel_event'].is_set() else 'completed'
            except Exception as exc:
                with self.lock:
                    job['error'] = dict(status_code=getattr(exc, 'status_code', 500),
                                        detail=str(getattr(exc, 'detail', exc)))
                    job['status'] = 'cancelled' if job['cancel_event'].is_set() else 'failed'
            finally:
                with self.lock:
                    job['ended'] = monotonic()
                    job['progress']['phase'] = job['status']
        Thread(target=execute, name='yeardream-analysis', daemon=True).start()
        return job_id

    def snapshot(self, job_id):
        with self.lock:
            job = self.jobs[job_id]
            return dict(id=job_id, status=job['status'], request=dict(job['request']),
                        cancel_requested=job['cancel_event'].is_set(),
                        elapsed_seconds=round((job['ended'] or monotonic()) - job['started'], 1),
                        progress=dict(job['progress']), result=deepcopy(job['result']), error=job['error'])

    def cancel(self, job_id):
        with self.lock:
            job = self.jobs[job_id]
            if job['status'] not in TERMINAL:
                job['cancel_event'].set()
                job['progress']['phase'] = 'cancelling'
        return self.snapshot(job_id)
