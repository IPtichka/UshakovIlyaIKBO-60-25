"""
Клиент npm-реестра для получения прямых зависимостей пакета.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict

DEFAULT_TIMEOUT = 15


class NpmRegistryError(ValueError):
    """Не удалось получить или разобрать данные из npm-реестра."""


def _build_package_url(registry_url: str, package_name: str) -> str:
    """Собрать URL документа пакета с корректным кодированием имени."""
    base = registry_url.rstrip("/")
    encoded = urllib.parse.quote(package_name, safe="@")
    return f"{base}/{encoded}"


def fetch_direct_dependencies(
    registry_url: str,
    package_name: str,
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, str]:
    """Вернуть прямые зависимости пакета как словарь {имя: диапазон}.

    Бросает NpmRegistryError при любой проблеме: сеть, HTTP-ошибка,
    невалидный JSON, отсутствие нужных полей.
    """
    url = _build_package_url(registry_url, package_name)

    try:
        request = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise NpmRegistryError(
                f"package {package_name!r} not found in npm registry"
            ) from exc
        raise NpmRegistryError(
            f"npm registry returned HTTP {exc.code} for {url}"
        ) from exc
    except urllib.error.URLError as exc:
        raise NpmRegistryError(
            f"failed to reach npm registry at {url}: {exc.reason}"
        ) from exc
    except OSError as exc:
        raise NpmRegistryError(
            f"network error while fetching {url}: {exc}"
        ) from exc

    try:
        document = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise NpmRegistryError(
            f"npm registry returned invalid JSON for {url}: {exc}"
        ) from exc

    if not isinstance(document, dict):
        raise NpmRegistryError(
            f"unexpected npm registry response for {url}: not a JSON object"
        )

    dist_tags = document.get("dist-tags")
    if not isinstance(dist_tags, dict) or "latest" not in dist_tags:
        raise NpmRegistryError(
            f"package {package_name!r} has no 'latest' dist-tag"
        )

    latest = dist_tags["latest"]
    versions = document.get("versions")
    if not isinstance(versions, dict) or latest not in versions:
        raise NpmRegistryError(
            f"package {package_name!r} version {latest!r} "
            f"is missing from 'versions'"
        )

    version_data = versions[latest]
    if not isinstance(version_data, dict):
        raise NpmRegistryError(
            f"version data for {package_name}@{latest} is not an object"
        )

    dependencies = version_data.get("dependencies", {})
    if dependencies is None:
        dependencies = {}
    if not isinstance(dependencies, dict):
        raise NpmRegistryError(
            f"'dependencies' of {package_name}@{latest} is not an object"
        )

    result: Dict[str, str] = {}
    for dep_name, dep_range in dependencies.items():
        if not isinstance(dep_name, str) or not dep_name:
            raise NpmRegistryError(
                f"invalid dependency name in {package_name}@{latest}: "
                f"{dep_name!r}"
            )
        if not isinstance(dep_range, str):
            raise NpmRegistryError(
                f"invalid version range for dependency {dep_name!r} "
                f"in {package_name}@{latest}"
            )
        result[dep_name] = dep_range
    return result