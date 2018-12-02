#!/usr/bin/env python

# This script should be called with the filename of the respective
# alembic configuration file. It modifies the file, so that alembic
# will use JSON formatter for its logging messages.

import sys
import configparser

file_name = sys.argv[1]
config = configparser.ConfigParser()
try:
    with open(file_name) as configfile:
        config.read_file(configfile)
except FileNotFoundError:
    sys.stderr.write('set_json_log_handler.py: alembic config file not found (%s)\n' % file_name)
    sys.exit(0)
try:
    handlers_keys = config['handlers']['keys']
except KeyError:
    handlers_keys = 'None'
if handlers_keys != 'console':
    sys.stderr.write('set_json_log_handler.py: wrong logging handlers keys (%s)\n' % handlers_keys)
    sys.exit(1)
config['formatter_json'] = {'class': 'jsonlogging.JSONFormatter'}
formatters = config.setdefault('formatters', {})
formatters_keys = [k.strip() for k in formatters.get('keys', '').split(',')]
if 'json' not in formatters_keys:
    formatters_keys.append('json')
    formatters['keys'] = ','.join(formatters_keys)
handler_console = config.setdefault('handler_console', {})
handler_console.update({
    'class': 'StreamHandler',
    'args': '(sys.stdout,)',
    'formatter': 'json',
})
with open(file_name, 'w') as configfile:
    config.write(configfile)
