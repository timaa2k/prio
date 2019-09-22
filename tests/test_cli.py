import datetime
import uuid

import pytest
import responses
from http import HTTPStatus

from priolib.client import APIClient, APIError
from priolib.model import Task


def generate_task_id() -> str:
    return str(uuid.uuid4())



class TestAPIClient:

    @pytest.fixture()
    def test_id(self) -> str:
        return generate_task_id()

    @pytest.fixture()
    def api(self) -> 'APIClient':
        return APIClient(addr='https://api.taskpr.io')

    @responses.activate
    def test_create_task(self, api, test_id):
        responses.add(
            method=responses.POST,
            url=f'{api.addr}/tasks',
            headers={'Location': f'{api.addr}/tasks/{test_id}'},
            status=HTTPStatus.CREATED.value,
        )
        task_id = api.create_task(
            title='First task',
            target='https://example.com',
            status='Today',
        )
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/tasks'
        assert task_id == test_id

    @responses.activate
    def test_create_task_failed(self, api) -> None:
        responses.add(
            method=responses.POST,
            url=f'{api.addr}/tasks',
            json={
                'reason': 'Internal Server Error',
                'message': 'Task could not be created.',
                'details': 'A task storage error occurred.',
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        with pytest.raises(APIError) as exc:
            api.create_task(
                title='First task',
                target='https://example.com',
            )
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == f'{api.addr}/tasks'
        assert exc.value.reason == 'Internal Server Error'
        assert exc.value.message == 'Task could not be created.'
        assert exc.value.details == 'A task storage error occurred.'

    @responses.activate
    def test_get_task(self, api, test_id):
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/tasks/{test_id}',
            json={
                'createdDate': '2007-01-25T12:00:00Z',
                'id': test_id,
                'kind': 'Task',
                'modifiedDate': '2007-01-25T12:00:00Z',
                'priority': 1,
                'selfLink': f'{api.addr}/tasks/{test_id}',
                'title': 'First task',
                'targetLink': 'https://example.com',
                'status': 'Later',
            },
            status=HTTPStatus.OK.value,
        )
        task = api.get_task(task_id=test_id)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'
        assert task.id == test_id
        assert task.title == 'First task'
        assert task.target == 'https://example.com'
        assert task.status == 'Later'
        assert task.priority == 1
        assert task.created == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)
        assert task.modified == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_get_task_failed(self, api, test_id):
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/tasks/{test_id}',
            json={
                'reason': 'Not Found',
                'message': 'Task not found.',
                'details': 'Task does not exist in task storage.',
            },
            status=HTTPStatus.NOT_FOUND.value,
        )
        with pytest.raises(APIError) as exc:
            api.get_task(task_id=test_id)
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'
        assert exc.value.reason == 'Not Found'
        assert exc.value.message == 'Task not found.'
        assert exc.value.details == 'Task does not exist in task storage.'

    @responses.activate
    def test_delete_task(self, api, test_id):
        responses.add(
            method=responses.DELETE,
            url=f'{api.addr}/tasks/{test_id}',
            status=HTTPStatus.NO_CONTENT.value,
        )
        api.delete_task(task_id=test_id)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'

    @responses.activate
    def test_delete_task_failed(self, api, test_id):
        responses.add(
            method=responses.DELETE,
            url=f'{api.addr}/tasks/{test_id}',
            json={
                'reason': 'Internal Server Error',
                'message': 'Task could not be deleted.',
                'details': 'A task storage error occurred.',
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        with pytest.raises(APIError) as exc:
            api.delete_task(task_id=test_id)
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'
        assert exc.value.reason == 'Internal Server Error'
        assert exc.value.message == 'Task could not be deleted.'
        assert exc.value.details == 'A task storage error occurred.'

    @responses.activate
    def test_update_task(self, api, test_id):
        responses.add(
            method=responses.PATCH,
            url=f'{api.addr}/tasks/{test_id}',
            status=HTTPStatus.NO_CONTENT.value,
        )
        updated = Task(
            id_=test_id,
            title='Updated task',
            target='https://new.com',
        )
        api.update_task(task=updated)
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'

    @responses.activate
    def test_update_task_failed(self, api, test_id):
        responses.add(
            method=responses.PATCH,
            url=f'{api.addr}/tasks/{test_id}',
            json={
                'reason': 'Internal Server Error',
                'message': 'Task could not be updated.',
                'details': 'A task storage error occurred.',
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        updated = Task(
            id_=test_id,
            title='Updated task',
            target='https://new.com',
        )
        with pytest.raises(APIError) as exc:
            api.update_task(task=updated)
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == f'{api.addr}/tasks/{test_id}'
        assert exc.value.reason == 'Internal Server Error'
        assert exc.value.message == 'Task could not be updated.'
        assert exc.value.details == 'A task storage error occurred.'

    @responses.activate
    def test_list_tasks(self, api) -> None:
        id_1 = generate_task_id()
        id_2 = generate_task_id()
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/tasks',
            json={
                'kind': 'Collection',
                'self': f'{api.addr}/tasks',
                'contents': [
                    {
                        'createdDate': '2007-01-25T12:00:00Z',
                        'id': id_1,
                        'kind': 'Task',
                        'modifiedDate': '2007-01-25T12:00:00Z',
                        'priority': 1,
                        'selfLink': f'{api.addr}/tasks/{id_1}',
                        'targetLink': 'https://swiss.com',
                        'title': 'Buy cheese',
                        'status': 'Later',
                    },
                    {
                        'createdDate': '2007-01-25T12:00:00Z',
                        'id': id_2,
                        'kind': 'Task',
                        'modifiedDate': '2007-01-25T12:00:00Z',
                        'priority': 1,
                        'selfLink': f'{api.addr}/tasks/{id_2}',
                        'targetLink': 'https://stuff.org',
                        'title': 'Do stuff',
                        'status': 'Today',
                    },
                ],
            },
            status=HTTPStatus.OK.value,
        )
        tasks = api.list_tasks()
        assert len(responses.calls) == 1
        url = f'{api.addr}/tasks'
        assert responses.calls[0].request.url == url
        assert len(tasks) == 2
        assert tasks[0].id == id_1
        assert tasks[0].title == 'Buy cheese'
        assert tasks[0].target == 'https://swiss.com'
        assert tasks[0].status == 'Later'
        assert tasks[0].priority == 1
        assert tasks[0].created == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)
        assert tasks[0].modified == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)
        assert tasks[1].id == id_2
        assert tasks[1].title == 'Do stuff'
        assert tasks[1].target == 'https://stuff.org'
        assert tasks[1].status == 'Today'
        assert tasks[1].priority == 1
        assert tasks[1].created == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)
        assert tasks[1].modified == datetime.datetime(
            2007, 1, 25, 12, 0, tzinfo=datetime.timezone.utc)

    @responses.activate
    def test_list_tasks_failed(self, api) -> None:
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/tasks',
            json={
                'reason': 'Internal Server Error',
                'message': 'Task could not be retrieved.',
                'details': 'A task storage error occurred.',
            },
            status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        )
        with pytest.raises(APIError) as exc:
            api.list_tasks()
        assert len(responses.calls) == 3
        assert responses.calls[0].request.url == f'{api.addr}/tasks'
        assert exc.value.reason == 'Internal Server Error'
        assert exc.value.message == 'Task could not be retrieved.'
        assert exc.value.details == 'A task storage error occurred.'

    @responses.activate
    def test_get_plan(self, api) -> None:
        id_1 = generate_task_id()
        id_2 = generate_task_id()
        id_3 = generate_task_id()
        id_4 = generate_task_id()
        id_5 = generate_task_id()
        id_6 = generate_task_id()
        responses.add(
            method=responses.GET,
            url=f'{api.addr}/plan',
            json={
                'kind': 'OrderedList',
                'self': f'{api.addr}/plan',
                'contents': [
                    {
                        'kind': 'OrderedList',
                        'status': 'Done',
                        'contents': [
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_1,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 1,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Done',
                            },
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_6,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 2,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Done',
                            },
                        ],
                    },
                    {
                        'kind': 'OrderedList',
                        'status': 'Today',
                        'contents': [
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_2,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 1,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Today',
                            },
                        ],
                    },
                    {
                        'kind': 'OrderedList',
                        'status': 'Todo',
                        'contents': [
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_3,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 1,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Todo',
                            },
                        ],
                    },
                    {
                        'kind': 'OrderedList',
                        'status': 'Blocked',
                        'contents': [
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_4,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 1,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Blocked',
                            },
                        ],
                    },
                    {
                        'kind': 'OrderedList',
                        'status': 'Later',
                        'contents': [
                            {
                                'createdDate': '2007-01-25T12:00:00Z',
                                'id': id_5,
                                'kind': 'Task',
                                'modifiedDate': '2007-01-25T12:00:00Z',
                                'priority': 1,
                                'selfLink': f'{api.addr}/tasks/{id_1}',
                                'targetLink': 'https://swiss.com',
                                'title': 'Buy cheese',
                                'status': 'Later',
                            },
                        ],
                    },
                ],
            },
            status=HTTPStatus.OK.value,
        )
        plan = api.get_plan()
        assert len(responses.calls) == 1
        url = f'{api.addr}/plan'
        assert responses.calls[0].request.url == url
        assert len(plan.done) == 2
        assert plan.done[0].id == id_1
        assert plan.done[1].id == id_6
        assert len(plan.today) == 1
        assert plan.today[0].id == id_2
        assert len(plan.todo) == 1
        assert plan.todo[0].id == id_3
        assert len(plan.blocked) == 1
        assert plan.blocked[0].id == id_4
        assert len(plan.later) == 1
        assert plan.later[0].id == id_5
