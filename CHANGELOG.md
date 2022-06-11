# Changelog

## 1.0

### 1.0.0-beta.2 - 2022-06-11

([full changelog](https://github.com/jupyterhub/docker-image-cleaner/compare/1.0.0-beta.1...1.0.0-beta.2))

#### Breaking changes

All environment variables configuring the docker-image-cleaner has been renamed
but have the same functionality.

| Before                    | After                                   |
| ------------------------- | --------------------------------------- |
| `NODE_NAME`               | `DOCKER_IMAGE_CLEANER_NODE_NAME`        |
| `PATH_TO_CHECK`           | `DOCKER_IMAGE_CLEANER_PATH_TO_CHECK`    |
| `IMAGE_GC_INTERVAL`       | `DOCKER_IMAGE_CLEANER_INTERVAL_SECONDS` |
| `IMAGE_GC_DELAY`          | `DOCKER_IMAGE_CLEANER_DELAY_SECONDS`    |
| `IMAGE_GC_THRESHOLD_TYPE` | `DOCKER_IMAGE_CLEANER_THRESHOLD_TYPE`   |
| `IMAGE_GC_THRESHOLD_HIGH` | `DOCKER_IMAGE_CLEANER_THRESHOLD_HIGH`   |
| `IMAGE_GC_THRESHOLD_LOW`  | `DOCKER_IMAGE_CLEANER_THRESHOLD_LOW`    |

## Bugs fixed

- prune all images if no dangling images left [#51](https://github.com/jupyterhub/docker-image-cleaner/pull/51) ([@minrk](https://github.com/minrk))

## Maintenance and upkeep improvements

- breaking, maint: prefix env vars with project name [#55](https://github.com/jupyterhub/docker-image-cleaner/pull/55) ([@consideRatio](https://github.com/consideRatio))
- pre-commit: use isort over reorder-python-imports [#53](https://github.com/jupyterhub/docker-image-cleaner/pull/53) ([@consideRatio](https://github.com/consideRatio))
- Bump actions/setup-python from 3 to 4 [#50](https://github.com/jupyterhub/docker-image-cleaner/pull/50) ([@dependabot](https://github.com/dependabot))

## Other merged PRs

- Refreeze Dockerfile's requirements.txt [#58](https://github.com/jupyterhub/docker-image-cleaner/pull/58) ([@jupyterhub-bot](https://github.com/jupyterhub-bot))
- ci: fix detail in refreeze requirements.txt workflow [#57](https://github.com/jupyterhub/docker-image-cleaner/pull/57) ([@consideRatio](https://github.com/consideRatio))
- image: use frozen requirements.txt and automate updates of it [#56](https://github.com/jupyterhub/docker-image-cleaner/pull/56) ([@consideRatio](https://github.com/consideRatio))
- breaking, maint: require py38+ [#54](https://github.com/jupyterhub/docker-image-cleaner/pull/54) ([@consideRatio](https://github.com/consideRatio))

## Contributors to this release

([GitHub contributors page for this release](https://github.com/jupyterhub/docker-image-cleaner/graphs/contributors?from=2022-05-25&to=2022-06-11&type=c))

[@consideRatio](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3AconsideRatio+updated%3A2022-05-25..2022-06-11&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Adependabot+updated%3A2022-05-25..2022-06-11&type=Issues) | [@jupyterhub-bot](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Ajupyterhub-bot+updated%3A2022-05-25..2022-06-11&type=Issues) | [@minrk](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Aminrk+updated%3A2022-05-25..2022-06-11&type=Issues) | [@welcome](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Awelcome+updated%3A2022-05-25..2022-06-11&type=Issues) | [@yuvipanda](https://github.com/search?q=repo%3Ajupyterhub%2Fdocker-image-cleaner+involves%3Ayuvipanda+updated%3A2022-05-25..2022-06-11&type=Issues)

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
