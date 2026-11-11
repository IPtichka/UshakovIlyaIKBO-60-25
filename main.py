"""CLI-анализатор зависимостей, этап 1.

Читает пользовательские параметры из INI-файла, валидирует каждый
и печатает их в формате ``ключ = значение``. При ошибках конфигурации
печатает сообщение в stderr и завершается с кодом 2 или 3 (ошибка в парсинге npm или в графе).
"""

from __future__ import annotations

import argparse
import configparser
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from npm_reg import NpmRegistryError, fetch_direct_dependencies
from graph import RepositoryError, build_graph, load_repository_file, render_graph
from graph import RepositoryError, build_graph, load_repository_file, render_graph, render_order, topological_order



# Имя единственной секции INI-файла и полный набор ключей в ней.
SECTION = "app"
FIELDS = (
    "package_name",
    "repository",
    "repo_mode",
    "max_depth",
    "filter_substring",
)

# Допустимые значения repo_mode и границы max_depth.
VALID_MODES = ("url", "file", "auto")
MIN_DEPTH = 1
MAX_DEPTH = 100

# Имя пакета: буква/цифра на краях, внутри допустимы «.», «_», «-».
_PACKAGE_NAME_RE = re.compile(
    r"^[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?$"
)


class ConfigError(ValueError):
    """Конфигурация отсутствует или содержит некорректные значения."""


@dataclass(frozen=True)
class AppConfig:
    """Пользовательские параметры анализатора."""

    package_name: str
    repository: str
    repo_mode: str
    max_depth: int
    filter_substring: str

    def as_items(self) -> list[tuple[str, str]]:
        """Вернуть параметры как упорядоченный список пар ключ-значение.

        Порядок фиксирован и совпадает с порядком в INI-файле; значения
        приводятся к строкам, чтобы вызывающий код не думал о типах.
        """
        return [
            ("package_name", self.package_name),
            ("repository", self.repository),
            ("repo_mode", self.repo_mode),
            ("max_depth", str(self.max_depth)),
            ("filter_substring", self.filter_substring),
        ]


def _is_url(value: str) -> bool:
    """Проверить, что значение — http/https URL с непустым хостом."""
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _validate_package_name(value: str) -> str:
    """Проверить имя пакета и вернуть его без окружающих пробелов."""
    value = value.strip()
    if not value:
        raise ConfigError("package_name must not be empty")
    if not _PACKAGE_NAME_RE.match(value):
        raise ConfigError(
            f"package_name {value!r} is not a valid Python package name"
        )
    return value


def _validate_mode(value: str) -> str:
    """Привести режим к нижнему регистру и проверить по списку."""
    value = value.strip().lower()
    if value not in VALID_MODES:
        raise ConfigError(
            f"repo_mode must be one of {VALID_MODES}, got {value!r}"
        )
    return value


def _validate_repository(value: str, mode: str) -> str:
    """Проверить repository с учётом выбранного режима.

    url  — обязателен http/https URL;
    file — обязателен существующий файл;
    auto — подходит URL или файл, что найдётся раньше.
    """
    value = value.strip()
    if not value:
        raise ConfigError("repository must not be empty")
    if mode in ("url", "auto") and _is_url(value):
        return value
    if mode in ("file", "auto") and Path(value).expanduser().is_file():
        return value
    if mode == "url":
        raise ConfigError(f"repository {value!r} is not a valid URL")
    if mode == "file":
        raise ConfigError(f"repository {value!r} is not an existing file")
    raise ConfigError(
        f"repository {value!r} is neither a valid URL nor an existing file"
    )


def _validate_max_depth(value: str) -> int:
    """Преобразовать max_depth в int и проверить диапазон."""
    try:
        depth = int(value.strip())
    except (TypeError, ValueError) as exc:
        raise ConfigError(
            f"max_depth must be an integer, got {value!r}"
        ) from exc
    if not MIN_DEPTH <= depth <= MAX_DEPTH:
        raise ConfigError(
            f"max_depth must be in [{MIN_DEPTH}, {MAX_DEPTH}], got {depth}"
        )
    return depth


def _validate_filter(value: str) -> str:
    """Проверить непустоту подстроки фильтрации."""
    value = value.strip()
    if not value:
        raise ConfigError("filter_substring must not be empty")
    return value


def _read_parser(path: Path) -> configparser.ConfigParser:
    """Открыть и распарсить INI-файл; ошибки чтения — как ConfigError.

    ``interpolation=None`` отключает подстановки ``%(name)s`` — иначе
    значение с символом ``%`` ломалось бы при чтении.
    """
    parser = configparser.ConfigParser(interpolation=None)
    try:
        with path.open("r", encoding="utf-8") as stream:
            parser.read_file(stream, source=str(path))
    except OSError as exc:
        raise ConfigError(f"failed to read {path}: {exc}") from exc
    except configparser.Error as exc:
        raise ConfigError(f"failed to parse {path}: {exc}") from exc
    return parser


