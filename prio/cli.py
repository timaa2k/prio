import datetime
import shutil
from typing import List

import click
import tableformatter as tf
from colorama import Back

import priolib.client
import priolib.model


SERVER_ADDR = 'http://localhost:8080'


def format_table(tasks: List[priolib.model.Task]) -> str:
    rows = tasks

    terminal = shutil.get_terminal_size((80, 20))

    total_width = terminal.columns
    status_width = int(0.08* total_width)
    id_width = int(0.32* total_width)
    title_width = int(0.15 * total_width)
    target_width = int(0.15 * total_width)
    age_width = int(0.20 * total_width)

    cols = (
        tf.Column(
            'STATUS',
            attrib='status',
            width=status_width,
            wrap_mode=tf.WrapMode.WRAP,
        ),
        tf.Column(
            'TITLE',
            attrib='title',
            width=title_width,
            wrap_mode=tf.WrapMode.WRAP,
        ),
        tf.Column(
            'URL',
            attrib='target',
            width=target_width,
            wrap_mode=tf.WrapMode.WRAP,
        ),
        tf.Column(
            'AGE',
            attrib='modified',
            width=age_width,
            wrap_mode=tf.WrapMode.WRAP,
        ),
        tf.Column(
            'ID',
            attrib='id',
            width=id_width,
            wrap_mode=tf.WrapMode.WRAP,
        ),
    )

    grid = tf.AlternatingRowGrid(Back.BLACK, Back.BLACK)
    grid = tf.SparseGrid()
    grid.show_header = True
    # grid.border_top = True
    # grid.border_header_divider = True
    # grid.col_divider = True
    # grid.row_divider = True
    return tf.generate_table(rows, cols, grid_style=grid)


@click.group()
def prio():
    pass


@prio.command()
def next(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    plan = api.get_plan()
    tasks = plan.done + \
        plan.today + \
        plan.todo + \
        plan.blocked + \
        plan.later
    print(f'{str(tasks[0])}')


@prio.command()
def now(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    plan = api.get_plan()

    def only_status(status) -> priolib.model.Task:
        return priolib.model.Task(id_='', status=status)

    def without_status(task) -> priolib.model.Task:
        task.status = ''
        return task

    def format_row_objects(
        status: str,
        tasks: List[priolib.model.Task],
    ) -> List[priolib.model.Task]:
        row_objects = []
        row_objects.append(priolib.model.Task(id_='', status=''))
        if len(tasks) == 0:
            row_objects.append(only_status(status))
        else:
            row_objects.append(tasks[0])
        return row_objects + [without_status(t) for t in tasks[1:]]

    row_objects = \
        format_row_objects(status='Done', tasks=plan.done) + \
        format_row_objects(status='Today', tasks=plan.today) + \
        format_row_objects(status='Todo', tasks=plan.todo) + \
        format_row_objects(status='Blocked', tasks=plan.blocked) + \
        format_row_objects(status='Later', tasks=plan.later)

    print(format_table(row_objects))


@prio.command()
def tasks(**kwargs):
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
