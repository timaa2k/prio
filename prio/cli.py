import datetime
import enum
import shutil
import webbrowser
from typing import Iterable, List, Union

import click
import tableformatter as tf
from colorama import Back

import priolib.client
import priolib.model


SERVER_ADDR = 'http://localhost:8080'
TERMINAL_COLUMNS = shutil.get_terminal_size((80, 20)).columns
DEFAULT_TASK_DISPLAY_OPTIONS = 'ID,TASK,URL,STATUS,CREATED,MODIFIED,AGE'


class TaskRowObject(object):

    def __init__(self) -> None:
        self.id = ''
        self.title = ''
        self.target = ''
        self.status = ''
        self.created = None
        self.modified = None

    @classmethod
    def From_task(cls, t: priolib.client.Task) -> 'TaskRowObject':
        o = cls()
        o.id = t.id
        o.title = t.title
        o.target = t.target
        o.status = t.status
        o.created = t.created
        o.modified = t.modified
        return o

    def get_created(self) -> str:
        return str(self.created)[:-21]

    def get_modified(self) -> str:
        return str(self.modified)[:-21]

    def get_age_days(self) -> str:
        if self.modified is not None:
            age = datetime.datetime.now(datetime.timezone.utc) - self.modified
            age_minutes = age.seconds / 60
            hours = int(age_minutes // 60)
            minutes = int(age_minutes % 60)
            seconds = int(age.seconds % 60)
            a = [
                (age.days, 'd'),
                (hours, 'h'),
                (minutes, 'm'),
                (seconds, 's'),
            ]
            age_string = ''
            count = 0
            i = 0
            while i < len(a) - 1:
                if a[i][0] < 1:
                    i += 1
                    continue
                age_string += str(a[i][0]) + a[i][1]
                if count == 1:
                    return age_string
                else:
                    i += 1
                    count += 1
            age_string += f'{seconds}s'
            return age_string
        return ''


class TaskDisplayOptions(enum.Enum):
    ID = 1
    TASK = 2
    URL = 3
    STATUS = 4
    CREATED = 5
    MODIFIED = 6
    AGE = 7


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
    total_width = TERMINAL_COLUMNS - ((len(options) - 1) * 4)
    mapping = {
        TaskDisplayOptions.ID: 'id',
        TaskDisplayOptions.TASK: 'title',
        TaskDisplayOptions.URL: 'target',
        TaskDisplayOptions.STATUS: 'status',
        TaskDisplayOptions.CREATED: 'get_created',
        TaskDisplayOptions.MODIFIED: 'get_modified',
        TaskDisplayOptions.AGE: 'get_age_days',
    }
    width = {
        TaskDisplayOptions.ID: len('xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'),
        TaskDisplayOptions.TASK: 0,
        TaskDisplayOptions.URL: 0,
        TaskDisplayOptions.STATUS: len('Blocked'),
        TaskDisplayOptions.CREATED: len('1996-12-19'),
        TaskDisplayOptions.MODIFIED: len('1996-12-19'),
        TaskDisplayOptions.AGE: len('99d60m'),
    }
    variable_width_opts = 0
    fixed_width = 0
    for opt in options:
        fixed_width += width[opt]
        if opt == TaskDisplayOptions.TASK or opt == TaskDisplayOptions.URL:
            variable_width_opts += 1

    remaining_width = total_width - fixed_width

    if variable_width_opts > 0:
        variable_width = int(remaining_width / variable_width_opts)
    else:
        variable_width = 0

    width[TaskDisplayOptions.TASK] = variable_width
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
        self.cell_pad_char = ' '

    def border_left_span(self, row_index: Union[int, None]) -> str:
        return ''

    def border_right_span(self, row_index: Union[int, None]) -> str:
        return ''

    def col_divider_span(self, row_index: Union[int, None]) -> str:
        return '    '

    def header_col_divider_span(self, row_index: Union[int, None]) -> str:
        return '    '


class EditGrid(tf.Grid):

    def __init__(self):
        super().__init__()
        self.cell_pad_char = ' '

    def border_left_span(self, row_index: Union[int, None]) -> str:
        return ''

    def border_right_span(self, row_index: Union[int, None]) -> str:
        return ''

    def col_divider_span(self, row_index: Union[int, None]) -> str:
        return '    '

    def header_col_divider_span(self, row_index: Union[int, None]) -> str:
        return '    '


def format_table(
    columns: List[TaskDisplayOptions],
    rows: List[priolib.model.Task],
) -> str:
    cols = task_col_obj(columns)
    return tf.generate_table(rows, cols, grid_style=TaskGrid())


@click.group(invoke_without_command=True)
@click.pass_context
@click.option(
    '--display-opts',
    default='STATUS,TASK,AGE',
    help='Task properties to display.',
)
def prio(ctx, **kwargs):
    if ctx.invoked_subcommand is None:
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

            tasks = \
                format_row_objects(status='Done', tasks=plan.done) + \
                format_row_objects(status='Today', tasks=plan.today) + \
                format_row_objects(status='Todo', tasks=plan.todo) + \
                format_row_objects(status='Blocked', tasks=plan.blocked) + \
                format_row_objects(status='Later', tasks=plan.later)

            print(format_table(opts, [TaskRowObject.From_task(t) for t in tasks]))


@prio.command()
@click.option(
    '--display-opts',
    default='TASK,URL',
    help='Task properties to display.',
)
def next(**kwargs):
    try:
        opts = parse_display_options(kwargs['display_opts'])
    except TaskDisplayOptionParseError:
        essage = (
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
            next = tasks[0]
            print(format_table(opts, [TaskRowObject.From_task(next)]))
            webbrowser.open_new(next.target)


@prio.command()
def edit(**kwargs):
    api = priolib.client.APIClient(SERVER_ADDR)
    plan = api.get_plan()
    opts = parse_display_options('STATUS,TASK,ID')
    tasks = \
        plan.done + \
        plan.today + \
        plan.todo + \
        plan.blocked + \
        plan.later
    cols = task_col_obj(opts)
    rows = [TaskRowObject.From_task(t) for t in tasks]
    table = tf.generate_table(rows, cols, grid_style=EditGrid())
    message = click.edit(table)
    if message is None:
        return
    p = priolib.model.Plan([], [], [], [], [])
    for line in message.split('\n')[:-2]:
        tokens = line.split()
        print(tokens)
        status = tokens[0]
        t = priolib.model.Task(
            status=status,
            id_=tokens[-1],
        )
        if status == 'Done':
            p.done.append(t)
        if status == 'Today':
            p.today.append(t)
        if status == 'Todo':
            p.todo.append(t)
        if status == 'Blocked':
            p.blocked.append(t)
        if status == 'Later':
            p.later.append(t)
    api.update_plan(p)


@prio.command()
@click.option(
    '--display-opts',
    default='ID,TASK,CREATED,MODIFIED',
    help='Task properties to display.',
)
def history(**kwargs):
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
        print(format_table(opts, [TaskRowObject.From_task(t) for t in tasks]))


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
def update(task_id, title, target, status):
    api = priolib.client.APIClient(SERVER_ADDR)
    api.update_task(priolib.model.Task(
        id_=task_id,
        title=title,
        target=target,
        status=status,
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
