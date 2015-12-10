[![Docker Repository on Quay](https://quay.io/repository/humu/rq-cloudwatch/status "Docker Repository on Quay")](https://quay.io/repository/humu/rq-cloudwatch)

# RQ CloudWatch [![](https://quay.io/repository/humu/rq-cloudwatch/status)](https://quay.io/repository/humu/rq-cloudwatch)

Utility to report [RQ](http://python-rq.org/) queue and worker status to AWS CloudWatch. It can be run either as a standalone utility or as a Docker container.

# Running as Docker container

When run in a Docker container rq-cloudwatch runs as a service and getting the RQ info every INTERVAL seconds and reporting it to CloudWatch. The service is restarted automatically if it fails.

```
docker run -d quay.io/humu/rq-cloudwatch \
  -e AWS_REGION=... \
  -e REDIS_URL=... \
  -e ENVIRONMENT=... \
  -e INTERVAL=... \
  /sbin/my_init
```

where:

* `AWS_REGION` - CloudWatch AWS region name
* `ENVIRONMENT` - name of the RQ environment to report on, e.g., "prod-1"
* `REDIS_URL` - [redis URL](https://www.npmjs.com/package/redis-url#url-format)
* `INTERVAL` - how often to collect and report data, in seconds

# Running as command line utility

It an report data once (good for cron job) or in a forever loop (good for running as a runit service). See help for details.

```console
./mon-put-rq-stats.py -h
```

## LICENSE
[![MIT License](http://img.shields.io/badge/license-MIT-blue.svg?style=flat)](LICENSE)
