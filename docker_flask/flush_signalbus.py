#!/usr/bin/env python

if __name__ == '__main__':
    import sys
    import logging
    import logging.config

    logging.config.fileConfig('/usr/src/app/docker_flask/logging.conf')
    logger = logging.getLogger(__name__)

    from wsgi import app

    if 'signalbus' in app.extensions:
        args = sys.argv[1:]
        kwargs = {'wait': float(args[0])} if len(args) >= 1 else {}
        with app.app_context():
            try:
                signal_count = app.extensions['signalbus'].flush(**kwargs)
            except:
                logger.exception('Caught error while sending penging signals.')
                sys.exit(1)
            if signal_count > 0:
                logger.warning('%i pending signals have been sent.', signal_count)
