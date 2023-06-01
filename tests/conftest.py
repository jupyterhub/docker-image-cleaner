import os
import sys
import time
from unittest import mock

import docker
import pytest
import requests

dind_container_name = "test-image-cleaner-dind"


@pytest.fixture(scope="session")
def host_docker():
    d = docker.from_env()
    d.images.pull("ubuntu:22.04")
    # make sure there isn't a lingering dind container
    try:
        dind_container = d.containers.get(dind_container_name)
    except docker.errors.NotFound:
        pass
    else:
        try:
            dind_container.stop()
        except docker.errors.NotFound:
            pass
        else:
            try:
                dind_container.remove()
            except docker.errors.NotFound:
                pass
    return d


@pytest.fixture(scope="session")
def dind_image(host_docker):
    dind_image = "docker:20-dind"
    host_docker.images.pull(dind_image)
    return dind_image


@pytest.fixture
def dind_dir(tmpdir):
    dind_dir = str(tmpdir.mkdir("dind"))
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_PATH_TO_CHECK": str(dind_dir)}
    ):
        yield str(dind_dir)


@pytest.fixture
def dind(tmpdir, host_docker, dind_image, dind_dir):
    """Start docker-in-docker (dind)"""
    # start the container
    dind_mount = docker.types.Mount(
        type="bind",
        target="/var/lib/docker",
        source=dind_dir,
        read_only=False,
    )
    dind_container = host_docker.containers.run(
        dind_image,
        name=dind_container_name,
        privileged=True,
        mounts=[dind_mount],
        command=[
            "dockerd",
            "--host=tcp://0.0.0.0:2376",
            "--tls=false",
        ],
        detach=True,
        ports={"2376/tcp": ("127.0.0.1", None)},
    )

    # start streaming logs from the container
    def stream_logs():
        for line in dind_container.logs(stream=True):
            sys.stderr.write(line.decode("utf8", "replace"))

    from threading import Thread

    log_thread = Thread(target=stream_logs)
    log_thread.start()

    # wait for ports to be ready
    while not dind_container.ports:
        dind_container.reload()

    port = dind_container.ports["2376/tcp"][0]["HostPort"]
    docker_host = f"tcp://127.0.0.1:{port}"

    with mock.patch.dict(os.environ, {"DOCKER_HOST": docker_host}):
        # wait for docker to start
        deadline = time.monotonic() + 30
        dind_client = None
        while time.monotonic() < deadline:
            try:
                result = dind_container.wait(timeout=1)
            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectionError,
            ):
                pass
            else:
                log_thread.join(timeout=1)
                pytest.fail(f"dind container exited! {result=}")
            try:
                dind_client = docker.from_env()
            except Exception as e:
                print(f"dind not ready: {e}")
                continue
            else:
                break
        assert dind_client is not None
        try:
            yield dind_client
        except Exception as e:
            print("Exception! {e}")

    # stop and remove
    try:
        dind_container.stop()
    except docker.errors.NotFound:
        pass
    try:
        dind_container.remove()
    except docker.errors.NotFound:
        pass

    # cleanup dind dir: needs root! pytest cleanup will fail with permission errors
    out = host_docker.containers.run(
        "ubuntu:22.04",
        remove=True,
        mounts=[dind_mount],
        command=[
            "sh",
            "-c",
            f"rm -rf {dind_mount['Target']}/*",
        ],
    )


@pytest.fixture
def absolute_threshold():
    """Use absolute threshold

    get_used is hard
    """
    with mock.patch.dict(
        os.environ, {"DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE": "absolute"}
    ):
        yield


class Slept(Exception):
    """Exception for raising instead of sleeping"""

    def __init__(self, slept_for):
        self.slept_for = slept_for


@pytest.fixture
def sleep_stops():
    def raise_slept(t):
        raise Slept(t)

    with mock.patch("time.sleep", raise_slept):
        yield
