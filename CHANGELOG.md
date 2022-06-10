# Changelog

## 1.0

### 1.0.0-beta.2 - Not yet released

#### Breaking changes

All environment variables configuring the docker-image-cleaner has been renamed
but have the same functionality.

| Before                    | After                                    |
| ------------------------- | ---------------------------------------- |
| `NODE_NAME`               | `DOCKER_IMAGE_CLEANER__NODE_NAME`        |
| `PATH_TO_CHECK`           | `DOCKER_IMAGE_CLEANER__PATH_TO_CHECK`    |
| `IMAGE_GC_INTERVAL`       | `DOCKER_IMAGE_CLEANER__INTERVAL_SECONDS` |
| `IMAGE_GC_DELAY`          | `DOCKER_IMAGE_CLEANER__DELAY_SECONDS`    |
| `IMAGE_GC_THRESHOLD_TYPE` | `DOCKER_IMAGE_CLEANER__THRESHOLD_TYPE`   |
| `IMAGE_GC_THRESHOLD_HIGH` | `DOCKER_IMAGE_CLEANER__THRESHOLD_HIGH`   |
| `IMAGE_GC_THRESHOLD_LOW`  | `DOCKER_IMAGE_CLEANER__THRESHOLD_LOW`    |

### 1.0.0-beta.1 - 2022-05-25

#### Enhancements made

- use docker system prune to clean images [#37](https://github.com/jupyterhub/docker-image-cleaner/pull/37) ([@minrk](https://github.com/minrk), [@consideRatio](https://github.com/consideRatio), [@betatim](https://github.com/betatim))

#### Maintenance and upkeep improvements

- Bump kubernetes from 23.3.0 to 23.6.0 [#47](https://github.com/jupyterhub/docker-image-cleaner/pull/47) ([@dependabot](https://github.com/dependabot), [@consideRatio](https://github.com/consideRatio))
- Bump kubernetes from 21.7.0 to 23.3.0 [#32](https://github.com/jupyterhub/docker-image-cleaner/pull/32) ([@dependabot](https://github.com/dependabot), [@minrk](https://github.com/minrk))
- Bump kubernetes from 20.13.0 to 21.7.0 [#23](https://github.com/jupyterhub/docker-image-cleaner/pull/23) ([@dependabot](https://github.com/dependabot), [@consideRatio](https://github.com/consideRatio))
- Bump kubernetes from 19.15.0 to 20.13.0 [#21](https://github.com/jupyterhub/docker-image-cleaner/pull/21) ([@dependabot](https://github.com/dependabot), [@consideRatio](https://github.com/consideRatio))
- Bump kubernetes from 18.20.0 to 19.15.0 [#17](https://github.com/jupyterhub/docker-image-cleaner/pull/17) ([@dependabot](https://github.com/dependabot), [@consideRatio](https://github.com/consideRatio))

#### Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/docker-image-cleaner/graphs/contributors?from=2021-10-10&to=2022-05-25&type=c))

[@betatim](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Abetatim+updated%3A2021-10-10..2022-05-25&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3AconsideRatio+updated%3A2021-10-10..2022-05-25&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Aminrk+updated%3A2021-10-10..2022-05-25&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Ayuvipanda+updated%3A2021-10-10..2022-05-25&type=Issues)

### 1.0.0-alpha.2 - 2021-10-10

Initial fixes to make it function properly in jupyterhub/binderhub and jupyterhub/mybinder.org-deploy.

### 1.0.0-alpha.1 - 2021-09-21

This script has lived by itself as part of jupyterhub/binderhub until now, but
going onwards it is to live in this standalone GitHub repository and be
published as a PyPI package and Docker image on quay.io.
