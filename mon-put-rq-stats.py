#!/usr/bin/env python
"""
Usage: mon-put-rq-stats.py [--url REDIS_URL] [--env ENV] [--region REGION]
                           [--pid PIDFILE] [--interval INTERVAL]
       mon-put-rq-stats.py -h | --help
       mon-put-rq-stats -v | --version

Report RQ stats to AWS CloudWatch

Options:
  -h --help            show help and exit
  -v --version         show version and exit

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
from time import sleep
import logging
from boto.ec2 import cloudwatch
from redis import StrictRedis
from rq import Queue, Worker
from rq.worker import WorkerStatus


logging.basicConfig(level=logging.INFO)
log = logging.getLogger('rq-stats')


def put_data(args):
    "Get RQ data and send to CloudWatch"
    cw = cloudwatch.connect_to_region(args['--region'])
    log.info('put_data {}'.format(args))
    def put_metrics(metrics, dimensions):
        dimensions['env'] = args['--env']
        log.info('dims: {} ==> {}'.format(dimensions, metrics))
        cw.put_metric_data('RQ',
                           list(metrics.keys()),
                           list(metrics.values()),
                           unit='Count', dimensions=dimensions)

    redis = StrictRedis.from_url(args['--url'])

    # all workers
    workers = Worker.all(connection=redis)

    # queues and their workers
    queues = {q:[] for q in Queue.all(connection=redis)}

    # populate list of workers for each queue
    for w in workers:
        for q in w.queues:
            if queues.get(q) is not None:
                queues[q].append(w)

    for q in queues:
        put_metrics({'jobs': len(q), 'workers': len(queues[q])},
                    {'queue': q.name})

        states = {}
        for w in queues[q]:
            count = states.get(w.state, 0) + 1
            states[w.state] = count

        for state in states:
            put_metrics({'workers': states[state]},
                        {
                            'queue': q.name,
                            'state': state.decode(),
                        })


if __name__ == '__main__':
    args = docopt.docopt(__doc__, version='0.0.1')
    if args.get('--pid') is not None:
        with open(os.path.expanduser(args['--pid']), "w") as f:
            f.write(str(os.getpid()))

    interval = args.get('--interval')
    if interval is None:
        put_data(args)
    else:
        interval = float(interval)
        while True:
            put_data(args)
            sleep(interval)
