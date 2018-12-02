import os

accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(D)s "%({X-Logging-Context}o)s" "%(f)s" "%(a)s"'

for k,v in os.environ.items():
    if k.startswith("GUNICORN_"):
        key = k.split('_', 1)[1].lower()
        locals()[key] = v
