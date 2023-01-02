import os
from pathlib import Path
from unittest import mock

import docker
import pytest
from conftest import Slept

from docker_image_cleaner import cleaner

here = Path(__file__).resolve().parent
test_image = here.joinpath("test-image")


def build_image(docker_client, tag, size_mb=1_000, fail=0):
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


def make_file(path, size_mb):
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
    make_file(test_path.join("1gb"), 1024)
    assert 0.9 < get_used() < 1.1
    # add another 1GB file
    make_file(test_path.join("1gb.2"), 1024)
    assert 1.9 < get_used() < 2.2


def test_ps(dind):
    assert dind.images.list() == []


def test_nothing_to_clean(dind, absolute_threshold, sleep_stops):
    dind.images.pull("ubuntu:22.04")
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    assert [image.name for image in dind.images.list()] == ["ubuntu:22.04"]


def test_clean_dangling(dind, absolute_threshold, sleep_stops):
    dind.images.pull("ubuntu:22.04")

    def get_images(**kwargs):
        return sorted(tuple(image.tags) for image in dind.images.list(**kwargs))

    before_build = get_images()
    before_build_all = get_images(all=True)

    build_image(dind, tag="unused", size_mb=2_000, fail=1)
    assert get_images() == before_build  # no new tagged image
    # but there is something still to prune
    assert len(get_images(all=True)) > len(before_build_all)

    # run clean
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    # did not delete pre-existing image
    assert get_images() == before_build
    # but did delete dangling images
    assert get_images(all=True) == before_build_all


def test_clean_all(dind, absolute_threshold, sleep_stops):
    dind.images.pull("ubuntu:22.04")

    def get_images(**kwargs):
        return sorted(tuple(image.tags) for image in dind.images.list(**kwargs))

    before_build = get_images()
    before_build_all = get_images(all=True)

    # build two images, one that fails (leaves dangles)
    # and one that succeeds
    build_image(dind, tag="unused", size_mb=1_000, fail=1)
    build_image(dind, tag="2gb", size_mb=2_000, fail=0)
    after_build = ["2gb"] + get_images()
    assert get_images() == after_build

    # run clean with 2GB
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": "2e9"}
    ), pytest.raises(Slept):
        cleaner.main()

    # dangling images wasn't enough, pruned everything
    # did not delete pre-existing image
    assert get_images() == []
    # but did delete dangling images
    assert get_images(all=True) == []