def load_config(path: Path) -> AppConfig:
    """Загрузить и провалидировать INI-файл по пути ``path``.

    Структурные ошибки (нет файла, нет секции, нет ключа) прерывают
    загрузку сразу. Ошибки в значениях собираются в список, чтобы
    пользователь увидел их все за один запуск, и лишь затем бросается
    единый ConfigError.
    """
    if not path.exists():
        raise ConfigError(f"configuration file not found: {path}")

    parser = _read_parser(path)
    if not parser.has_section(SECTION):
        raise ConfigError(
            f"missing required section [{SECTION}] in {path}"
        )

    section = parser[SECTION]
    raw = {key: section.get(key) for key in FIELDS}
    missing = [key for key, value in raw.items() if value is None]
    if missing:
        raise ConfigError(
            "; ".join(f"missing required key: {key}" for key in missing)
        )

    # Накопитель ошибок по значениям: валидируем каждый параметр,
    # даже если предыдущий уже упал.
    errors: list[str] = []

    try:
        package_name = _validate_package_name(raw["package_name"])
    except ConfigError as exc:
        errors.append(str(exc))
        package_name = ""

    try:
        repo_mode = _validate_mode(raw["repo_mode"])
    except ConfigError as exc:
        errors.append(str(exc))
        repo_mode = "auto"

    # repository зависит от repo_mode, поэтому проверяется после него;
    # при невалидном repo_mode используем fallback «auto», чтобы всё
    # равно получить и накопить ошибку repository.
    try:
        repository = _validate_repository(raw["repository"], repo_mode)
    except ConfigError as exc:
        errors.append(str(exc))
        repository = ""

    try:
        max_depth = _validate_max_depth(raw["max_depth"])
    except ConfigError as exc:
        errors.append(str(exc))
        max_depth = 0

    try:
        filter_substring = _validate_filter(raw["filter_substring"])
    except ConfigError as exc:
        errors.append(str(exc))
        filter_substring = ""

    if errors:
        raise ConfigError("; ".join(errors))

    return AppConfig(
        package_name=package_name,
        repository=repository,
        repo_mode=repo_mode,
        max_depth=max_depth,
        filter_substring=filter_substring,
    )


def print_config(config: AppConfig) -> None:
    """Напечатать все параметры в формате ``ключ = значение``.

    Ключи выравниваются по ширине самого длинного, чтобы столбец «=»
    был ровным — это косметика, но заметно облегчает чтение глазами.
    """
    items = config.as_items()
    width = max(len(key) for key, _ in items)
    for key, value in items:
        print(f"{key:<{width}} = {value}")


def build_parser() -> argparse.ArgumentParser:
    """Собрать парсер аргументов командной строки."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        default="config.ini"
    )
    parser.add_argument(
        "--order",
        action="store_true"
    )
    return parser


def print_dependencies(
    package_name: str,
    dependencies: dict[str, str],
) -> None:
    """Напечатать прямые зависимости в формате «имя (диапазон)»."""
    if not dependencies:
        print(f"Package {package_name!r} has no direct dependencies.")
        return
    print(f"Direct dependencies of {package_name!r}:")
    for dep_name, dep_range in dependencies.items():
        print(f"  - {dep_name} ({dep_range})")


def main(argv: list[str] | None = None) -> int:
    """Точка входа. Возвращает код процесса: 0 — успех, 2 — ошибка, 3 — репозиторий/граф."""
    args = build_parser().parse_args(argv)
    try:
        config = load_config(Path(args.config))
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    repository_path = Path(config.repository)
    use_file = (
        config.repo_mode == "file"
        or (config.repo_mode == "auto" and repository_path.is_file())
    )

    if use_file:
        try:
            repository = load_repository_file(repository_path)
        except RepositoryError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 3

        def fetch(name: str) -> dict[str, str]:
            return {dep: "*" for dep in repository.get(name, [])}
    else:
        cache: dict[str, dict[str, str]] = {}

        def fetch(name: str) -> dict[str, str]:
            if name not in cache:
                cache[name] = fetch_direct_dependencies(
                    config.repository, name
                )
            return cache[name]

    try:
        graph = build_graph(
            root=config.package_name,
            max_depth=config.max_depth,
            filter_substring=config.filter_substring,
            fetch=fetch,
        )
    except NpmRegistryError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    if args.order:
        order, broken = topological_order(graph)
        print(render_order(graph, order, broken))
        return 0
    print(render_graph(graph))
    return 0


if __name__ == "__main__":
    sys.exit(main())