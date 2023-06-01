import os
from pathlib import Path
from unittest import mock

import docker
import pytest
from conftest import Slept

from docker_image_cleaner import cleaner

here = Path(__file__).resolve().parent
test_image = here.joinpath("test-image")


def _get_images_tags(docker_client, **kwargs):
    """
    Returns a sorted list of images' tags.

    This list looks like ["alpine:3", "ubuntu:20.04", "ubuntu:22.04"].

    docker client's images.list ref: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.list
    """
    images = docker_client.images.list(**kwargs)
    tags = []
    for image in images:
        tags += image.tags
    return sorted(tags)


def _build_image(docker_client, tag, size_mb=1_000, fail=0):
    """
    Builds an image with a given tag and size.

    docker client's images.build ref: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.build
    """
    try:
        docker_client.images.build(
            path=str(test_image),
            tag=tag,
            buildargs={
                "SIZE_MB": str(size_mb),
                "FAIL": str(fail),
            },
        )
    except docker.errors.BuildError:
        if not fail:
            raise
    else:
        if fail:
            raise RuntimeError("Should have failed!")


def _make_file(path, size_mb):
    with open("/dev/zero", "rb") as r:
        mb = r.read(2**20)

    with open(path, "wb") as f:
        for i in range(size_mb):
            f.write(mb)
    return path


def test_get_used_percent():
    used = cleaner.get_used_percent("/")
    # assert range, not much else we can check here
    assert 0 < used < 100


def test_get_absolute_size(tmpdir):
    test_path = tmpdir.mkdir("test")

    def get_used():
        return cleaner.get_absolute_size(str(test_path))

    assert get_used() == 0
    # add a 1GB file
    _make_file(test_path.join("1gb"), 1024)
    assert 0.9 < get_used() < 1.1
    # add another 1GB file
    _make_file(test_path.join("1gb.2"), 1024)
    assert 1.9 < get_used() < 2.2


def test_ps(dind):
    """
    Tests the dind fixture to provide a clean docker environment to test
    against, with no existing images.
    """
    assert _get_images_tags(dind) == []


def test_nothing_to_clean(dind, absolute_threshold, sleep_stops):
    """
    Tests pulling an image and running the cleaner with a high enough threshold
    for the pulled image not be cleaned.
    """
    dind.images.pull("ubuntu:22.04")

    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    assert _get_images_tags(dind) == ["ubuntu:22.04"]


def test_clean_dangling(dind, absolute_threshold, sleep_stops):
    dind.images.pull("ubuntu:22.04")

    before_build = _get_images_tags(dind)
    before_build_all = _get_images_tags(dind, all=True)

    _build_image(dind, tag="unused", size_mb=2_000, fail=1)
    assert _get_images_tags(dind) == before_build  # no new tagged image
    # but there is something still to prune
    assert len(_get_images_tags(dind, all=True)) > len(before_build_all)

    # run clean
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    # did not delete pre-existing image
    assert _get_images_tags(dind) == before_build
    # but did delete dangling images
    assert _get_images_tags(dind, all=True) == before_build_all


def test_clean_all(dind, absolute_threshold, sleep_stops):
    dind.images.pull("ubuntu:22.04")

    before_build = _get_images_tags(dind)
    before_build_all = _get_images_tags(dind, all=True)

    # build two images, one that fails (leaves dangles)
    # and one that succeeds
    _build_image(dind, tag="unused", size_mb=1_000, fail=1)
    _build_image(dind, tag="2gb", size_mb=2_000, fail=0)
    after_build = ["2gb"] + _get_images_tags(dind)
    assert _get_images_tags(dind) == after_build

    # run clean with 2GB
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    # dangling images wasn't enough, pruned everything
    # did not delete pre-existing image
    assert _get_images_tags(dind) == []
    # but did delete dangling images
    assert _get_images_tags(dind, all=True) == []
