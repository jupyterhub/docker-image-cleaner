"""
Clean docker images

Calls docker prune when the disk starts getting full.

This serves as a substitute for Kubernetes ImageGC
which has thresholds that are not sufficiently configurable on GKE
at this time.
"""
import logging
import os
import time
from contextlib import contextmanager, nullcontext
from functools import partial

import docker
import requests

logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


annotation_key = "hub.jupyter.org/image-cleaner-cordoned"

GB = 2**30


def get_absolute_size(path):
    """
    Directory size in gigabytes
    """
    # first, check permissions, existence of path with os.listdir
    # os.walk returns an empty list if it doesn't find anything
    os.listdir(path)
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for fname in filenames:
            f = os.path.join(dirpath, fname)
            # some files are links, skip them as they don't use
            # up additional space
            if os.path.isfile(f):
                total += os.path.getsize(f)

    return total / GB


def get_used_percent(path):
    """
    Return disk usage as a percentage

    (100 is full, 0 is empty)

    Calculated by blocks or inodes,
    which ever reports as the most full.
    """
    stat = os.statvfs(path)
    inodes_avail = stat.f_favail / stat.f_files
    blocks_avail = stat.f_bavail / stat.f_blocks
    return 100 * (1 - min(blocks_avail, inodes_avail))


def cordon(kube, node):
    """cordon a kubernetes node"""
    logging.info(f"Cordoning node {node}")
    kube.patch_node(
        node,
        {
            # record that we are the one responsible for cordoning
            "metadata": {
                "annotations": {
                    annotation_key: "true",
                },
            },
            "spec": {
                "unschedulable": True,
            },
        },
    )


def uncordon(kube, node):
    """uncordon a kubernetes node"""
    logging.info(f"Uncordoning node {node}")
    kube.patch_node(
        node,
        {
            # clear annotation since we're no longer the reason for cordoning,
            # if the node ever does become cordoned
            "metadata": {
                "annotations": {
                    annotation_key: None,
                },
            },
            "spec": {
                "unschedulable": False,
            },
        },
    )


@contextmanager
def cordoned(kube, node):
    """Context manager for cordoning a node"""
    try:
        cordon(kube, node)
        yield
    finally:
        uncordon(kube, node)


