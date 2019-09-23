import enum
import shutil
from typing import Iterable, List, Union

import click
import tableformatter as tf
from colorama import Back

import priolib.client
import priolib.model


SERVER_ADDR = 'http://localhost:8080'
TERMINAL_COLUMNS = shutil.get_terminal_size((80, 20)).columns
DEFAULT_TASK_DISPLAY_OPTIONS = 'ID,TITLE,URL,STATUS,PRIORITY,CREATED,MODIFIED,AGE'


class TaskDisplayOptions(enum.Enum):
    ID = 1
    TITLE = 2
    URL = 3
    STATUS = 4
    PRIORITY = 5
    CREATED = 6
    MODIFIED = 7
    AGE = 8


class TaskDisplayOptionParseError(Exception):
    pass


def parse_display_options(opts: str) -> List[TaskDisplayOptions]:
    options = []
    display_options = opts.split(',')
    for opt in display_options:
        try:
            opt_enum = TaskDisplayOptions[opt]
        except KeyError:
            raise TaskDisplayOptionParseError
        else:
            options.append(opt_enum)
    return options


def task_col_obj(
    options: List[TaskDisplayOptions],
) -> Iterable[tf.Column]:
    total_width = TERMINAL_COLUMNS - (len(options) + 5)
    mapping = {
        TaskDisplayOptions.ID: 'id',
        TaskDisplayOptions.TITLE: 'title',
        TaskDisplayOptions.URL: 'target',
        TaskDisplayOptions.STATUS: 'status',
        TaskDisplayOptions.PRIORITY: 'priority',
        TaskDisplayOptions.CREATED: 'created',
        TaskDisplayOptions.MODIFIED: 'modified',
        TaskDisplayOptions.AGE: 'get_age_days',
    }
    width = {
        TaskDisplayOptions.ID: len('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'),
        TaskDisplayOptions.TITLE: 0,
        TaskDisplayOptions.URL: 0,
        TaskDisplayOptions.STATUS: len('Blocked'),
        TaskDisplayOptions.PRIORITY: len('2147483647'),
        TaskDisplayOptions.CREATED: len('2019-09-22 00:27:54.845291+00:00'),
        TaskDisplayOptions.MODIFIED: len('2019-09-22 00:27:54.845291+00:00'),
        TaskDisplayOptions.AGE: len('99d'),
    }
    variable_width_opts = 0
    fixed_width = 0
    for opt in options:
        fixed_width += width[opt]
        if opt == TaskDisplayOptions.TITLE or opt == TaskDisplayOptions.URL:
            variable_width_opts += 1

    remaining_width = total_width - fixed_width

    if variable_width_opts > 0:
        variable_width = int(remaining_width / variable_width_opts)
    else:
        variable_width = 0

    width[TaskDisplayOptions.TITLE] = variable_width
    width[TaskDisplayOptions.URL] = variable_width

    def column(option: TaskDisplayOptions) -> tf.Column:
        return tf.Column(
            option.name,
            attrib=mapping[option],
            width=width[option],
            cell_padding=0,
            wrap_mode=tf.WrapMode.WRAP,
        )

    return [column(opt) for opt in options]


class TaskGrid(tf.Grid):

    def __init__(self):
        super().__init__()
        self.show_header = True
        self.border_top = True
        self.border_header_divider = True
        self.col_divider = True
        self.row_divider = True
        self.cell_pad_char = ''

    def border_left_span(self, row_index: Union[int, None]) -> str:
        return ''

    def border_right_span(self, row_index: Union[int, None]) -> str:
        return ''

    def col_divider_span(self, row_index: Union[int, None]) -> str:
        return '  '

    def header_col_divider_span(self, row_index: Union[int, None]) -> str:
        return '  '


def format_table(
    columns: List[TaskDisplayOptions],
    rows: List[priolib.model.Task],
) -> str:
    cols = task_col_obj(columns)
    return tf.generate_table(rows, cols, grid_style=TaskGrid())


@click.group()
def prio():
    pass


@prio.command()
@click.option(
    '--display-opts',
    default='STATUS,TITLE,URL,AGE',
    help='Task properties to display.',
)
def next(**kwargs):
    try:
        opts = parse_display_options(kwargs['display_opts'])
    except TaskDisplayOptionParseError:
        message = (
            'Invalid display options received.\n'
            'Display options must follow the format {options_format}'
        ).format(options_format=DEFAULT_TASK_DISPLAY_OPTIONS)
        print(message)
    else:
        api = priolib.client.APIClient(SERVER_ADDR)
        plan = api.get_plan()
        tasks = \
            plan.today + \
            plan.todo + \
            plan.blocked + \
            plan.later
        if len(tasks) == 0:
            print('No tasks found. Nothing to do.')
        else:
            print(format_table(opts, [tasks[0]]))


@prio.command()
@click.option(
    '--display-opts',
    default='STATUS,TITLE,URL,AGE',
    help='Task properties to display.',
)
def current(**kwargs):
    try:
        opts = parse_display_options(kwargs['display_opts'])
    except TaskDisplayOptionParseError:
        message = (
            'Invalid display options received.\n'
            'Display options must follow the format {options_format}'
        ).format(options_format=DEFAULT_TASK_DISPLAY_OPTIONS)
        print(message)
    else:
        api = priolib.client.APIClient(SERVER_ADDR)
        plan = api.get_plan()

        def without_status(task) -> priolib.model.Task:
            task.status = ''
            return task

        def format_row_objects(
            status: str,
            tasks: List[priolib.model.Task],
        ) -> List[priolib.model.Task]:
            row_objects = []
            # row_objects.append(priolib.model.Task(id_='', status=''))
            if len(tasks) == 0:
                row_objects.append(priolib.model.Task(id_='', status=status))
            else:
                row_objects.append(tasks[0])
            return row_objects + [without_status(t) for t in tasks[1:]]

        row_objects = \
            format_row_objects(status='Done', tasks=plan.done) + \
            format_row_objects(status='Today', tasks=plan.today) + \
            format_row_objects(status='Todo', tasks=plan.todo) + \
            format_row_objects(status='Blocked', tasks=plan.blocked) + \
            format_row_objects(status='Later', tasks=plan.later)

        print(format_table(opts, row_objects))


@prio.command()
@click.option(
    '--display-opts',
    default='ID,TITLE,URL,CREATED,MODIFIED',
    help='Task properties to display.',
)
def created(**kwargs):
    try:
        opts = parse_display_options(kwargs['display_opts'])
    except TaskDisplayOptionParseError:
        message = (
            'Invalid display options received.\n'
            'Display options must follow the format {options_format}'
        ).format(options_format=DEFAULT_TASK_DISPLAY_OPTIONS)
        print(message)
    else:
        api = priolib.client.APIClient(SERVER_ADDR)
        tasks = api.list_tasks()
        print(format_table(opts, tasks))


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
