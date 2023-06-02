import os
from pathlib import Path
from unittest import mock

import docker
import pytest
from conftest import Slept

from docker_image_cleaner import cleaner

here = Path(__file__).resolve().parent
test_image = here.joinpath("test-image")


def _get_image_tags(docker_client):
    """
    Returns a sorted list of non-dangling images' tags.

    The return value can look like this:

    - []
    - ["alpine:3", "ubuntu:20.04", "ubuntu:22.04"]

    docker client's images.list ref: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.list
    """
    images = docker_client.images.list(filters={"dangling": False})
    tags = []
    for image in images:
        if image.tags:
            tags += image.tags
    return sorted(tags)


def _get_dangling_image_layer_ids(docker_client):
    """
    Returns a sorted list of dangling images' ids.

    The return value can look like this:

    - []
    - ["sha256:0123456789ab", "sha256:0123456789xy"]

    docker client's images.list ref: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.list
    """
    images = docker_client.images.list(all=True, filters={"dangling": True})
    ids = []
    for image in images:
        ids.append(image.short_id)
    return sorted(ids)


def _build_image(docker_client, tag, size_mb=1000, fail=0):
    """
    Attempts to build an image tag to a given size, and can be configured to
    fail so that a dangling image is created.

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


def test_clean_nothing(dind, dind_dir, absolute_threshold, sleep_stops):
    """
    Tests pulling an image and running the cleaner with a high enough threshold
    for the pulled image not be cleaned.
    """
    # expect no images and then pull one to check it won't get cleaned
    assert _get_image_tags(dind) == []
    assert _get_dangling_image_layer_ids(dind) == []
    assert 0.1 > cleaner.get_absolute_size(dind_dir)

    dind.images.pull("ubuntu:22.04")
    before_clean = _get_image_tags(dind)
    assert before_clean == ["ubuntu:22.04"]
    assert cleaner.get_absolute_size(dind_dir) > 0.1

    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": f"{cleaner.GB}"}
    ), pytest.raises(Slept):
        cleaner.main()

    # expect to not delete pre-existing image
    assert _get_image_tags(dind) == before_clean
    assert cleaner.get_absolute_size(dind_dir) > 0.1


def test_clean_dangling(dind, dind_dir, absolute_threshold, sleep_stops):
    """
    Tests pulling an image, creating dangling image layers, and running the
    cleaner with a high enough threshold for the pulled image not be cleaned
    after the dangling image layers was cleaned.
    """
    assert 0.1 > cleaner.get_absolute_size(dind_dir)

    dind.images.pull("ubuntu:22.04")
    assert 1 > cleaner.get_absolute_size(dind_dir) > 0.1

    initial_tags = _get_image_tags(dind)

    # build an image, fail the build intentionally to create dangling image layers
    _build_image(dind, tag="test:dangling", size_mb=500, fail=1)
    assert cleaner.get_absolute_size(dind_dir) > 1

    assert _get_image_tags(dind) == initial_tags
    assert len(_get_dangling_image_layer_ids(dind)) > 0

    # run clean
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": f"{cleaner.GB}"}
    ), pytest.raises(Slept):
        cleaner.main()

    # expect to not delete pre-existing image, but the new dangling image layers
    assert _get_image_tags(dind) == initial_tags
    assert len(_get_dangling_image_layer_ids(dind)) == 0
    assert 1 > cleaner.get_absolute_size(dind_dir) > 0.1


def test_clean_all(dind, dind_dir, absolute_threshold, sleep_stops):
    """
    Tests pulling an image, creating dangling image layers and a non-dangling
    image, then running the cleaner forced to clean up non-dangling image layers
    as well.
    """
    dind.images.pull("ubuntu:22.04")
    assert 1 > cleaner.get_absolute_size(dind_dir) > 0.1

    initial_tags = _get_image_tags(dind)

    # build two images, fail one build intentionally to create dangling image layers
    assert len(_get_dangling_image_layer_ids(dind)) == 0
    _build_image(dind, tag="test:dangling", size_mb=100, fail=1)
    assert len(_get_dangling_image_layer_ids(dind)) > 0
    assert 0.1 < cleaner.get_absolute_size(dind_dir) < 1

    _build_image(dind, tag="test:too-large", size_mb=500, fail=0)
    assert len(_get_image_tags(dind)) > len(initial_tags)
    assert cleaner.get_absolute_size(dind_dir) > 1

    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH": f"{cleaner.GB}"}
    ), pytest.raises(Slept):
        cleaner.main()

    # deleted dangling images as the first action to remedy the situation...
    assert cleaner.get_absolute_size(dind_dir) < 1
    assert _get_dangling_image_layer_ids(dind) == []

    # ... and new too large image, but also the pre-existing image because
    # everything goes at this point
    assert 0.1 > cleaner.get_absolute_size(dind_dir)
    assert _get_image_tags(dind) == []


def test_get_absolute_size_no_such_dir(tmpdir):
    with pytest.raises(FileNotFoundError):
        cleaner.get_absolute_size(tmpdir.join("nosuchdir"))