def main():
    node = os.getenv("DOCKER_IMAGE_CLEANER_NODE_NAME")
    if node:
        import kubernetes.client
        import kubernetes.config

        try:
            kubernetes.config.load_incluster_config()
        except Exception:
            kubernetes.config.load_kube_config()
        kube = kubernetes.client.CoreV1Api()
        # verify that we can talk to the node
        node_info = kube.read_node(node)
        # recover from possible crash!
        if node_info.spec.unschedulable and node_info.metadata.annotations.get(
            annotation_key
        ):
            logging.warning(
                f"Node {node} still cordoned, possibly leftover from earlier crash of image-cleaner"
            )
            uncordon(kube, node)

        cordon_context = partial(cordoned, kube, node)
    else:
        cordon_context = nullcontext

    path_to_check = os.getenv("DOCKER_IMAGE_CLEANER_PATH_TO_CHECK", "/var/lib/docker")
    interval_seconds = float(os.getenv("DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS", "300"))
    delay_seconds = float(os.getenv("DOCKER_IMAGE_CLEANER_DELAY_SECONDS", "1"))
    threshold_type = os.getenv("DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE", "relative")
    threshold_high = float(os.getenv("DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH", "80"))
    timeout_seconds = int(os.getenv("DOCKER_IMAGE_CLEANER_TIMEOUT_SECONDS", "300"))

    logging.info("Starting docker image cleaning with the following settings:")
    logging.info(f"DOCKER_IMAGE_CLEANER_PATH_TO_CHECK={path_to_check}")
    logging.info(f"DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS={interval_seconds}")
    logging.info(f"DOCKER_IMAGE_CLEANER_DELAY_SECONDS={delay_seconds}")
    logging.info(f"DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE={threshold_type}")
    logging.info(f"DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH={threshold_high}")
    logging.info(f"DOCKER_IMAGE_CLEANER_TIMEOUT_SECONDS={timeout_seconds}")

    docker_client = docker.from_env(version="auto", timeout=timeout_seconds)

    # with the threshold type set to relative the thresholds are interpreted
    # as a percentage of how full the partition is. In absolute mode the
    # thresholds are interpreted as size in bytes. By default you should use
    # "relative" mode. Use "absolute" mode when you are using DIND and your
    # nodes only have one partition.
    if threshold_type == "relative":
        get_used = get_used_percent
        used_msg = "{used:.1f}% used"
        threshold_s = f"{threshold_high}% inodes or blocks"
    elif threshold_type == "absolute":
        get_used = get_absolute_size
        used_msg = "{used:.2f}GB used"
        threshold_s = f"{threshold_high / GB:.2f}GB"
        if threshold_high < GB:
            raise ValueError(
                f"Absolute GC threshold should be at least 1GB, got {threshold_high}B"
            )
        # units in GB
        threshold_high = threshold_high / GB
    else:
        raise ValueError(
            f"DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE must be 'relative' or 'absolute', got '{threshold_type}'"
        )

    logging.info(f"Pruning docker images when {path_to_check} has {threshold_s} used")

    while True:
        used = get_used(path_to_check)
        logging.info(used_msg.format(used=used))
        if used < threshold_high:
            # Do nothing! We have enough space
            time.sleep(interval_seconds)
            continue

        images = docker_client.images.list(all=True)
        if not images:
            logging.info("No images to delete")
            time.sleep(interval_seconds)
            continue
        else:
            logging.info(f"{len(images)} images available to prune")

        # Ensure the node is cordoned while we prune
        with cordon_context():
            for kind in ("containers", "images"):
                key = f"{kind.title()}Deleted"
                tic = time.perf_counter()
                try:
                    # docker_client.containers.prune: https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.prune
                    # docker_client.images.prune: https://docker-py.readthedocs.io/en/stable/images.html#docker.models.images.ImageCollection.prune
                    pruned = getattr(docker_client, kind).prune()
                except requests.exceptions.ReadTimeout:
                    logging.warning(f"Timeout pruning {kind}")
                    # Delay longer after a timeout, which indicates that Docker is overworked
                    time.sleep(max(delay_seconds, 30))
                    continue

                deleted = pruned[key]
                # pruned looks like:
                # {
                #     "ImagesDeleted": [
                #         {"Deleted": "sha256:5611ea8655"},
                #     ],
                #     "SpaceReclaimed": 4563228463,
                # }

                deleted_bytes = pruned["SpaceReclaimed"]
                deleted_gb = deleted_bytes / GB
                if deleted is None:
                    # returns None instead of empty list when nothing to delete
                    n_deleted = 0
                else:
                    n_deleted = len(deleted)

                # first prune only removes dangling images
                # check if it deleted enough, or if we should continue pruning all images
                prune_all_images = False
                if kind == "images":
                    if not deleted:
                        # found no dangling images to prune,
                        # no need to check space again
                        prune_all_images = True
                    else:
                        # check used again after pruning dangling images
                        # if dangling images didn't cross the threshold,
                        # delete all images
                        logging.info(
                            "Checking if pruning dangling images freed enough space"
                        )
                        if threshold_type == "absolute":
                            # we can estimate change in absolute usage without calling get_used
                            # absolute get_used is very expensive
                            used -= deleted_gb
                        else:
                            # inode-based get_used is very cheap to recalculate
                            used = get_used(path_to_check)
                        prune_all_images = used > threshold_high

                if kind == "images" and prune_all_images:
                    # Deleting dangling images didn't free enough
                    logging.info(
                        f"Pruning {n_deleted} dangling images freed only {deleted_gb:.2f}GB, pruning _all_ images"
                    )
                    try:
                        # prune again, this time with `dangling=False` filter,
                        # which deletes _all_ images instead of just dangling ones
                        pruned = docker_client.images.prune(filters={"dangling": False})
                    except requests.exceptions.ReadTimeout:
                        logging.warning("Timeout pruning all images")
                        # Delay longer after a timeout, which indicates that Docker is overworked
                        time.sleep(max(delay_seconds, 30))
                        continue
                    deleted = pruned[key]
                    if deleted:
                        n_deleted += len(deleted)
                    # recalculate deleted gb
                    deleted_bytes += pruned["SpaceReclaimed"]
                    deleted_gb = deleted_bytes / GB

                toc = time.perf_counter()
                duration = toc - tic
                logging.info(
                    f"Deleted {n_deleted} {kind}, freed {deleted_gb:.2f}GB in {duration:.0f} seconds."
                )

        time.sleep(interval_seconds)


if __name__ == "__main__":
    main()
