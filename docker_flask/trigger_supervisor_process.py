#!/usr/bin/env python

import sys
from xmlrpc.client import ServerProxy


def write_stdout(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()


def trigger(process_name, interval):
    server = ServerProxy('http://dummy:dummy@localhost:9001/RPC2')
    last_started_at = 0.0
    while True:
        write_stdout('READY\n')
        headers_line = sys.stdin.readline()
        headers = dict([x.split(':') for x in headers_line.split()])
        event_data = sys.stdin.read(int(headers['len']))
        if headers['eventname'] == 'TICK_5':
            assert event_data.startswith('when:')
            now = float(event_data[5:])
            seconds_since_last_started = now - last_started_at
            if seconds_since_last_started >= interval:
                statename = server.supervisor.getProcessInfo(process_name)['statename']
                if statename in ['STOPPED', 'BACKOFF', 'EXITED']:
                    server.supervisor.startProcess(process_name)
                    last_started_at = now
        write_stdout('RESULT 2\nOK')


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) == 2:
        trigger(args[0], int(args[1]))
    else:
        print('Usage: trigger_supervisor_process.py PROCESS_NAME INTERVAL_SECONDS')
        sys.exit(1)
