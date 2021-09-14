# Docker Image Cleaner

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/jupyterhub/docker-image-cleaner/Publish?logo=github)](https://github.com/jupyterhub/docker-image-cleaner/actions)
[![Latest PyPI version](https://img.shields.io/pypi/v/jupyterhub-docker-image-cleaner?logo=pypi)](https://pypi.python.org/pypi/jupyterhub-docker-image-cleaner)

A Python package (`docker-image-cleaner`) and associated Docker image
(`quay.io/jupyterhub/docker-image-cleaner`) to clean up old docker images when a
disk is running low on inodes or space.

The script has initially been developed to help installations of BinderHub clean
up space on nodes as it otherwise can run out of space and stop being able to
build now docker images.
