from typing import List

import click
from tabulate import tabulate

import priolib.client
import priolib.model


SERVER_ADDR = 'http://localhost:8080'


def format_table(tasks: List[priolib.model.Task]) -> str:
    header = ['ID', 'Title', 'URL', 'Age']
    lines = []
    for t in tasks:
        line = [t.id, t.title, t.target, str(t.created)]
        lines.append(line)
    return tabulate(lines, header, tablefmt="fancy_grid")


@click.group()
def prio():
    pass


@prio.command()
def next(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    plan = api.get_plan()
    tasks = plan.done + plan.today + plan.todo + plan.blocked + plan.later
    print(f'{str(tasks[0])}')


@prio.command()
def list(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    plan = api.get_plan()
    print('+ Done:')
    print(format_table(plan.done))
    print('\n+ Today:')
    print(format_table(plan.today))
    print('\n+ Todo:')
    print(format_table(plan.todo))
    print('\n+ Blocked:')
    print(format_table(plan.blocked))
    print('\n+ Later:')
    print(format_table(plan.later))


@prio.command()
def all(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    tasks = api.list_tasks()
    print(format_table(tasks))


@prio.command()
@click.option('--status', default='Todo', help='Task status.')
@click.option('--title', prompt='Title', help='Task title.')
@click.option('--target', prompt='URL', help='Task target URL.')
def add(status, title, target):
    api = priolib.client.APIClient(SERVER_ADDR)
    task_id = api.create_task(title=title, target=target, status=status)
    print(f'Task {task_id} created.')


@prio.command()
@click.argument('task-id')
@click.option('--title', default=None, help='Task title.')
@click.option('--target', default=None, help='Task target URL.')
@click.option('--status', default=None, help='Task status.')
@click.option('--priority', type=int, default=None, help='Task priority within status.')
def update(task_id, title, target, status, priority):
    api = priolib.client.APIClient(SERVER_ADDR)
    api.update_task(priolib.model.Task(
        id_=task_id,
        title=title,
        target=target,
        status=status,
        priority=priority,
    ))
    print(f'Task {task_id} updated.')


@prio.command()
@click.argument('task-id')
def delete(task_id):
    api = priolib.client.APIClient(SERVER_ADDR)
    api.delete_task(task_id=task_id)
    print(f'Task {task_id} deleted.')


if __name__ == '__main__':
    prio()
