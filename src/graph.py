"""Построение графа зависимостей рекурсивным BFS."""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

DependencyFetcher = Callable[[str], dict[str, str]]


class GraphError(ValueError):
    """Не удалось построить граф зависимостей."""


class RepositoryError(ValueError):
    """Тестовый репозиторий некорректен."""


@dataclass
class GraphNode:
    """Узел графа: имя пакета и его глубина от корня."""

    name: str
    depth: int


@dataclass
class Graph:
    """Построенный граф зависимостей."""

    root: str
    max_depth: int
    filter_substring: str
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    cycles: list[tuple[str, str]] = field(default_factory=list)

    def add_node(self, name: str, depth: int) -> bool:
        """Добавить узел; вернуть True, если его не было раньше."""
        if name in self.nodes:
            return False
        self.nodes[name] = GraphNode(name=name, depth=depth)
        return True

    def add_edge(self, src: str, dst: str) -> None:
        """Зарегистрировать ребро (без дублей)."""
        if (src, dst) not in self.edges:
            self.edges.append((src, dst))

    def mark_cycle(self, src: str, dst: str) -> None:
        """Зарегистрировать обратное ребро как цикл (без дублей)."""
        if (src, dst) not in self.cycles:
            self.cycles.append((src, dst))


def load_repository_file(path: Path) -> dict[str, list[str]]:
    """Загрузить тестовый репозиторий из JSON.
    Формат: ``{"PACKAGE": ["DEP1", "DEP2"], ...}``. Имена пакетов —
    произвольные непустые строки; в тестовых примерах используются
    большие латинские буквы.
    """
    if not path.exists():
        raise RepositoryError(f"repository file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except OSError as exc:
        raise RepositoryError(f"failed to read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise RepositoryError(f"failed to parse {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise RepositoryError(
            f"repository root in {path} must be a JSON object"
        )

    result: dict[str, list[str]] = {}
    for name, deps in data.items():
        if not isinstance(name, str) or not name:
            raise RepositoryError(
                f"package names must be non-empty strings: {name!r}"
            )
        if not isinstance(deps, list):
            raise RepositoryError(
                f"dependencies of {name!r} must be a list of strings"
            )
        for dep in deps:
            if not isinstance(dep, str) or not dep:
                raise RepositoryError(
                    f"dependency names of {name!r} "
                    f"must be non-empty strings"
                )
        result[name] = list(deps)
    return result


def _bfs_recursive(
    graph: Graph,
    fetch: DependencyFetcher,
    level: list[str],
    depth: int,
) -> None:
    """Рекурсивный BFS: обработать уровень и перейти к следующему.

    `level` — пакеты на глубине `depth`. Для каждого пакета берутся
    прямые зависимости; новые пакеты образуют следующий уровень,
    повторно встреченные — фиксируются как обратные рёбра (циклы),
    если их глубина не больше текущей.

    Рекурсия — переход к следующему уровню; BFS — обработка по
    уровням, а не в глубину. Узлы не переоткрываются, поэтому
    зацикливания не происходит даже при наличии циклов.
    """
    if not level or depth >= graph.max_depth:
        return

    next_level: list[str] = []
    for parent in level:
        dependencies = fetch(parent)
        for dep_name in dependencies:
            if (
                graph.filter_substring
                and graph.filter_substring in dep_name
            ):
                continue
            graph.add_edge(parent, dep_name)
            if dep_name in graph.nodes:
                dep_depth = graph.nodes[dep_name].depth
                if dep_depth <= depth:
                    graph.mark_cycle(parent, dep_name)
                continue
            graph.add_node(dep_name, depth + 1)
            next_level.append(dep_name)

    _bfs_recursive(graph, fetch, next_level, depth + 1)


def build_graph(
    root: str,
    max_depth: int,
    filter_substring: str,
    fetch: DependencyFetcher,
) -> Graph:
    """Построить граф зависимостей от `root` рекурсивным BFS.

    Параметры:
        root             — начальный пакет;
        max_depth        — максимальная глубина (>= 1);
        filter_substring — подстрока фильтрации (пустая — без фильтра);
        fetch            — функция получения прямых зависимостей пакета.

    Возвращает Graph с узлами, рёбрами и списком обратных рёбер.
    """
    graph = Graph(
        root=root,
        max_depth=max_depth,
        filter_substring=filter_substring,
    )
    graph.add_node(root, 0)
    _bfs_recursive(graph, fetch, [root], 0)
    return graph


def render_graph(graph: Graph) -> str:
    """Сформировать текстовое представление графа."""
    lines: list[str] = []
    lines.append(
        f"Graph for {graph.root!r} "
        f"(max_depth={graph.max_depth}, "
        f"filter={graph.filter_substring!r})"
    )
    lines.append("")
    lines.append(f"Nodes ({len(graph.nodes)}):")
    ordered = sorted(
        graph.nodes.values(),
        key=lambda node: (node.depth, node.name),
    )
    for node in ordered:
        lines.append(f"  depth {node.depth}: {node.name}")
    lines.append("")
    lines.append(f"Edges ({len(graph.edges)}):")
    for src, dst in graph.edges:
        lines.append(f"  {src} -> {dst}")
    lines.append("")
    if graph.cycles:
        lines.append(f"Back edges (cycles) ({len(graph.cycles)}):")
        for src, dst in graph.cycles:
            lines.append(f"  {src} -> {dst} (cycle)")
    else:
        lines.append("Back edges (cycles): none")
    return "\n".join(lines)


def topological_order(graph: Graph) -> tuple[list[str], list[tuple[str, str]]]:
    """Вернуть порядок загрузки пакетов (зависимости раньше зависимых).
    Возвращает пару:
        order  — список имён в порядке загрузки;
        broken — рёбра, которые пришлось разорвать из-за циклов.
    Алгоритм: DFS с тремя цветами.
    - «белый» (не посещён) → идём вглубь;
    - «серый» (в текущем стеке) → нашли обратное ребро, цикл;
    - «чёрный» (обработан) → узел уже добавлен в результат.
    Для цикла ребро попадает в `broken`, а узел всё равно добавляется
    в результат после своих зависимостей — так порядок остаётся
    максимально близким к топологическому.
    """
    white, gray, black = 0, 1, 2
    color: dict[str, int] = {name: white for name in graph.nodes}
    order: list[str] = []
    broken: list[tuple[str, str]] = []
    children: dict[str, list[str]] = {name: [] for name in graph.nodes}
    for src, dst in graph.edges:
        children[src].append(dst)

    def visit(name: str) -> None:
        if color[name] == black:
            return
        if color[name] == gray:
            return
        color[name] = gray
        for child in children[name]:
            if color[child] == gray:
                broken.append((name, child))
                continue
            visit(child)
        color[name] = black
        order.append(name)
    for name in graph.nodes:
        visit(name)

    return order, broken


def render_order(
    graph: Graph,
    order: list[str],
    broken: list[tuple[str, str]],
) -> str:
    """Сформировать текстовое представление порядка загрузки."""
    lines: list[str] = []
    lines.append(
        f"Load order for {graph.root!r} "
        f"(max_depth={graph.max_depth}, "
        f"filter={graph.filter_substring!r})"
    )
    lines.append("")
    lines.append(f"Order ({len(order)} packages):")
    for index, name in enumerate(order, start=1):
        depth = graph.nodes[name].depth
        lines.append(f"  {index:>2}. {name} (depth {depth})")
    lines.append("")
    if broken:
        lines.append(f"Broken edges (cycles) ({len(broken)}):")
        for src, dst in broken:
            lines.append(f"  {src} -> {dst} (cycle, order is approximate)")
    else:
        lines.append("Broken edges (cycles): none")
    return "\n".join(lines)


def render_dot(graph: Graph) -> str:
    """Сформировать DOT-представление графа для Graphviz."""
    lines: list[str] = []
    lines.append("digraph deps {")
    lines.append('    rankdir="LR";')
    lines.append('    node [shape=box, fontname="Helvetica"];')

    for name, node in graph.nodes.items():
        if name == graph.root:
            attrs = 'style="bold,filled", fillcolor="lightblue"'
        else:
            attrs = f'label="{name}\\n(depth {node.depth})"'
        lines.append(f'    "{name}" [{attrs}];')

    for src, dst in graph.edges:
        style = ' [style=dashed, color=red]'
        if (src, dst) in graph.cycles:
            style = ' [color=red, penwidth=2, label="cycle"]'
        lines.append(f'    "{src}" -> "{dst}"{style};')

    lines.append("}")
    return "\n".join(lines)
