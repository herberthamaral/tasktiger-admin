from flask import redirect, url_for, abort
from flask_admin import BaseView, expose
import json
from tasktiger.task import Task

class TaskTigerView(BaseView):
    def __init__(self, tiger, *args, **kwargs):
        super(TaskTigerView, self).__init__(*args, **kwargs)
        self.tiger = tiger

    @expose('/')
    def index(self):
        queue_stats = self.tiger.get_queue_stats()
        return self.render('tasktiger_admin/tasktiger.html',
                           queue_stats=queue_stats.items())

    @expose('/<queue>/<state>/retry/', methods=['POST'])
    def task_retry_multiple(self, queue, state):
        LIMIT = 50
        n, tasks = Task.tasks_from_queue(self.tiger, queue, state, limit=LIMIT)
        for task in tasks:
            task.retry()
        return redirect(url_for('.queue_detail', queue=queue, state=state))

    @expose('/<queue>/<state>/<task_id>/')
    def task_detail(self, queue, state, task_id):
        LIMIT = 1000
        task = Task.from_id(self.tiger, queue, state, task_id,
                            load_executions=LIMIT)

        if not task:
            abort(404)

        executions_dumped = []
        for execution in task.executions:
            traceback = execution.pop('traceback', None)
            executions_dumped.append((
                json.dumps(execution, indent=2, sort_keys=True),
                traceback)
            )

        return self.render('tasktiger_admin/tasktiger_task_detail.html',
            queue=queue,
            state=state,
            task=task,
            task_dumped=json.dumps(task.data, indent=2, sort_keys=True),
            executions_dumped=executions_dumped,
        )

    @expose('/<queue>/<state>/<task_id>/retry/', methods=['POST'])
    def task_retry(self, queue, state, task_id):
        task = Task.from_id(self.tiger, queue, state, task_id)
        if not task:
            abort(404)
        task.retry()
        return redirect(url_for('.queue_detail', queue=queue, state=state))

    @expose('/<queue>/<state>/<task_id>/delete/', methods=['POST'])
    def task_delete(self, queue, state, task_id):
        task = Task.from_id(self.tiger, queue, state, task_id)
        if not task:
            abort(404)
        task.delete()
        return redirect(url_for('.queue_detail', queue=queue, state=state))

    @expose('/<queue>/<state>/')
    def queue_detail(self, queue, state):
        n, tasks = Task.tasks_from_queue(self.tiger, queue, state,
                                         load_executions=1)

        return self.render('tasktiger_admin/tasktiger_queue_detail.html',
            queue=queue,
            state=state,
            n=n,
            tasks=tasks,
        )