from __future__ import unicode_literals, division, absolute_import
from builtins import *  # pylint: disable=unused-import, redefined-builtin

from functools import partial

from flexget import options
from flexget.logger import console
from flexget.terminal import CLITable, CLITableError, table_parser
from flexget.manager import Session
from flexget.event import event
from flexget.plugins.filter.retry_failed import FailedEntry


def do_cli(manager, options):
    if options.failed_action == 'list':
        list_failed(options)
    elif options.failed_action == 'clear':
        clear_failed(manager)


def list_failed(options):
    ww = partial(CLITable.word_wrap, max_length=options.max_column_width)
    with Session() as session:
        results = session.query(FailedEntry).all()
        header = ['#', 'Title', 'Fail count', 'Reason', 'Failure time']
        table_data = [header]
        for entry in results:
            table_data.append(
                [entry.id, ww(entry.title), entry.count, '' if entry.reason == 'None' else entry.reason,
                 entry.tof.strftime('%Y-%m-%d %H:%M')])
    table = CLITable(options.table_type, table_data, check_size=options.check_size)
    table.table.justify_columns[0] = 'center'
    try:
        console(table.output)
    except CLITableError as e:
        console('ERROR: %s' % str(e))


def clear_failed(manager):
    session = Session()
    try:
        results = session.query(FailedEntry).delete()
        console('Cleared %i items.' % results)
        session.commit()
        if results:
            manager.config_changed()
    finally:
        session.close()


@event('options.register')
def register_parser_arguments():
    parser = options.register_command('failed', do_cli, help='list or clear remembered failures')
    subparsers = parser.add_subparsers(dest='failed_action', metavar='<action>')
    subparsers.add_parser('list', help='list all the entries that have had failures', parents=[table_parser])
    subparsers.add_parser('clear', help='clear all failures from database, so they can be retried')