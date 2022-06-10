# Docker Image Cleaner

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/docker-image-cleaner/Publish?logo=github)](https://github.com/jupyterhub/docker-image-cleaner/actions)
[![Latest PyPI version](https://img.shields.io/pypi/v/docker-image-cleaner?logo=pypi)](https://pypi.python.org/pypi/docker-image-cleaner)
[![Latest quay.io image tags](https://img.shields.io/github/v/tag/jupyterhub/docker-image-cleaner?include_prereleases&label=quay.io)](https://quay.io/repository/jupyterhub/docker-image-cleaner?tab=tags)

A Python package (`docker-image-cleaner`) and associated Docker image
(`quay.io/jupyterhub/docker-image-cleaner`) to clean up old docker images when a
disk is running low on inodes or space.

The script has initially been developed to help installations of BinderHub clean
up space on nodes as it otherwise can run out of space and stop being able to
build now docker images.

## Why?

Container images are one of the biggest consumers of disk space
and inodes on kubernetes nodes. Kubernetes tries to make sure there is enough
disk space on each node by [garbage
collecting](https://kubernetes.io/docs/concepts/architecture/garbage-collection/#containers-images)
unused container images and containers. Tuning this is important
for [binderhub](https://github.com/jupyterhub/binderhub/) installations,
as many images are built and used only a couple times. However, on
most managed kubernetes installations (like GKE, EKS, etc), we can not
tune these parameters!

This script approximates the specific parts of the kubernetes container image
garbage collection in a configurable way.

## Requirements

1. Only kubernetes nodes using the `docker` runtime are supported.
   `containerd` or `cri-o` container backends are not supported.
2. The script expects to run in a kubernetes `DaemonSet`, with `/var/lib/docker`
   from the node mounted inside the container. This lets the script figure
   out how much disk space docker container images are actually using.
3. The `DaemonSet` should have a `ServiceAccount` attached that has permissions
   to talk to the kubernetes API and cordon / uncordon nodes. This makes sure
   new pods are not scheduled on to the node while image cleaning is happening,
   as it can take a while.

## How does it work?

1. Compute how much space `/var/lib/docker` directory (specified by the
   `DOCKER_IMAGE_CLEANER_PATH_TO_CHECK` environment variable) is taking up.
2. If the disk space used is greater than the garbage collection trigger threshold
   (specified by `DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH`), garbage collection is triggered.
   If not, the script just waits another 5 minutes (set by `DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS`).
3. If garbage collection is triggered, the kubernetes node is first cordoned
   to prevent any new pods from being scheduled on it for the duration of the
   garbage collection.
4. Unused container images are deleted one by one, starting with the biggest,
   until the disk space used by `/var/lib/docker` falls below the garbage collection
   'ok' threshold (specified by `DOCKER_IMAGE_CLEANER_THRESHOLD_LOW`). This low / high system
   makes sure we don't get too aggressive in cleaning the disk, as images being
   present on the node does speed up binderhub launches.
5. After the garbage collection is done, the kubernetes node is also uncordoned.
6. When done, we wait another 5 minutes (set by `DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS`), and repeat
   the whole process.

## Configuration options

Currently, environment variables are used to set configuration for now.

| Env variable                            | Description                                                                                                                    | Default           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| `DOCKER_IMAGE_CLEANER_NODE_NAME`        | The k8s node where the docker image cleaner is running, so it can be cordoned via the k8s api                                  |                   |
| `DOCKER_IMAGE_CLEANER_PATH_TO_CHECK`    | Path to `/var/lib/docker` directory used by the docker daemon                                                                  | `/var/lib/docker` |
| `DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS` | Amount of time (in seconds) to wait between checking if GC needs to be triggered                                               | `300`             |
| `DOCKER_IMAGE_CLEANER_DELAY_SECONDS`    | Amount of time (in seconds) to wait between deleting container images, so we don't DOS the docker API                          | `1`               |
| `DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE`   | Determine if GC should be triggered based on relative or absolute disk usage                                                   | `relative`        |
| `DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH`   | % or absolute disk space available (based on `DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE`) when we start deleting container images    | `80`              |
| `DOCKER_IMAGE_CLEANER_THRESHOLD_LOW`    | % or absolute disk space available (based on `DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE`) when we can stop deleting container images | `60`              |
