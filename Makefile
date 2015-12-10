HOST = quay.io
NAME = humu/rq-cloudwatch
VERSION = 0.0.2

build:
	docker build -t $(HOST)/$(NAME):$(VERSION) --rm .

tag:
	docker tag -f $(HOST)/$(NAME):$(VERSION) $(HOST)/$(NAME):latest

release: tag
	docker push $(HOST)/$(NAME)

start-redis:
	@(docker ps --filter=name=redis --filter=status=running | grep -q redis) \
	  || (echo 'starting redis' && docker run -d --name redis redis)

stop-redis:
	@(docker rm -f redis 2>/dev/null && echo stopped) \
	  || echo 'redis not running'

run: start-redis
	docker run -d \
	  --link redis:redis \
	  --name rq-cloudwatch \
	  -h rq-cloudwatch \
	  -e ENVIRONMENT=$(USER)-`hostname` \
	  -e AWS_ACCESS_KEY_ID=$(AWS_ACCESS_KEY_ID) \
	  -e AWS_SECRET_ACCESS_KEY=$(AWS_SECRET_ACCESS_KEY) \
      -e REDIS_URL=http://redis:6379 \
      -e INTERVAL=30 \
      -e AWS_REGION=us-east-1 \
	  $(HOST)/$(NAME):$(VERSION) /sbin/my_init

.PHONY: build test tag release
