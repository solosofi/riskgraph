"""Dependency graph builder — maps package dependency trees."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GraphNode:
    name: str
    version: str = ""
    ecosystem: str = "npm"
    risk_score: float = 0.0
    depth: int = 0
    children: list["GraphNode"] = field(default_factory=list)
    is_abandoned: bool = False


@dataclass
class DependencyGraph:
    root: GraphNode
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    total_packages: int = 0
    max_depth: int = 0

    def __post_init__(self):
        self._index()

    def _index(self):
        """Build flat index of all nodes."""
        self.nodes = {}
        self._walk(self.root)

    def _walk(self, node: GraphNode):
        key = f"{node.ecosystem}:{node.name}@{node.version}"
        if key not in self.nodes:
            self.nodes[key] = node
            self.total_packages += 1
            self.max_depth = max(self.max_depth, node.depth)
        for child in node.children:
            self._walk(child)

    def to_dict(self) -> dict:
        """Serialize for API/JSON output."""
        def _node_dict(n: GraphNode) -> dict:
            return {
                "name": n.name,
                "version": n.version,
                "ecosystem": n.ecosystem,
                "risk_score": n.risk_score,
                "depth": n.depth,
                "is_abandoned": n.is_abandoned,
                "children": [_node_dict(c) for c in n.children],
            }
        return _node_dict(self.root)

    def flatten(self) -> list[dict]:
        """Return flat list of all packages in the graph."""
        result = []
        def _walk(n: GraphNode):
            result.append({
                "name": n.name,
                "version": n.version,
                "ecosystem": n.ecosystem,
                "risk_score": n.risk_score,
                "depth": n.depth,
                "is_abandoned": n.is_abandoned,
            })
            for c in n.children:
                _walk(c)
        _walk(self.root)
        return result


def build_graph_from_npm(package_json: dict, max_depth: int = 5) -> DependencyGraph:
    """Build a dependency graph from npm package.json data."""
    deps = package_json.get("dependencies", {})
    dev_deps = package_json.get("devDependencies", {})
    all_deps = {**deps, **dev_deps}

    root = GraphNode(
        name=package_json.get("name", "unknown"),
        version=package_json.get("version", "0.0.0"),
        ecosystem="npm",
    )

    for name, version in all_deps.items():
        clean_version = version.lstrip("^~>=<")
        child = GraphNode(
            name=name,
            version=clean_version,
            ecosystem="npm",
            depth=1,
        )
        root.children.append(child)

    graph = DependencyGraph(root=root)
    return graph


def build_graph_from_pypi(requirements: list[str]) -> DependencyGraph:
    """Build a dependency graph from requirements.txt lines."""
    root = GraphNode(name="requirements", ecosystem="pypi")

    for line in requirements:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Parse name[extras]>=version
        name = line.split(">=")[0].split("==")[0].split("<=")[0].split("~=")[0].split("!=")[0].split("[")[0].strip()
        version = ""
        for op in [">=", "==", "<=", "~="]:
            if op in line:
                version = line.split(op)[1].strip().split(",")[0].strip()
                break
        child = GraphNode(name=name, version=version, ecosystem="pypi", depth=1)
        root.children.append(child)

    graph = DependencyGraph(root=root)
    return graph
