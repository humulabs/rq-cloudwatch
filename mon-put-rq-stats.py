#!/usr/bin/env python
"""
Usage: mon-put-rq-stats.py [--url REDIS_URL] [--env ENV] [--region REGION]
                           [--pid PIDFILE] [--interval INTERVAL]
                           [--debug] [--no-cloudwatch]
       mon-put-rq-stats.py -h | --help
       mon-put-rq-stats -v | --version

Report RQ stats to AWS CloudWatch

Options:
  -h --help            show help and exit
  -v --version         show version and exit
  --no-cloudwatch      do not report stats to AWS CloudWatch, mostly for
                       debugging. Use "rq info" utility that comes with RQ
                       if you just want to see RQ info at a glance.
  --debug              log debug messages, including AWS API calls

Arguments:
  --url=REDIS_URL      redis URL [default: redis://localhost:6379]

  --env=ENV            environment name to report on [default: dev]

  --region=REGION      AWS CloudWatch region to use [default: us-east-1]

  --pid=PIDFILE        file to write PID to, default is to not write PID

  --interval=INTERVAL  If supplied report data every INTERVAL seconds. If
                       not supplied report data once and exit.
"""
import docopt
import os
import sys
from time import sleep
import logging
from boto.ec2 import cloudwatch
from redis import StrictRedis
from rq import Queue, Worker


def put_data(args, log):
    "Get RQ data and send to CloudWatch"
    log.info('put_data()')
    cw = cloudwatch.connect_to_region(args['--region'])
    def put_metrics(metrics, dimensions):
        dimensions['env'] = args['--env']
        log.info('{} --> {}'.format(dimensions, metrics))
        if not args['--no-cloudwatch']:
            cw.put_metric_data('RQ',
                               list(metrics.keys()),
                               list(metrics.values()),
                               unit='Count', dimensions=dimensions)

    try:
        redis = StrictRedis.from_url(args['--url'])
        redis.ping()
    except Exception as e:
        log.error('Unable to connect to redis: {}'.format(e))
        return

    # group workers by queue
    workers_by_queue = {}
    for w in Worker.all(connection=redis):
        for q in w.queues:
            ws = workers_by_queue.get(q, [])
            ws.append(w)
            workers_by_queue[q] = ws

    for q in workers_by_queue:
        # report queue level rollup
        put_metrics({'jobs': len(q), 'workers': len(workers_by_queue[q])},
                    {'queue': q.name})

        # report workers for each queue in each worker state
        states = {}
        for w in workers_by_queue[q]:
            count = states.get(w.state, 0) + 1
            states[w.state] = count

        for state in states:
            put_metrics({'workers': states[state]},
                        {
                            'queue': q.name,
                            'state': state.decode(),
                        })


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='0.0.2')

    log_level = logging.DEBUG if args['--debug'] else logging.INFO
    log_format = '%(asctime)-15s %(levelname)s %(message)s'
    logging.basicConfig(level=log_level, format=log_format)
    log = logging.getLogger('rq-cloudwatch')

    if args.get('--pid') is not None:
        with open(os.path.expanduser(args['--pid']), "w") as f:
            f.write(str(os.getpid()))
        log.info('starting {}'.format(args))

    interval = args.get('--interval')
    if interval is None:
        put_data(args, log)
    else:
        interval = float(interval)
        while True:
            put_data(args, log)
            sleep(interval)
