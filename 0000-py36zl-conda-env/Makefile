
# docker run -it --rm zipline-docker-base-image:202111290853 /bin/bash

TAG_DATE=202111290853

# docker container prune
zipline-docker-base-image:
	docker build -f dockerfile.base --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg http_proxy=${HTTP_PROXY} --build-arg https_proxy=${HTTPS_PROXY} --tag zipline-docker-base-image:${TAG_DATE} --tag zipline-docker-base-image:latest .

# docker save -o zipline-docker-base-image.tar zipline-docker-base-image:latest

zipline-norgate-volume-container:
	docker run -it --rm -v $(shell readlink -f ../norgate_stock_data):/root/bundle:ro -v $(shell readlink -f ../norgate_stock_data/data):/root/bundle/data:ro --name NORGATE-DATA-VOLUME zipline-docker-base-image:latest

zipline-norgate-volume-container2:
	docker run -it --rm --volumes-from NORGATE-DATA-VOLUME busybox

# https://github.com/moby/buildkit/issues/818 Symbolic links as source in RUN --mount=type=bind doesn't mount
# https://github.com/moby/moby/issues/37129   Proposal: add support for multiple (named) build-contexts
zipline-norgate-data-image1:
	docker build -f dockerfile.norgate1 --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg http_proxy=${HTTP_PROXY} --build-arg https_proxy=${HTTPS_PROXY} --tag zipline-norgate-data-image1:${TAG_DATE} --tag zipline-norgate-data-image1:latest ../norgate_stock_data

zipline-norgate-data-image2:
	docker build -f dockerfile.norgate2 --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg http_proxy=${HTTP_PROXY} --build-arg https_proxy=${HTTPS_PROXY} --tag zipline-norgate-data-image2:${TAG_DATE} --tag zipline-norgate-data-image2:latest $(shell readlink -f ../norgate_stock_data/data)
#	DOCKER_BUILDKIT=1 docker buildx build -f dockerfile.norgate2 --build-arg HTTP_PROXY=${HTTP_PROXY} --build-arg HTTPS_PROXY=${HTTPS_PROXY} --build-arg http_proxy=${HTTP_PROXY} --build-arg https_proxy=${HTTPS_PROXY} --tag zipline-norgate-data-image2:${TAG_DATE} --tag zipline-norgate-data-image2:latest $(shell readlink -f ../norgate_stock_data/data)

# docker save -o zipline-norgate-data-image2.tar zipline-norgate-data-image2:latest


# jupyter notebook --no-browser --port=8880
# change user
# docker run -it --rm --net=host --uts=host --pid=host --user "`id -u`:`id -g`" -v `readlink -f .`:/root/local:ro -w /root/local zipline-norgate-data-image2:latest /bin/bash --login -c "jupyter notebook --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
# docker run -it --rm --net=host -v `readlink -f .`:/root/local -w /root/local zipline-norgate-data-image2:latest /bin/bash --login -c "jupyter notebook --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
zipline-norgate-data-container:
	docker run -it --rm --net=host -v `readlink -f .`:/root/local:ro -w /root/local zipline-norgate-data-image2:latest /bin/bash --login -c "jupyter notebook --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
