from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
import csv
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from typing import Any, cast

import matplotlib
matplotlib.use("TkAgg")
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


THEME = {
    "bg": "#0f0f0f",
    "panel": "#1a1a1a",
    "card": "#222222",
    "card_inner": "#292929",
    "card_alt": "#262626",
    "border": "#2f2f2f",
    "border_soft": "#3b3b3b",
    "text": "#ffffff",
    "muted": "#a3a3a3",
    "muted_soft": "#7e7e7e",
    "accent": "#00ffcc",
    "secondary": "#ffaa00",
    "danger": "#ff5d5d",
    "grid": "#2d2d2d",
    "grid_minor": "#212121", 
    "builder_grid": "#7a7a7a",
    "selection": "#00ffcc",
    "wire": "#7cf5df",
    "wire_pending": "#ffaa00",
}

GRID_SIZE = 24
COMPONENT_WIDTH = 108
COMPONENT_HEIGHT = 52

COMPONENT_META = {
    "Resistor": {"prefix": "R", "unit": "Ohm", "default": 1.0, "lambda_default": 1.0e-5, "category": "Passive", "shape": "rectangle"},
    "Inductor": {"prefix": "L", "unit": "H", "default": 1.0, "lambda_default": 1.6e-5, "category": "Passive", "shape": "rectangle"},
    "Capacitor": {"prefix": "C", "unit": "F", "default": 0.5, "lambda_default": 2.0e-5, "category": "Passive", "shape": "rectangle"},
    "Diode": {"prefix": "D", "unit": "", "default": 1.0, "lambda_default": 3.0e-5, "category": "Active", "shape": "diamond"},
    "Transistor": {"prefix": "Q", "unit": "", "default": 1.0, "lambda_default": 4.0e-5, "category": "Active", "shape": "diamond"},
    "IC": {"prefix": "U", "unit": "", "default": 1.0, "lambda_default": 5.0e-5, "category": "Active", "shape": "diamond"},
    "DCMotor": {"prefix": "M", "unit": "", "default": 1.0, "lambda_default": 7.0e-6, "category": "Motor", "shape": "circle"},
    "ACMotor": {"prefix": "M", "unit": "", "default": 1.0, "lambda_default": 6.0e-6, "category": "Motor", "shape": "circle"},
    "StepperMotor": {"prefix": "M", "unit": "", "default": 1.0, "lambda_default": 8.0e-6, "category": "Motor", "shape": "circle"},
    "ServoMotor": {"prefix": "M", "unit": "", "default": 1.0, "lambda_default": 7.5e-6, "category": "Motor", "shape": "circle"},
    "Battery": {"prefix": "B", "unit": "V", "default": 12.0, "lambda_default": 2.5e-6, "category": "Power", "shape": "rounded_rectangle"},
    "PowerSupply": {"prefix": "PS", "unit": "V", "default": 5.0, "lambda_default": 2.0e-6, "category": "Power", "shape": "rounded_rectangle"},
    "Source": {"prefix": "V", "unit": "V", "default": 1.0, "lambda_default": 2.0e-6, "category": "Power", "shape": "rounded_rectangle"},
    "Node": {"prefix": "J", "unit": "", "default": 0.0, "lambda_default": 1.0e-9, "category": "Passive", "shape": "circle"},
    "ParallelContainer": {"prefix": "P", "unit": "", "default": 0.0, "lambda_default": 1.0e-9, "category": "Passive", "shape": "rectangle"},
    "SeriesContainer": {"prefix": "S", "unit": "", "default": 0.0, "lambda_default": 1.0e-9, "category": "Passive", "shape": "rectangle"},
}

SIGNAL_OPTIONS = ["Noise", "Sine", "Multi-Sine", "Step", "Square", "Pulse", "Impulse", "Chirp"]

PRESET_LIBRARY = {
    "Series RLC Resonator": {
        "components": [
            ("Source", 144, 216, 1.0),
            ("Resistor", 312, 216, 1.0),
            ("Inductor", 480, 216, 1.2),
            ("Capacitor", 648, 216, 0.2),
        ],
        "connections": [(0, "right", 1, "left"), (1, "right", 2, "left"), (2, "right", 3, "left"), (3, "right", 0, "left")],
    },
    "Parallel RLC Resonator": {
        "components": [
            ("Source", 168, 228, 1.0),
            ("Node", 324, 144, 0.0),
            ("Node", 324, 312, 0.0),
            ("Resistor", 468, 144, 1.1),
            ("Inductor", 468, 228, 1.2),
            ("Capacitor", 468, 312, 0.2),
        ],
        "connections": [
            (0, "right", 1, "left"),
            (0, "left", 2, "left"),
            (1, "right", 3, "left"),
            (1, "down", 4, "left"),
            (1, "down", 5, "left"),
            (3, "right", 2, "right"),
            (4, "right", 2, "up"),
            (5, "right", 2, "right"),
        ],
    },
    "RC Low-Pass": {
        "components": [
            ("Source", 144, 216, 1.0),
            ("Resistor", 312, 216, 1.6),
            ("Capacitor", 480, 216, 0.18),
        ],
        "connections": [(0, "right", 1, "left"), (1, "right", 2, "left"), (2, "right", 0, "left")],
    },
    "RL High-Pass": {
        "components": [
            ("Source", 144, 216, 1.0),
            ("Inductor", 312, 216, 1.0),
            ("Resistor", 480, 216, 1.8),
        ],
        "connections": [(0, "right", 1, "left"), (1, "right", 2, "left"), (2, "right", 0, "left")],
    },
    "Band-Pass Ladder": {
        "components": [
            ("Source", 120, 216, 1.0),
            ("Resistor", 280, 216, 0.9),
            ("Inductor", 440, 216, 1.1),
            ("Capacitor", 600, 216, 0.22),
            ("Resistor", 760, 216, 0.7),
        ],
        "connections": [(0, "right", 1, "left"), (1, "right", 2, "left"), (2, "right", 3, "left"), (3, "right", 4, "left"), (4, "right", 0, "left")],
    },
}

NODE_TERMINALS = ("left", "right", "up", "down")
DEFAULT_TERMINALS = ("left", "right")


@dataclass(slots=True)
class Node:
    id: str
    component_ids: list[str] = field(default_factory=list)


@dataclass(slots=True)
class GraphComponent:
    id: str
    type: str
    value: float
    node1: str
    node2: str
    display_name: str


@dataclass(slots=True)
class CircuitGraph:
    nodes: list[Node]
    components: list[GraphComponent]
    source_component_ids: list[str]


@dataclass(slots=True)
class TopologyAnalysis:
    is_valid: bool
    message: str
    source_component_id: str | None
    source_nodes: tuple[str, str] | None
    floating_nodes: list[str]
    legacy_mode: str | None
    topology_name: str
    equivalent_l: float | None
    equivalent_c: float | None
    equivalent_r: float | None


def _append_graph_component(
    component_models: list[GraphComponent],
    node_members: dict[str, list[str]],
    *,
    component_id: str,
    component_type: str,
    value: float,
    node1: str,
    node2: str,
    display_name: str,
) -> None:
    component_models.append(
        GraphComponent(
            id=component_id,
            type=component_type,
            value=float(value),
            node1=node1,
            node2=node2,
            display_name=display_name,
        )
    )
    node_members.setdefault(node1, []).append(component_id)
    node_members.setdefault(node2, []).append(component_id)


def _new_internal_node_id(root_to_node_id: dict[str, str], node_members: dict[str, list[str]]) -> str:
    node_id = f"N{len(root_to_node_id) + 1}"
    root_to_node_id[f"__internal__:{node_id}"] = node_id
    node_members.setdefault(node_id, [])
    return node_id


def _expand_child_spec_to_graph(
    child: dict[str, Any],
    start_node: str,
    end_node: str,
    prefix: str,
    *,
    component_models: list[GraphComponent],
    node_members: dict[str, list[str]],
    root_to_node_id: dict[str, str],
) -> bool:
    child_type = str(child.get("type", ""))
    if child_type in {"Resistor", "Inductor", "Capacitor", "Source"}:
        try:
            value = float(child.get("value", 0.0))
        except (TypeError, ValueError):
            return False
        display_name = str(child.get("display_name", prefix))
        component_id = str(child.get("component_id", prefix))
        _append_graph_component(
            component_models,
            node_members,
            component_id=component_id,
            component_type=child_type,
            value=value,
            node1=start_node,
            node2=end_node,
            display_name=display_name,
        )
        return True

    container_type = str(child.get("container_type", ""))
    nested_children_raw = child.get("children", [])
    nested_children = [nested for nested in nested_children_raw if isinstance(nested, dict)]
    if container_type not in {"ParallelContainer", "SeriesContainer"}:
        return False
    if not nested_children:
        return False

    temp_component = ComponentModel(
        component_id=str(child.get("component_id", prefix)),
        component_type=container_type,
        display_name=str(child.get("display_name", container_type)),
        value=0.0,
        x=0.0,
        y=0.0,
        parallel_children=cast(list[dict[str, float | str]], nested_children),
    )
    if container_type == "ParallelContainer":
        reduced_type, reduced_value, _ = _parallel_container_summary(temp_component)
        if reduced_type is not None and reduced_value is not None:
            _append_graph_component(
                component_models,
                node_members,
                component_id=str(child.get("component_id", prefix)),
                component_type=reduced_type,
                value=reduced_value,
                node1=start_node,
                node2=end_node,
                display_name=str(child.get("display_name", prefix)),
            )
            return True
        for index, nested_child in enumerate(nested_children):
            if not _expand_child_spec_to_graph(
                nested_child,
                start_node,
                end_node,
                f"{prefix}/P{index + 1}",
                component_models=component_models,
                node_members=node_members,
                root_to_node_id=root_to_node_id,
            ):
                return False
        return True

    reduced_type, reduced_value, _ = _series_container_summary(temp_component)
    if reduced_type is not None and reduced_value is not None:
        _append_graph_component(
            component_models,
            node_members,
            component_id=str(child.get("component_id", prefix)),
            component_type=reduced_type,
            value=reduced_value,
            node1=start_node,
            node2=end_node,
            display_name=str(child.get("display_name", prefix)),
        )
        return True

    current_start = start_node
    for index, nested_child in enumerate(nested_children):
        current_end = end_node if index == len(nested_children) - 1 else _new_internal_node_id(root_to_node_id, node_members)
        if not _expand_child_spec_to_graph(
            nested_child,
            current_start,
            current_end,
            f"{prefix}/S{index + 1}",
            component_models=component_models,
            node_members=node_members,
            root_to_node_id=root_to_node_id,
        ):
            return False
        current_start = current_end
    return True


def parse_system_state(state: Any) -> CircuitGraph:
    components_by_id: dict[str, Any] = dict(getattr(state, "components", {}))
    connections_by_id: dict[str, Any] = dict(getattr(state, "connections", {}))

    terminals: list[str] = []
    for component in components_by_id.values():
        for terminal in _terminals_for_type(component.component_type):
            terminals.append(f"{component.component_id}:{terminal}")

    parent = {terminal: terminal for terminal in terminals}

    def find(item: str) -> str:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(a: str, b: str) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for component in components_by_id.values():
        if component.component_type != "Node":
            continue
        node_terminals = [f"{component.component_id}:{terminal}" for terminal in NODE_TERMINALS]
        anchor = node_terminals[0]
        for terminal in node_terminals[1:]:
            union(anchor, terminal)

    for connection in connections_by_id.values():
        union(
            f"{connection.from_component}:{connection.from_terminal}",
            f"{connection.to_component}:{connection.to_terminal}",
        )

    root_to_node_id: dict[str, str] = {}
    node_members: dict[str, list[str]] = {}
    component_models: list[GraphComponent] = []
    source_component_ids: list[str] = []
    power_source_types = {"Source", "PowerSupply", "Battery"}

    for component in components_by_id.values():
        if component.component_type == "Node":
            continue

        terminal_names = _terminals_for_type(component.component_type)
        root_a = find(f"{component.component_id}:{terminal_names[0]}")
        root_b = find(f"{component.component_id}:{terminal_names[1]}")
        node_a = root_to_node_id.setdefault(root_a, f"N{len(root_to_node_id) + 1}")
        node_b = root_to_node_id.setdefault(root_b, f"N{len(root_to_node_id) + 1}")

        if component.component_type == "ParallelContainer":
            child_prefix = component.display_name or component.component_id
            if not component.parallel_children or not _expand_child_spec_to_graph(
                {"container_type": "ParallelContainer", "display_name": child_prefix, "children": component.parallel_children, "component_id": component.component_id},
                node_a,
                node_b,
                component.component_id,
                component_models=component_models,
                node_members=node_members,
                root_to_node_id=root_to_node_id,
            ):
                _append_graph_component(
                    component_models,
                    node_members,
                    component_id=component.component_id,
                    component_type="InvalidContainer",
                    value=0.0,
                    node1=node_a,
                    node2=node_b,
                    display_name=component.display_name,
                )
            continue

        if component.component_type == "SeriesContainer":
            child_prefix = component.display_name or component.component_id
            if not component.parallel_children or not _expand_child_spec_to_graph(
                {"container_type": "SeriesContainer", "display_name": child_prefix, "children": component.parallel_children, "component_id": component.component_id},
                node_a,
                node_b,
                component.component_id,
                component_models=component_models,
                node_members=node_members,
                root_to_node_id=root_to_node_id,
            ):
                _append_graph_component(
                    component_models,
                    node_members,
                    component_id=component.component_id,
                    component_type="InvalidContainer",
                    value=0.0,
                    node1=node_a,
                    node2=node_b,
                    display_name=component.display_name,
                )
            continue

        graph_component_type = "Source" if component.component_type in power_source_types else component.component_type
        _append_graph_component(
            component_models,
            node_members,
            component_id=component.component_id,
            component_type=graph_component_type,
            value=float(component.value),
            node1=node_a,
            node2=node_b,
            display_name=getattr(component, "display_name", component.component_id),
        )
        if graph_component_type == "Source":
            source_component_ids.append(component.component_id)

    nodes = [Node(id=node_id, component_ids=sorted(set(component_ids))) for node_id, component_ids in sorted(node_members.items())]
    return CircuitGraph(nodes=nodes, components=component_models, source_component_ids=source_component_ids)


def _terminals_for_type(component_type: str) -> tuple[str, ...]:
    if component_type == "Node":
        return NODE_TERMINALS
    return DEFAULT_TERMINALS


def _child_spec_summary(child: dict[str, Any]) -> tuple[str | None, float | None]:
    if "type" in child and "value" in child:
        child_type = str(child.get("type", ""))
        if child_type not in {"Resistor", "Inductor", "Capacitor"}:
            return None, None
        try:
            return child_type, float(child.get("value", 0.0))
        except (TypeError, ValueError):
            return None, None

    container_type = str(child.get("container_type", ""))
    nested_children = child.get("children", [])
    nested_component = ComponentModel(
        component_id=str(child.get("component_id", child.get("display_name", "nested"))),
        component_type=container_type,
        display_name=str(child.get("display_name", container_type or "Nested")),
        value=0.0,
        x=0.0,
        y=0.0,
        parallel_children=cast(list[dict[str, Any]], nested_children if isinstance(nested_children, list) else []),
    )
    if container_type == "ParallelContainer":
        child_type, child_value, _ = _parallel_container_summary(nested_component)
        return child_type, child_value
    if container_type == "SeriesContainer":
        child_type, child_value, _ = _series_container_summary(nested_component)
        return child_type, child_value
    return None, None


def _parallel_container_summary(component: ComponentModel) -> tuple[str | None, float | None, int]:
    children = [child for child in component.parallel_children if isinstance(child, dict)]
    if not children:
        return None, None, 0
    reduced_children: list[tuple[str, float]] = []
    for child in children:
        child_type, child_value = _child_spec_summary(cast(dict[str, Any], child))
        if child_type is None or child_value is None:
            return None, None, len(children)
        reduced_children.append((child_type, child_value))
    child_types = {child_type for child_type, _ in reduced_children}
    if len(child_types) != 1:
        return None, None, len(children)
    component_type = next(iter(child_types))
    values = [value for _, value in reduced_children]
    if component_type == "Resistor":
        equivalent = _parallel_equivalent(values)
    elif component_type == "Inductor":
        equivalent = _parallel_equivalent(values)
    elif component_type == "Capacitor":
        equivalent = sum(values)
    else:
        return None, None, len(children)
    return component_type, equivalent, len(children)


def _series_container_summary(component: ComponentModel) -> tuple[str | None, float | None, int]:
    children = [child for child in component.parallel_children if isinstance(child, dict)]
    if not children:
        return None, None, 0
    reduced_children: list[tuple[str, float]] = []
    for child in children:
        child_type, child_value = _child_spec_summary(cast(dict[str, Any], child))
        if child_type is None or child_value is None:
            return None, None, len(children)
        reduced_children.append((child_type, child_value))
    child_types = {child_type for child_type, _ in reduced_children}
    if len(child_types) != 1:
        return None, None, len(children)
    component_type = next(iter(child_types))
    values = [value for _, value in reduced_children]
    if component_type == "Capacitor":
        equivalent = _series_capacitance(values)
    elif component_type in {"Resistor", "Inductor"}:
        equivalent = sum(values)
    else:
        return None, None, len(children)
    return component_type, equivalent, len(children)


def _normalize_container_children(raw_children: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_children, list):
        return []
    normalized: list[dict[str, Any]] = []
    for child in raw_children:
        if not isinstance(child, dict):
            continue
        container_type = child.get("container_type")
        if container_type in {"ParallelContainer", "SeriesContainer"}:
            normalized_container: dict[str, Any] = {
                "container_type": str(container_type),
                "display_name": str(child.get("display_name", container_type)),
                "children": _normalize_container_children(child.get("children", [])),
            }
            normalized.append(normalized_container)
            continue
        child_type = child.get("type", child.get("component_type"))
        child_value = child.get("value")
        if child_type is None or child_value is None:
            continue
        try:
            normalized_child: dict[str, Any] = {
                "type": str(child_type),
                "value": float(child_value),
            }
        except (TypeError, ValueError):
            continue
        display_name = child.get("display_name")
        if display_name is not None:
            normalized_child["display_name"] = str(display_name)
        container_type = child.get("container_type")
        if container_type is not None:
            normalized_child["container_type"] = str(container_type)
        if "lambda_" in child:
            normalized_child["lambda_"] = _normalize_lambda(child.get("lambda_"), float(_meta_for_component(str(child_type)).get("lambda_default", 1.0e-5)))
        if "category" in child:
            normalized_child["category"] = str(child.get("category"))
        if "shape" in child:
            normalized_child["shape"] = str(child.get("shape"))
        if "metadata" in child and isinstance(child.get("metadata"), dict):
            normalized_child["metadata"] = dict(cast(dict[str, Any], child.get("metadata")))
        normalized.append(normalized_child)
    return normalized


def _summary_for_container_type(
    container_type: str,
    children: list[dict[str, Any]],
) -> tuple[str | None, float | None, int]:
    temp_component = ComponentModel(
        component_id="summary",
        component_type=container_type,
        display_name=container_type,
        value=0.0,
        x=0.0,
        y=0.0,
        parallel_children=cast(list[dict[str, float | str]], children),
    )
    if container_type == "ParallelContainer":
        return _parallel_container_summary(temp_component)
    if container_type == "SeriesContainer":
        return _series_container_summary(temp_component)
    return None, None, len(children)


def analyze_circuit(graph: CircuitGraph) -> TopologyAnalysis:
    sources = [component for component in graph.components if component.type == "Source"]
    if not graph.components:
        return TopologyAnalysis(False, "No components in the circuit graph.", None, None, [], None, "Manual", None, None, None)
    invalid_containers = [component for component in graph.components if component.type == "InvalidContainer"]
    if invalid_containers:
        return TopologyAnalysis(False, "Containers must contain valid passive parts or valid nested structures.", None, None, [], None, "Unresolved", None, None, None)
    if len(sources) != 1:
        return TopologyAnalysis(False, "Exactly one source is required.", None, None, [], None, "Unresolved", None, None, None)

    source = sources[0]
    if source.node1 == source.node2:
        return TopologyAnalysis(False, "Source terminals collapse onto the same node.", source.id, None, [], None, "Unresolved", None, None, None)

    passive_components = [component for component in graph.components if component.type != "Source"]
    if not passive_components:
        return TopologyAnalysis(False, "Add passive components to create a solvable network.", source.id, (source.node1, source.node2), [], None, "Manual", None, None, None)

    source_nodes = (source.node1, source.node2)
    adjacency = _build_node_adjacency(passive_components)
    reachable = _reachable_nodes(adjacency, source_nodes[0]) | {source_nodes[0]}
    floating_nodes = sorted(node.id for node in graph.nodes if node.id not in reachable and node.id not in source_nodes)
    if floating_nodes:
        return TopologyAnalysis(False, "Floating nodes detected in the circuit graph.", source.id, source_nodes, floating_nodes, None, "Unresolved", None, None, None)

    legacy_parallel = _detect_parallel_family(passive_components, source_nodes)
    if legacy_parallel is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_parallel
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "parallel", topology_name, equivalent_l, equivalent_c, equivalent_r)

    legacy_series = _detect_series_family(passive_components, source_nodes)
    if legacy_series is not None:
        topology_name, equivalent_l, equivalent_c, equivalent_r = legacy_series
        return TopologyAnalysis(True, f"{topology_name} detected.", source.id, source_nodes, [], "series", topology_name, equivalent_l, equivalent_c, equivalent_r)

    return TopologyAnalysis(
        True,
        "Valid graph circuit detected. Use graph-based nodal analysis instead of legacy LCR reduction.",
        source.id,
        source_nodes,
        [],
        None,
        "Unresolved",
        None,
        None,
        None,
    )


def _build_node_adjacency(components: list[GraphComponent]) -> dict[str, list[str]]:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for component in components:
        if component.node1 == component.node2:
            continue
        adjacency[component.node1].append(component.node2)
        adjacency[component.node2].append(component.node1)
    return dict(adjacency)


def _reachable_nodes(adjacency: dict[str, list[str]], start: str) -> set[str]:
    visited: set[str] = set()
    queue: deque[str] = deque([start])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for neighbor in adjacency.get(node, []):
            if neighbor not in visited:
                queue.append(neighbor)
    return visited


def _detect_parallel_family(passive_components: list[GraphComponent], source_nodes: tuple[str, str]) -> tuple[str, float | None, float | None, float | None] | None:
    branches = _extract_parallel_branches(passive_components, source_nodes)
    if branches is None or len(branches) < 1:
        return None

    reduced_branches = [_reduce_series_branch(branch) for branch in branches]
    if any(reduced is None for reduced in reduced_branches):
        return None

    reduced_by_type: dict[str, list[float]] = defaultdict(list)
    for reduced in reduced_branches:
        component_type, value = reduced
        reduced_by_type[component_type].append(value)

    topology_name = _topology_name("Parallel", reduced_by_type)
    resistance = _parallel_equivalent(reduced_by_type["Resistor"]) if "Resistor" in reduced_by_type else None
    inductance = _parallel_equivalent(reduced_by_type["Inductor"]) if "Inductor" in reduced_by_type else None
    capacitance = sum(reduced_by_type["Capacitor"]) if "Capacitor" in reduced_by_type else None
    return topology_name, inductance, capacitance, resistance


def _detect_series_family(passive_components: list[GraphComponent], source_nodes: tuple[str, str]) -> tuple[str, float | None, float | None, float | None] | None:
    adjacency: dict[str, list[str]] = defaultdict(list)
    for component in passive_components:
        if component.node1 == component.node2:
            return None
        adjacency[component.node1].append(component.node2)
        adjacency[component.node2].append(component.node1)

    if source_nodes[0] not in adjacency or source_nodes[1] not in adjacency:
        return None

    visited = _reachable_nodes(dict(adjacency), source_nodes[0])
    if source_nodes[1] not in visited:
        return None

    for node, neighbors in adjacency.items():
        degree = len(neighbors)
        if node in source_nodes and degree != 1:
            return None
        if node not in source_nodes and degree != 2:
            return None

    reduced_by_type: dict[str, list[float]] = defaultdict(list)
    for component in passive_components:
        reduced_by_type[component.type].append(component.value)

    topology_name = _topology_name("Series", reduced_by_type)
    resistance = sum(reduced_by_type["Resistor"]) if "Resistor" in reduced_by_type else None
    inductance = sum(reduced_by_type["Inductor"]) if "Inductor" in reduced_by_type else None
    capacitance = _series_capacitance(reduced_by_type["Capacitor"]) if "Capacitor" in reduced_by_type else None
    return topology_name, inductance, capacitance, resistance


def _parallel_equivalent(values: list[float]) -> float:
    reciprocal_sum = sum(1.0 / value for value in values if value > 0)
    return 1.0 / reciprocal_sum if reciprocal_sum > 0 else math.inf


def _series_capacitance(values: list[float]) -> float:
    reciprocal_sum = sum(1.0 / value for value in values if value > 0)
    return 1.0 / reciprocal_sum if reciprocal_sum > 0 else 0.0


def _extract_parallel_branches(passive_components: list[GraphComponent], source_nodes: tuple[str, str]) -> list[list[GraphComponent]] | None:
    start_node, return_node = source_nodes
    node_to_components: dict[str, list[GraphComponent]] = defaultdict(list)
    for component in passive_components:
        if component.node1 == component.node2:
            return None
        node_to_components[component.node1].append(component)
        node_to_components[component.node2].append(component)

    branch_starts = list(node_to_components.get(start_node, []))
    if not branch_starts:
        return None

    visited_component_ids: set[str] = set()
    branches: list[list[GraphComponent]] = []

    for start_component in branch_starts:
        if start_component.id in visited_component_ids:
            continue
        branch: list[GraphComponent] = []
        current_component = start_component
        current_node = start_node

        while True:
            if current_component.id in visited_component_ids:
                return None
            visited_component_ids.add(current_component.id)
            branch.append(current_component)

            next_node = current_component.node2 if current_component.node1 == current_node else current_component.node1
            if next_node == return_node:
                branches.append(branch)
                break

            next_components = [component for component in node_to_components.get(next_node, []) if component.id != current_component.id]
            if len(next_components) != 1:
                return None

            current_node = next_node
            current_component = next_components[0]

    if visited_component_ids != {component.id for component in passive_components}:
        return None
    return branches


def _reduce_series_branch(branch: list[GraphComponent]) -> tuple[str, float] | None:
    branch_types = {component.type for component in branch}
    if len(branch_types) != 1:
        return None
    component_type = branch[0].type
    values = [component.value for component in branch]
    if component_type == "Resistor":
        return component_type, sum(values)
    if component_type == "Inductor":
        return component_type, sum(values)
    if component_type == "Capacitor":
        return component_type, _series_capacitance(values)
    return None


def _topology_name(prefix: str, reduced_by_type: dict[str, list[float]]) -> str:
    suffix_parts = []
    if "Resistor" in reduced_by_type:
        suffix_parts.append("R")
    if "Inductor" in reduced_by_type:
        suffix_parts.append("L")
    if "Capacitor" in reduced_by_type:
        suffix_parts.append("C")
    if not suffix_parts:
        return f"{prefix} Unknown"
    return f"{prefix} {''.join(suffix_parts)}"


class ReliabilityNode:
    def reliability(self, t: float) -> float:
        raise NotImplementedError

    def simulate_snapshot(self, t: float, rng: np.random.Generator) -> bool:
        raise NotImplementedError

    def sample_failure_time(self, rng: np.random.Generator) -> float:
        raise NotImplementedError


@dataclass
class ReliabilityComponentNode(ReliabilityNode):
    name: str
    lambda_: float

    def reliability(self, t: float) -> float:
        return math.exp(-self.lambda_ * t)

    def simulate_snapshot(self, t: float, rng: np.random.Generator) -> bool:
        fail_probability = 1.0 - math.exp(-self.lambda_ * t)
        return float(rng.random()) >= fail_probability

    def sample_failure_time(self, rng: np.random.Generator) -> float:
        u = max(float(rng.random()), 1.0e-12)
        return -math.log(u) / self.lambda_


@dataclass
class ReliabilitySeriesNode(ReliabilityNode):
    nodes: list[ReliabilityNode]

    def reliability(self, t: float) -> float:
        r = 1.0
        for node in self.nodes:
            r *= node.reliability(t)
        return r

    def simulate_snapshot(self, t: float, rng: np.random.Generator) -> bool:
        for node in self.nodes:
            if not node.simulate_snapshot(t, rng):
                return False
        return True

    def sample_failure_time(self, rng: np.random.Generator) -> float:
        return min(node.sample_failure_time(rng) for node in self.nodes)


@dataclass
class ReliabilityParallelNode(ReliabilityNode):
    nodes: list[ReliabilityNode]

    def reliability(self, t: float) -> float:
        product = 1.0
        for node in self.nodes:
            product *= 1.0 - node.reliability(t)
        return 1.0 - product

    def simulate_snapshot(self, t: float, rng: np.random.Generator) -> bool:
        for node in self.nodes:
            if node.simulate_snapshot(t, rng):
                return True
        return False

    def sample_failure_time(self, rng: np.random.Generator) -> float:
        return max(node.sample_failure_time(rng) for node in self.nodes)


def _meta_for_component(component_type: str) -> dict[str, Any]:
    return COMPONENT_META.get(component_type, {"lambda_default": 1.0e-5, "category": "Passive", "shape": "rectangle"})


def _normalize_lambda(value: Any, fallback: float) -> float:
    try:
        candidate = float(value)
    except (TypeError, ValueError):
        return fallback
    return candidate if candidate > 0 else fallback


def _reliability_node_from_child(child: dict[str, Any], fallback_name: str) -> ReliabilityNode | None:
    child_type = str(child.get("type", ""))
    if child_type:
        meta = _meta_for_component(child_type)
        name = str(child.get("display_name", fallback_name))
        lambda_ = _normalize_lambda(child.get("lambda_", meta.get("lambda_default", 1.0e-5)), float(meta.get("lambda_default", 1.0e-5)))
        return ReliabilityComponentNode(name=name, lambda_=lambda_)

    container_type = str(child.get("container_type", ""))
    nested = child.get("children", [])
    if not isinstance(nested, list):
        return None
    nodes: list[ReliabilityNode] = []
    for index, nested_child in enumerate(nested):
        if not isinstance(nested_child, dict):
            continue
        node = _reliability_node_from_child(nested_child, f"{fallback_name}-{index + 1}")
        if node is not None:
            nodes.append(node)
    if not nodes:
        return None
    if container_type == "ParallelContainer":
        return ReliabilityParallelNode(nodes)
    if container_type == "SeriesContainer":
        return ReliabilitySeriesNode(nodes)
    return None


def build_reliability_system(state: "SystemState") -> ReliabilityNode | None:
    nodes: list[tuple[float, ReliabilityNode]] = []
    for component in state.components.values():
        if component.component_type in {"Source", "Node"}:
            continue
        if component.component_type == "ParallelContainer":
            children = [child for child in component.parallel_children if isinstance(child, dict)]
            child_nodes = [node for node in (_reliability_node_from_child(child, component.display_name) for child in children) if node is not None]
            if child_nodes:
                nodes.append((component.x, ReliabilityParallelNode(child_nodes)))
            continue
        if component.component_type == "SeriesContainer":
            children = [child for child in component.parallel_children if isinstance(child, dict)]
            child_nodes = [node for node in (_reliability_node_from_child(child, component.display_name) for child in children) if node is not None]
            if child_nodes:
                nodes.append((component.x, ReliabilitySeriesNode(child_nodes)))
            continue
        lambda_ = _normalize_lambda(component.lambda_, float(_meta_for_component(component.component_type).get("lambda_default", 1.0e-5)))
        nodes.append((component.x, ReliabilityComponentNode(component.display_name, lambda_)))

    if not nodes:
        return None
    ordered = [node for _, node in sorted(nodes, key=lambda pair: pair[0])]
    topology_text = state.derived_parameters.topology.lower()
    if topology_text.startswith("parallel"):
        return ReliabilityParallelNode(ordered)
    return ReliabilitySeriesNode(ordered)


def reliability_snapshot_monte_carlo(system: ReliabilityNode, t: float, trials: int, rng: np.random.Generator) -> float:
    survived = 0
    for _ in range(max(trials, 1)):
        if system.simulate_snapshot(t, rng):
            survived += 1
    return survived / max(trials, 1)


def reliability_calculate_warranty(system: ReliabilityNode, target_reliability: float) -> float:
    low, high = 0.0, 100000.0
    mid = 0.0
    while high - low > 1.0:
        mid = (low + high) / 2.0
        if system.reliability(mid) > target_reliability:
            low = mid
        else:
            high = mid
    return mid


def format_duration_hours(total_hours: float) -> str:
    total_minutes = max(int(round(total_hours * 60.0)), 0)
    minutes_per_hour = 60
    minutes_per_day = 24 * minutes_per_hour
    minutes_per_month = 30 * minutes_per_day
    minutes_per_year = 365 * minutes_per_day

    years, rem = divmod(total_minutes, minutes_per_year)
    months, rem = divmod(rem, minutes_per_month)
    days, rem = divmod(rem, minutes_per_day)
    hours, minutes = divmod(rem, minutes_per_hour)

    parts: list[str] = []
    if years:
        parts.append(f"{years} year{'s' if years != 1 else ''}")
    if months:
        parts.append(f"{months} month{'s' if months != 1 else ''}")
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    return ", ".join(parts)


def reliability_lifetime_samples(system: ReliabilityNode, trials: int, rng: np.random.Generator) -> np.ndarray:
    return np.array([system.sample_failure_time(rng) for _ in range(max(trials, 1))], dtype=float)


def reliability_empirical_curve(failure_times: np.ndarray, points: int = 100) -> tuple[np.ndarray, np.ndarray]:
    if failure_times.size == 0:
        return np.array([], dtype=float), np.array([], dtype=float)
    max_time = float(np.max(failure_times))
    time_grid = np.linspace(0.0, max_time * 1.02, max(points, 2))
    reliability_values = np.array([np.mean(failure_times > t) for t in time_grid], dtype=float)
    return time_grid, reliability_values


@dataclass
class ComponentModel:
    component_id: str
    component_type: str
    display_name: str
    value: float
    x: float
    y: float
    lambda_: float = 1.0e-5
    category: str = "Passive"
    shape: str = "rectangle"
    metadata: dict[str, str] = field(default_factory=dict)
    parallel_children: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ConnectionModel:
    connection_id: str
    from_component: str
    from_terminal: str
    to_component: str
    to_terminal: str


@dataclass
class CircuitInterpretation:
    topology: str
    message: str
    is_valid: bool
    L: float | None
    C: float | None
    R: float | None


@dataclass
class SimulationResult:
    time: np.ndarray
    input_signal: np.ndarray
    current: np.ndarray
    charge: np.ndarray
    component_voltages: dict[str, np.ndarray] = field(default_factory=dict)
    component_currents: dict[str, np.ndarray] = field(default_factory=dict)
    output_label: str = "Circuit Current"


@dataclass
class FrequencyResponse:
    frequency: np.ndarray
    magnitude: np.ndarray
    phase: np.ndarray
    smoothed_magnitude: np.ndarray


@dataclass
class GraphSolveResult:
    frequency: np.ndarray
    transfer: np.ndarray
    impedance: np.ndarray
    component_transfer: dict[str, np.ndarray] = field(default_factory=dict)
    component_current_transfer: dict[str, np.ndarray] = field(default_factory=dict)


@dataclass
class AnalysisSummary:
    resonance_hz: float
    peak_gain: float
    damping_ratio: float
    system_type: str
    quality_factor: float
    peak_index: int


@dataclass
class TransientSummary:
    rise_time: float | None
    settling_time: float | None
    overshoot_pct: float | None
    peak_time: float | None


@dataclass
class DerivedParameters:
    L: float | None
    C: float | None
    R: float | None
    topology: str
    message: str
    is_valid: bool

    def update(
        self,
        *,
        L: float | None,
        C: float | None,
        R: float | None,
        topology: str,
        message: str,
        is_valid: bool,
    ) -> None:
        self.L = L
        self.C = C
        self.R = R
        self.topology = topology
        self.message = message
        self.is_valid = is_valid


class SystemState:
    def __init__(self) -> None:
        self.default_values = {
            "L": 1.2,
            "C": 0.2,
            "R": 0.9,
            "signal_type": "Noise",
            "signal_amplitude": 1.0,
            "signal_frequency": 1.2,
            "signal_offset": 0.0,
            "signal_frequency_2": 3.5,
            "pulse_width": 0.18,
            "chirp_end_frequency": 8.0,
            "source_resistance": 0.0,
            "inductor_series_resistance": 0.04,
            "capacitor_esr": 0.02,
        }
        self.L = self.default_values["L"]
        self.C = self.default_values["C"]
        self.R = self.default_values["R"]
        self.signal_type = self.default_values["signal_type"]
        self.signal_amplitude = self.default_values["signal_amplitude"]
        self.signal_frequency = self.default_values["signal_frequency"]
        self.signal_offset = self.default_values["signal_offset"]
        self.signal_frequency_2 = self.default_values["signal_frequency_2"]
        self.pulse_width = self.default_values["pulse_width"]
        self.chirp_end_frequency = self.default_values["chirp_end_frequency"]
        self.source_resistance = self.default_values["source_resistance"]
        self.inductor_series_resistance = self.default_values["inductor_series_resistance"]
        self.capacitor_esr = self.default_values["capacitor_esr"]

        self.components: dict[str, ComponentModel] = {}
        self.connections: dict[str, ConnectionModel] = {}
        self.selected_component_id: str | None = None
        self.selected_component_ids: list[str] = []
        self.ctrl_multiselect_redirect = False
        self.derived_parameters = DerivedParameters(
            L=self.L,
            C=self.C,
            R=self.R,
            topology="Manual",
            message="Manual simulation parameters.",
            is_valid=False,
        )

        self.dt = 0.001
        self.duration = 12.0
        self.analysis_min_hz = 0.05
        self.analysis_max_hz = 8.0
        self.smoothing_window = 21
        self.time = np.arange(0.0, self.duration, self.dt)

        self._component_counter = 1
        self._connection_counter = 1

    def next_component_id(self, component_type: str) -> str:
        component_id = f"{COMPONENT_META[component_type]['prefix']}{self._component_counter}"
        self._component_counter += 1
        return component_id

    def next_connection_id(self) -> str:
        connection_id = f"W{self._connection_counter}"
        self._connection_counter += 1
        return connection_id

    def add_component(self, component_type: str, x: float, y: float, value: float | None = None) -> ComponentModel:
        component_id = self.next_component_id(component_type)
        meta = _meta_for_component(component_type)
        component = ComponentModel(
            component_id=component_id,
            component_type=component_type,
            display_name=component_id,
            value=value if value is not None else COMPONENT_META[component_type]["default"],
            x=x,
            y=y,
            lambda_=_normalize_lambda(meta.get("lambda_default", 1.0e-5), 1.0e-5),
            category=str(meta.get("category", "Passive")),
            shape=str(meta.get("shape", "rectangle")),
            metadata={},
            parallel_children=[],
        )
        self.components[component.component_id] = component
        return component

    def update_component_position(self, component_id: str, x: float, y: float) -> None:
        self.components[component_id].x = x
        self.components[component_id].y = y

    def update_component_value(self, component_id: str, value: float) -> None:
        self.components[component_id].value = value

    def update_component_profile(
        self,
        component_id: str,
        *,
        display_name: str | None = None,
        lambda_: float | None = None,
        category: str | None = None,
        metadata_text: str | None = None,
    ) -> bool:
        component = self.components.get(component_id)
        if component is None:
            return False
        if display_name is not None:
            cleaned = display_name.strip()
            if cleaned:
                component.display_name = cleaned
        if lambda_ is not None:
            if float(lambda_) <= 0:
                return False
            component.lambda_ = float(lambda_)
        if category is not None:
            component.category = category
            category_shape = {"Passive": "rectangle", "Active": "diamond", "Motor": "circle", "Power": "rounded_rectangle"}
            component.shape = category_shape.get(category, component.shape)
        if metadata_text is not None:
            component.metadata = {"notes": metadata_text}
        return True

    def update_container_child_value(self, component_id: str, child_index: int, value: float) -> bool:
        component = self.components.get(component_id)
        if component is None:
            return False
        if child_index < 0 or child_index >= len(component.parallel_children):
            return False
        child = component.parallel_children[child_index]
        if not isinstance(child, dict) or "value" not in child:
            return False
        child["value"] = float(value)
        return True

    def update_control_value(self, control_key: str, value: float) -> bool:
        if "|child|" not in control_key:
            if control_key in self.components:
                self.update_component_value(control_key, value)
                return True
            return False
        component_id, child_path = control_key.split("|child|", 1)
        component = self.components.get(component_id)
        if component is None:
            return False
        children: list[dict[str, Any]] = cast(list[dict[str, Any]], component.parallel_children)
        path_parts = [part for part in child_path.split(".") if part]
        target: dict[str, Any] | None = None
        for depth, part in enumerate(path_parts):
            try:
                child_index = int(part)
            except ValueError:
                return False
            if child_index < 0 or child_index >= len(children):
                return False
            child = children[child_index]
            if not isinstance(child, dict):
                return False
            if depth == len(path_parts) - 1:
                target = child
                break
            nested_children = child.get("children")
            if not isinstance(nested_children, list):
                return False
            children = cast(list[dict[str, Any]], nested_children)
        if target is None or "value" not in target:
            return False
        target["value"] = float(value)
        return True

    def _component_to_child_spec(self, component: ComponentModel) -> dict[str, Any]:
        if component.component_type in {"ParallelContainer", "SeriesContainer"}:
            return {
                "container_type": component.component_type,
                "display_name": component.display_name,
                "children": deepcopy(component.parallel_children),
            }
        return {
            "type": component.component_type,
            "display_name": component.display_name,
            "value": float(component.value),
            "lambda_": float(component.lambda_),
            "category": component.category,
            "shape": component.shape,
            "metadata": deepcopy(component.metadata),
        }

    def add_child_spec_to_container(
        self,
        component_id: str,
        child_spec: dict[str, Any],
        path: list[int] | None = None,
    ) -> bool:
        component = self.components.get(component_id)
        if component is None or not isinstance(child_spec, dict):
            return False
        target_type = component.component_type
        target_children: list[dict[str, Any]] = cast(list[dict[str, Any]], component.parallel_children)
        for child_index in path or []:
            if child_index < 0 or child_index >= len(target_children):
                return False
            nested_child = target_children[child_index]
            if not isinstance(nested_child, dict):
                return False
            nested_type = str(nested_child.get("container_type", ""))
            if nested_type not in {"ParallelContainer", "SeriesContainer"}:
                return False
            target_type = nested_type
            nested_children = nested_child.setdefault("children", [])
            if not isinstance(nested_children, list):
                return False
            target_children = cast(list[dict[str, Any]], nested_children)

        if target_type == "ParallelContainer":
            child_type, _ = _child_spec_summary(child_spec)
            if child_type is None and str(child_spec.get("container_type", "")) not in {"ParallelContainer", "SeriesContainer"}:
                return False
        elif target_type != "SeriesContainer":
            return False
        target_children.append(deepcopy(child_spec))
        return True

    def rename_component(self, component_id: str, display_name: str) -> None:
        cleaned = display_name.strip()
        if not cleaned:
            return
        self.components[component_id].display_name = cleaned

    def add_parallel_child(self, component_id: str, child_type: str, value: float) -> bool:
        if component_id not in self.components:
            return False
        component = self.components[component_id]
        if component.component_type != "ParallelContainer" or child_type not in {"Resistor", "Inductor", "Capacitor"}:
            return False
        meta = _meta_for_component(child_type)
        return self.add_child_spec_to_container(
            component_id,
            {
                "type": child_type,
                "value": float(value),
                "lambda_": float(meta.get("lambda_default", 1.0e-5)),
                "category": str(meta.get("category", "Passive")),
                "shape": str(meta.get("shape", "rectangle")),
                "metadata": {},
            },
        )

    def add_series_child(self, component_id: str, child_type: str, value: float) -> bool:
        if component_id not in self.components:
            return False
        component = self.components[component_id]
        if component.component_type != "SeriesContainer" or child_type not in {"Resistor", "Inductor", "Capacitor"}:
            return False
        meta = _meta_for_component(child_type)
        return self.add_child_spec_to_container(
            component_id,
            {
                "type": child_type,
                "value": float(value),
                "lambda_": float(meta.get("lambda_default", 1.0e-5)),
                "category": str(meta.get("category", "Passive")),
                "shape": str(meta.get("shape", "rectangle")),
                "metadata": {},
            },
        )

    def remove_component(self, component_id: str) -> None:
        if component_id not in self.components:
            return
        del self.components[component_id]
        if self.selected_component_id == component_id:
            self.selected_component_id = None
        connection_ids = [
            connection_id
            for connection_id, connection in self.connections.items()
            if component_id in (connection.from_component, connection.to_component)
        ]
        for connection_id in connection_ids:
            del self.connections[connection_id]

    def add_connection(self, from_component: str, from_terminal: str, to_component: str, to_terminal: str) -> ConnectionModel | None:
        if from_component == to_component:
            return None
        for connection in self.connections.values():
            same_direction = (
                connection.from_component == from_component
                and connection.from_terminal == from_terminal
                and connection.to_component == to_component
                and connection.to_terminal == to_terminal
            )
            reverse_direction = (
                connection.from_component == to_component
                and connection.from_terminal == to_terminal
                and connection.to_component == from_component
                and connection.to_terminal == from_terminal
            )
            if same_direction or reverse_direction:
                return None
        connection = ConnectionModel(
            connection_id=self.next_connection_id(),
            from_component=from_component,
            from_terminal=from_terminal,
            to_component=to_component,
            to_terminal=to_terminal,
        )
        self.connections[connection.connection_id] = connection
        return connection

    def remove_connection(self, connection_id: str) -> None:
        self.connections.pop(connection_id, None)

    def clear_circuit(self) -> None:
        self.components.clear()
        self.connections.clear()
        self.selected_component_id = None
        self.selected_component_ids = []
        self.ctrl_multiselect_redirect = False
        self.derived_parameters.update(
            L=self.L,
            C=self.C,
            R=self.R,
            topology="Manual",
            message="Workspace reset. Add components to derive circuit parameters.",
            is_valid=False,
        )

    def set_signal_type(self, signal_type: str) -> None:
        self.signal_type = signal_type

    def set_signal_settings(
        self,
        *,
        amplitude: float | None = None,
        frequency: float | None = None,
        offset: float | None = None,
        secondary_frequency: float | None = None,
        pulse_width: float | None = None,
        chirp_end_frequency: float | None = None,
    ) -> None:
        if amplitude is not None:
            self.signal_amplitude = max(float(amplitude), 0.0)
        if frequency is not None:
            self.signal_frequency = max(float(frequency), 0.01)
        if offset is not None:
            self.signal_offset = float(offset)
        if secondary_frequency is not None:
            self.signal_frequency_2 = max(float(secondary_frequency), 0.01)
        if pulse_width is not None:
            self.pulse_width = min(max(float(pulse_width), 0.01), 0.95)
        if chirp_end_frequency is not None:
            self.chirp_end_frequency = max(float(chirp_end_frequency), self.signal_frequency)

    def set_loss_settings(
        self,
        *,
        source_resistance: float | None = None,
        inductor_series_resistance: float | None = None,
        capacitor_esr: float | None = None,
    ) -> None:
        if source_resistance is not None:
            self.source_resistance = max(float(source_resistance), 0.0)
        if inductor_series_resistance is not None:
            self.inductor_series_resistance = max(float(inductor_series_resistance), 0.0)
        if capacitor_esr is not None:
            self.capacitor_esr = max(float(capacitor_esr), 0.0)

    def set_simulation_parameters(self, inductance: float, capacitance: float, resistance: float, topology: str = "Manual") -> None:
        self.L = inductance
        self.C = capacitance
        self.R = resistance
        self.derived_parameters.update(
            L=inductance,
            C=capacitance,
            R=resistance,
            topology=topology,
            message=f"{topology} parameters ready for simulation.",
            is_valid=topology != "Manual",
        )

    def update_derived_parameters(self, interpretation: CircuitInterpretation) -> None:
        self.derived_parameters.update(
            L=interpretation.L if interpretation.is_valid else None,
            C=interpretation.C if interpretation.is_valid else None,
            R=interpretation.R if interpretation.is_valid else None,
            topology=interpretation.topology,
            message=interpretation.message,
            is_valid=interpretation.is_valid,
        )
        if interpretation.is_valid and interpretation.L is not None:
            self.L = interpretation.L
        if interpretation.is_valid and interpretation.C is not None:
            self.C = interpretation.C
        if interpretation.is_valid and interpretation.R is not None:
            self.R = interpretation.R

    def get_passive_components(self) -> list[ComponentModel]:
        order = {"Resistor": 0, "Inductor": 1, "Capacitor": 2}
        return sorted(
            [component for component in self.components.values() if component.component_type not in {"Source", "Node"}],
            key=lambda component: (order.get(component.component_type, 99), component.component_id),
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "L": self.L,
            "C": self.C,
            "R": self.R,
            "signal_type": self.signal_type,
            "signal_amplitude": self.signal_amplitude,
            "signal_frequency": self.signal_frequency,
            "signal_offset": self.signal_offset,
            "signal_frequency_2": self.signal_frequency_2,
            "pulse_width": self.pulse_width,
            "chirp_end_frequency": self.chirp_end_frequency,
            "source_resistance": self.source_resistance,
            "inductor_series_resistance": self.inductor_series_resistance,
            "capacitor_esr": self.capacitor_esr,
            "dt": self.dt,
            "duration": self.duration,
            "analysis_min_hz": self.analysis_min_hz,
            "analysis_max_hz": self.analysis_max_hz,
            "smoothing_window": self.smoothing_window,
            "components": [
                {
                    "component_id": component.component_id,
                    "component_type": component.component_type,
                    "display_name": component.display_name,
                    "value": component.value,
                    "x": component.x,
                    "y": component.y,
                    "lambda_": component.lambda_,
                    "category": component.category,
                    "shape": component.shape,
                    "metadata": component.metadata,
                    "parallel_children": component.parallel_children,
                }
                for component in self.components.values()
            ],
            "connections": [
                {
                    "connection_id": connection.connection_id,
                    "from_component": connection.from_component,
                    "from_terminal": connection.from_terminal,
                    "to_component": connection.to_component,
                    "to_terminal": connection.to_terminal,
                }
                for connection in self.connections.values()
            ],
            "derived_parameters": {
                "L": self.derived_parameters.L,
                "C": self.derived_parameters.C,
                "R": self.derived_parameters.R,
                "topology": self.derived_parameters.topology,
                "message": self.derived_parameters.message,
                "is_valid": self.derived_parameters.is_valid,
            },
            "component_counter": self._component_counter,
            "connection_counter": self._connection_counter,
        }

    def restore_snapshot(self, snapshot: dict[str, object]) -> None:
        self.selected_component_id = None
        self.selected_component_ids = []
        self.ctrl_multiselect_redirect = False
        self.L = float(snapshot["L"])
        self.C = float(snapshot["C"])
        self.R = float(snapshot["R"])
        self.signal_type = str(snapshot["signal_type"])
        self.signal_amplitude = float(snapshot.get("signal_amplitude", self.default_values["signal_amplitude"]))
        self.signal_frequency = float(snapshot.get("signal_frequency", self.default_values["signal_frequency"]))
        self.signal_offset = float(snapshot.get("signal_offset", self.default_values["signal_offset"]))
        self.signal_frequency_2 = float(snapshot.get("signal_frequency_2", self.default_values["signal_frequency_2"]))
        self.pulse_width = float(snapshot.get("pulse_width", self.default_values["pulse_width"]))
        self.chirp_end_frequency = float(snapshot.get("chirp_end_frequency", self.default_values["chirp_end_frequency"]))
        self.source_resistance = float(snapshot.get("source_resistance", self.default_values["source_resistance"]))
        self.inductor_series_resistance = float(snapshot.get("inductor_series_resistance", self.default_values["inductor_series_resistance"]))
        self.capacitor_esr = float(snapshot.get("capacitor_esr", self.default_values["capacitor_esr"]))
        self.dt = float(snapshot.get("dt", self.dt))
        self.duration = float(snapshot.get("duration", self.duration))
        self.analysis_min_hz = float(snapshot.get("analysis_min_hz", self.analysis_min_hz))
        self.analysis_max_hz = float(snapshot.get("analysis_max_hz", self.analysis_max_hz))
        self.smoothing_window = int(snapshot.get("smoothing_window", self.smoothing_window))
        self.time = np.arange(0.0, self.duration, self.dt)
        self.components = {}
        component_items = cast(list[dict[str, Any]], snapshot["components"])
        for item in component_items:
            component = ComponentModel(
                component_id=str(item["component_id"]),
                component_type=str(item["component_type"]),
                display_name=str(item.get("display_name", item["component_id"])),
                value=float(item["value"]),
                x=float(item["x"]),
                y=float(item["y"]),
                lambda_=_normalize_lambda(item.get("lambda_", _meta_for_component(str(item["component_type"])).get("lambda_default", 1.0e-5)), 1.0e-5),
                category=str(item.get("category", _meta_for_component(str(item["component_type"])).get("category", "Passive"))),
                shape=str(item.get("shape", _meta_for_component(str(item["component_type"])).get("shape", "rectangle"))),
                metadata=cast(dict[str, str], item.get("metadata", {})),
                parallel_children=_normalize_container_children(item.get("parallel_children", [])),
            )
            self.components[component.component_id] = component
        self.connections = {}
        connection_items = cast(list[dict[str, Any]], snapshot["connections"])
        for item in connection_items:
            connection = ConnectionModel(
                connection_id=str(item["connection_id"]),
                from_component=str(item["from_component"]),
                from_terminal=str(item["from_terminal"]),
                to_component=str(item["to_component"]),
                to_terminal=str(item["to_terminal"]),
            )
            self.connections[connection.connection_id] = connection
        derived = cast(dict[str, Any], snapshot["derived_parameters"])
        self.derived_parameters = DerivedParameters(
            L=float(derived["L"]) if derived["L"] is not None else None,
            C=float(derived["C"]) if derived["C"] is not None else None,
            R=float(derived["R"]) if derived["R"] is not None else None,
            topology=str(derived["topology"]),
            message=str(derived["message"]),
            is_valid=bool(derived["is_valid"]),
        )
        self._component_counter = int(snapshot["component_counter"])
        self._connection_counter = int(snapshot["connection_counter"])


class SignalGenerator:
    def __init__(self) -> None:
        self.rng = np.random.default_rng()

    def generate(self, mode: str, time_vector: np.ndarray, state: SystemState) -> np.ndarray:
        amplitude = max(state.signal_amplitude, 0.0)
        offset = state.signal_offset
        base_frequency = max(state.signal_frequency, 0.01)
        secondary_frequency = max(state.signal_frequency_2, base_frequency)
        if mode == "Noise":
            return offset + self.rng.normal(0.0, max(amplitude, 1e-6), len(time_vector))
        if mode == "Sine":
            return offset + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
        if mode == "Multi-Sine":
            return (
                offset
                + amplitude * np.sin(2.0 * np.pi * base_frequency * time_vector)
                + 0.65 * amplitude * np.sin(2.0 * np.pi * (base_frequency * 0.5) * time_vector + 0.3)
                + 0.35 * amplitude * np.sin(2.0 * np.pi * secondary_frequency * time_vector + 1.1)
            )
        if mode == "Step":
            step_time = time_vector[0] + max(time_vector[-1] - time_vector[0], 1e-9) * 0.08
            return offset + amplitude * (time_vector >= step_time).astype(float)
        if mode == "Square":
            return offset + amplitude * np.sign(np.sin(2.0 * np.pi * base_frequency * time_vector))
        if mode == "Pulse":
            period = max(1.0 / base_frequency, 1e-6)
            pulse_width = min(max(state.pulse_width, 0.01), 0.95)
            return offset + amplitude * (((time_vector % period) / period) <= pulse_width).astype(float)
        if mode == "Impulse":
            impulse = np.full(len(time_vector), offset, dtype=float)
            if len(impulse):
                impulse[0] = offset + amplitude / max(time_vector[1] - time_vector[0] if len(time_vector) > 1 else 1.0, 1e-6)
            return impulse
        if mode == "Chirp":
            sweep_rate = (max(state.chirp_end_frequency, base_frequency) - base_frequency) / max(time_vector[-1] - time_vector[0], 1e-6)
            phase = 2.0 * np.pi * (base_frequency * time_vector + 0.5 * sweep_rate * np.square(time_vector))
            return offset + amplitude * np.sin(phase)
        raise ValueError(f"Unsupported signal type: {mode}")


class SimulationEngine:
    def run(self, inductance: float, capacitance: float, resistance: float, excitation: np.ndarray, time_vector: np.ndarray, dt: float, state: SystemState) -> SimulationResult:
        charge = 0.0
        current = 0.0
        current_trace = np.zeros_like(time_vector)
        charge_trace = np.zeros_like(time_vector)
        resistor_voltage = np.zeros_like(time_vector)
        inductor_voltage = np.zeros_like(time_vector)
        capacitor_voltage = np.zeros_like(time_vector)
        inv_l = 1.0 / inductance
        inv_c = 1.0 / capacitance
        effective_resistance = resistance + state.source_resistance + state.inductor_series_resistance + state.capacitor_esr
        for index, source_voltage in enumerate(excitation):
            dqdt = current
            capacitor_drop = inv_c * charge
            resistive_drop = effective_resistance * current
            didt = inv_l * (source_voltage - resistive_drop - capacitor_drop)
            charge += dqdt * dt
            current += didt * dt
            current_trace[index] = current
            charge_trace[index] = charge
            resistor_voltage[index] = resistance * current
            capacitor_voltage[index] = capacitor_drop
            inductor_voltage[index] = source_voltage - resistor_voltage[index] - capacitor_voltage[index]
        return SimulationResult(
            time=time_vector,
            input_signal=excitation,
            current=current_trace,
            charge=charge_trace,
            component_voltages={
                "Resistor": resistor_voltage,
                "Inductor": inductor_voltage,
                "Capacitor": capacitor_voltage,
            },
            component_currents={
                "Circuit Current": current_trace.copy(),
                "Resistor": current_trace.copy(),
                "Inductor": current_trace.copy(),
                "Capacitor": current_trace.copy(),
            },
        )


class FFTProcessor:
    def compute_transfer_function(self, input_signal: np.ndarray, output_signal: np.ndarray, dt: float, smoothing_window: int) -> FrequencyResponse:
        window = np.hanning(len(input_signal))
        spectrum_in = np.fft.rfft(input_signal * window)
        spectrum_out = np.fft.rfft(output_signal * window)
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        transfer = np.zeros_like(spectrum_out, dtype=np.complex128)

        input_magnitude = np.abs(spectrum_in)
        excitation_threshold = max(np.max(input_magnitude) * 0.03, 1e-8)
        excited_mask = input_magnitude >= excitation_threshold
        transfer[excited_mask] = spectrum_out[excited_mask] / spectrum_in[excited_mask]

        magnitude = np.abs(transfer)
        phase = np.zeros_like(magnitude)
        phase[excited_mask] = np.unwrap(np.angle(transfer[excited_mask]))
        smoothed_magnitude = self._moving_average(magnitude, smoothing_window)
        return FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed_magnitude)

    @staticmethod
    def _moving_average(values: np.ndarray, window: int) -> np.ndarray:
        if window <= 1 or len(values) < window:
            return values.copy()
        return np.convolve(values, np.ones(window, dtype=float) / window, mode="same")


class GraphCircuitSolver:
    def solve_frequency_response(self, graph: CircuitGraph, frequency: np.ndarray, smoothing_window: int, state: SystemState) -> tuple[FrequencyResponse, GraphSolveResult] | None:
        if not graph.source_component_ids:
            return None
        source = next((component for component in graph.components if component.type == "Source"), None)
        if source is None:
            return None

        transfer = np.zeros(len(frequency), dtype=np.complex128)
        impedance = np.zeros(len(frequency), dtype=np.complex128)
        component_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        component_current_transfer = {
            component.id: np.zeros(len(frequency), dtype=np.complex128)
            for component in graph.components
            if component.type != "Source"
        }
        for index, freq_hz in enumerate(frequency):
            solution = self._solve_at_frequency(graph, source, float(freq_hz), state)
            if solution is None:
                return None
            transfer[index] = solution["source_current"]
            impedance[index] = np.inf if abs(solution["source_current"]) < 1e-12 else 1.0 / solution["source_current"]
            for component_id, value in solution["component_voltage"].items():
                component_transfer[component_id][index] = value
            for component_id, value in solution["component_current"].items():
                component_current_transfer[component_id][index] = value

        magnitude = np.abs(transfer)
        phase = np.unwrap(np.angle(transfer))
        smoothed = FFTProcessor._moving_average(magnitude, smoothing_window)
        response = FrequencyResponse(frequency=frequency, magnitude=magnitude, phase=phase, smoothed_magnitude=smoothed)
        return response, GraphSolveResult(
            frequency=frequency,
            transfer=transfer,
            impedance=impedance,
            component_transfer=component_transfer,
            component_current_transfer=component_current_transfer,
        )

    def simulate_signal(self, graph: CircuitGraph, input_signal: np.ndarray, time_vector: np.ndarray, dt: float, smoothing_window: int, state: SystemState) -> tuple[SimulationResult, FrequencyResponse, GraphSolveResult] | None:
        frequency = np.fft.rfftfreq(len(input_signal), dt)
        solved = self.solve_frequency_response(graph, frequency, smoothing_window, state)
        if solved is None:
            return None
        response, graph_result = solved
        input_spectrum = np.fft.rfft(input_signal)
        output_spectrum = graph_result.transfer * input_spectrum
        current = np.fft.irfft(output_spectrum, n=len(input_signal))
        component_voltages = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_transfer.items()
        }
        component_currents = {
            component_id: np.fft.irfft(transfer * input_spectrum, n=len(input_signal)).real
            for component_id, transfer in graph_result.component_current_transfer.items()
        }
        simulation = SimulationResult(
            time=time_vector,
            input_signal=input_signal,
            current=current.real,
            charge=np.cumsum(current.real) * dt,
            component_voltages=component_voltages,
            component_currents=component_currents,
        )
        return simulation, response, graph_result

    def _solve_at_frequency(self, graph: CircuitGraph, source: GraphComponent, frequency_hz: float, state: SystemState) -> dict[str, Any] | None:
        ground = source.node2
        nodes = sorted({node.id for node in graph.nodes if node.id != ground})
        node_index = {node_id: index for index, node_id in enumerate(nodes)}
        size = len(nodes) + 1
        matrix = np.zeros((size, size), dtype=np.complex128)
        vector = np.zeros(size, dtype=np.complex128)
        omega = 2.0 * math.pi * frequency_hz

        for component in graph.components:
            if component.type == "Source":
                continue
            admittance = self._component_admittance(component, omega, state)
            self._stamp_admittance(matrix, node_index, component.node1, component.node2, ground, admittance)

        # Small shunt conductance keeps open/floating AC edge cases numerically stable.
        for diagonal_index in range(len(nodes)):
            matrix[diagonal_index, diagonal_index] += 1e-9

        source_index = len(nodes)
        if source.node1 != ground:
            plus = node_index[source.node1]
            matrix[plus, source_index] += 1.0
            matrix[source_index, plus] += 1.0
        if source.node2 != ground:
            minus = node_index[source.node2]
            matrix[minus, source_index] -= 1.0
            matrix[source_index, minus] -= 1.0
        vector[source_index] = 1.0

        try:
            solution = np.linalg.solve(matrix, vector)
        except np.linalg.LinAlgError:
            return None
        node_voltage = {ground: 0.0 + 0.0j}
        for node_id, index in node_index.items():
            node_voltage[node_id] = solution[index]
        component_voltage: dict[str, complex] = {}
        component_current: dict[str, complex] = {}
        for component in graph.components:
            if component.type == "Source":
                continue
            voltage_drop = node_voltage.get(component.node1, 0.0 + 0.0j) - node_voltage.get(component.node2, 0.0 + 0.0j)
            admittance = self._component_admittance(component, omega, state)
            component_voltage[component.id] = voltage_drop
            component_current[component.id] = admittance * voltage_drop
        return {
            "source_current": -solution[source_index],
            "component_voltage": component_voltage,
            "component_current": component_current,
        }

    def _component_admittance(self, component: GraphComponent, omega: float, state: SystemState) -> complex:
        value = max(component.value, 1e-12)
        if component.type == "Resistor":
            return 1.0 / value
        if component.type == "Inductor":
            return 1.0 / complex(max(state.inductor_series_resistance, 1e-12), max(omega, 1e-12) * value)
        if component.type == "Capacitor":
            capacitive_reactance = -1.0 / (max(omega, 1e-9) * value)
            return 1.0 / complex(max(state.capacitor_esr, 1e-12), capacitive_reactance)
        return 0.0 + 0.0j

    def _stamp_admittance(
        self,
        matrix: np.ndarray,
        node_index: dict[str, int],
        node_a: str,
        node_b: str,
        ground: str,
        admittance: complex,
    ) -> None:
        index_a = node_index.get(node_a) if node_a != ground else None
        index_b = node_index.get(node_b) if node_b != ground else None
        if index_a is not None:
            matrix[index_a, index_a] += admittance
        if index_b is not None:
            matrix[index_b, index_b] += admittance
        if index_a is not None and index_b is not None:
            matrix[index_a, index_b] -= admittance
            matrix[index_b, index_a] -= admittance


class Analyzer:
    def analyze(self, state: SystemState, response: FrequencyResponse) -> tuple[np.ndarray, np.ndarray, np.ndarray, AnalysisSummary]:
        mask = (response.frequency >= state.analysis_min_hz) & (response.frequency <= state.analysis_max_hz)
        frequency = response.frequency[mask]
        magnitude = response.smoothed_magnitude[mask]
        phase = response.phase[mask]
        if len(frequency) == 0:
            frequency = response.frequency
            magnitude = response.smoothed_magnitude
            phase = response.phase
        peak_index = int(np.argmax(magnitude))
        resonance_hz = float(frequency[peak_index])
        peak_gain = float(magnitude[peak_index])
        damping_ratio = float("nan")
        half_power = peak_gain / math.sqrt(2.0)
        above_half = np.where(magnitude >= half_power)[0]
        quality_factor = 0.0
        if len(above_half) >= 2:
            bandwidth = float(frequency[above_half[-1]] - frequency[above_half[0]])
            quality_factor = resonance_hz / bandwidth if bandwidth > 0 else 0.0
        if (
            state.derived_parameters.L is not None
            and state.derived_parameters.C is not None
            and state.derived_parameters.R is not None
        ):
            damping_ratio = state.derived_parameters.R / 2.0 * math.sqrt(state.derived_parameters.C / state.derived_parameters.L)
            if damping_ratio < 0.999:
                system_type = "Underdamped"
            elif math.isclose(damping_ratio, 1.0, rel_tol=0.05):
                system_type = "Critically damped"
            else:
                system_type = "Overdamped"
        else:
            system_type = "Graph Network" if state.components else "Manual"
        return frequency, magnitude, phase, AnalysisSummary(resonance_hz, peak_gain, damping_ratio, system_type, quality_factor, peak_index)

    def analyze_transient(self, simulation: SimulationResult, output_trace: np.ndarray) -> TransientSummary:
        if len(output_trace) < 3:
            return TransientSummary(None, None, None, None)
        final_value = float(np.mean(output_trace[-max(len(output_trace) // 10, 1) :]))
        peak_index = int(np.argmax(np.abs(output_trace)))
        peak_time = float(simulation.time[peak_index])
        peak_value = float(output_trace[peak_index])
        reference = final_value if abs(final_value) > 1e-9 else peak_value
        rise_time = None
        if abs(reference) > 1e-9:
            lower = 0.1 * reference
            upper = 0.9 * reference
            lower_hits = np.where(output_trace >= lower)[0]
            upper_hits = np.where(output_trace >= upper)[0]
            if len(lower_hits) and len(upper_hits):
                rise_time = float(simulation.time[upper_hits[0]] - simulation.time[lower_hits[0]])
        tolerance = max(abs(reference) * 0.02, 1e-4)
        settling_time = None
        deviation = np.abs(output_trace - final_value)
        within = deviation <= tolerance
        for index in range(len(within)):
            if np.all(within[index:]):
                settling_time = float(simulation.time[index])
                break
        overshoot_pct = None
        if abs(reference) > 1e-9:
            overshoot_pct = max((peak_value - reference) / abs(reference) * 100.0, 0.0)
        return TransientSummary(rise_time, settling_time, overshoot_pct, peak_time)


class CircuitInterpreter:
    def interpret(self, state: SystemState) -> CircuitInterpretation:
        if not state.components:
            return CircuitInterpretation("Manual", "Add components to the builder workspace.", False, None, None, None)

        analysis = analyze_circuit(parse_system_state(state))
        if not analysis.is_valid:
            topology = analysis.topology_name if analysis.topology_name else ("Manual" if analysis.source_component_id is None else "Unresolved")
            return CircuitInterpretation(topology, analysis.message, False, None, None, None)

        if analysis.legacy_mode == "parallel":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )
        if analysis.legacy_mode == "series":
            return CircuitInterpretation(
                analysis.topology_name,
                analysis.message,
                True,
                float(analysis.equivalent_l) if analysis.equivalent_l is not None else None,
                float(analysis.equivalent_c) if analysis.equivalent_c is not None else None,
                float(analysis.equivalent_r) if analysis.equivalent_r is not None else None,
            )

        return CircuitInterpretation(
            "Graph Network",
            "Mixed topology detected. Graph-based nodal analysis is enabled for simulation and per-component traces.",
            False,
            None,
            None,
            None,
        )


class PlotManager:
    def __init__(self, parent: tk.Widget) -> None:
        self.figure = Figure(figsize=(10, 7), dpi=100, facecolor=THEME["panel"])
        self.ax_magnitude = self.figure.add_subplot(211)
        self.ax_phase = self.figure.add_subplot(212)
        self.figure.subplots_adjust(left=0.095, right=0.982, top=0.92, bottom=0.10, hspace=0.28)
        self._rebuild_plot_artists()

        self.frequency = np.array([])
        self.magnitude = np.array([])
        self.phase = np.array([])
        self.hover_callback = None
        self.hover_clear_callback = None
        self.bode_mode = False
        self.watermark = self.figure.text(
            0.995,
            0.01,
            "Powered by Mayank Jindal",
            ha="right",
            va="bottom",
            color=THEME["muted_soft"],
            fontsize=8,
            alpha=0.9,
        )

        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=THEME["panel"], highlightthickness=0, bd=0)
        widget.pack(fill="both", expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("axes_leave_event", self._clear_hover)

    def _rebuild_plot_artists(self) -> None:
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        self._style_axis(self.ax_magnitude, "Magnitude Response", "Gain")
        self._style_axis(self.ax_phase, "Phase Response", "Phase (rad)")
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        (self.magnitude_line,) = self.ax_magnitude.plot([], [], color=THEME["accent"], linewidth=2.4)
        (self.phase_line,) = self.ax_phase.plot([], [], color=THEME["secondary"], linewidth=2.2)
        (self.overlay_line,) = self.ax_magnitude.plot([], [], color=THEME["secondary"], linewidth=1.1, alpha=0.35)
        self.peak_marker = self.ax_magnitude.scatter([], [], s=72, color=THEME["secondary"], zorder=5)
        self.peak_label = self.ax_magnitude.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            color=THEME["text"],
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.35", "fc": THEME["card_inner"], "ec": THEME["border_soft"], "lw": 1},
        )

    def _style_axis(self, axis, title: str, ylabel: str) -> None:
        axis.set_facecolor(THEME["panel"])
        axis.set_title(title, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=14)
        axis.set_ylabel(ylabel, color=THEME["muted"], labelpad=8)
        axis.minorticks_on()
        axis.grid(True, which="major", color=THEME["grid"], alpha=0.8, linewidth=0.8)
        axis.grid(True, which="minor", color=THEME["grid_minor"], alpha=0.85, linewidth=0.45)
        axis.tick_params(colors=THEME["muted"], labelsize=9, which="major", length=5, width=0.9)
        axis.tick_params(colors=THEME["muted_soft"], labelsize=8, which="minor", length=3, width=0.6)
        for spine in axis.spines.values():
            spine.set_color(THEME["border"])
            spine.set_linewidth(1.0)

    def set_bode_mode(self, enabled: bool) -> None:
        self.bode_mode = enabled

    def reset_for_refresh(self) -> None:
        self._rebuild_plot_artists()
        self.frequency = np.array([])
        self.magnitude = np.array([])
        self.phase = np.array([])
        self.magnitude_line.set_data([], [])
        self.phase_line.set_data([], [])
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.canvas.draw_idle()


    def update(self, frequency: np.ndarray, magnitude: np.ndarray, phase: np.ndarray, summary: AnalysisSummary) -> None:
        if self.bode_mode:
            self.ax_magnitude.set_title("Bode Magnitude", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Bode Phase", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        else:
            self.ax_magnitude.set_title("Magnitude Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
            self.ax_phase.set_title("Phase Response", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Gain", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Phase (rad)", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)
        self.ax_magnitude.set_xscale("log" if self.bode_mode else "linear")
        self.ax_phase.set_xscale("log" if self.bode_mode else "linear")
        self.frequency = frequency
        self.magnitude = magnitude
        self.phase = phase
        self.magnitude_line.set_data(frequency, magnitude)
        self.phase_line.set_data(frequency, phase)
        self.overlay_line.set_data([], [])
        peak_x = frequency[summary.peak_index]
        peak_y = magnitude[summary.peak_index]
        self.peak_marker.set_offsets(np.array([[peak_x, peak_y]]))
        self.peak_marker.set_visible(True)
        self.peak_label.set_visible(True)
        self.peak_label.xy = (peak_x, peak_y)
        self.peak_label.set_text(f"Peak  {peak_x:.3f} Hz\nGain  {peak_y:.3f}")
        self.ax_magnitude.set_xlim(frequency[0], frequency[-1])
        self.ax_phase.set_xlim(frequency[0], frequency[-1])
        self.ax_magnitude.set_ylim(0.0, max(peak_y * 1.18, 0.5))
        phase_min = float(np.min(phase))
        phase_max = float(np.max(phase))
        padding = max((phase_max - phase_min) * 0.1, 0.2)
        self.ax_phase.set_ylim(phase_min - padding, phase_max + padding)
        self.canvas.draw_idle()

    def update_signal_view(self, simulation: SimulationResult, output_trace: np.ndarray, output_label: str) -> None:
        self.ax_magnitude.set_xscale("linear")
        self.ax_phase.set_xscale("linear")
        self.frequency = np.array([])
        self.magnitude = np.array([])
        self.phase = np.array([])

        samples = min(len(simulation.time), 2400)
        time_slice = simulation.time[:samples]
        input_slice = simulation.input_signal[:samples]
        output_slice = output_trace[:samples]

        self.ax_magnitude.set_title("Input Excitation", color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_phase.set_title(output_label, color=THEME["text"], fontsize=12, fontweight="bold", loc="left", pad=12)
        self.ax_magnitude.set_ylabel("Voltage", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_ylabel("Response", color=THEME["muted"], labelpad=8)
        self.ax_phase.set_xlabel("Time (s)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.tick_params(labelbottom=False)
        self.ax_phase.tick_params(labelbottom=True)

        self.magnitude_line.set_data(time_slice, input_slice)
        self.phase_line.set_data(time_slice, output_slice)
        self.overlay_line.set_data([], [])
        self.peak_marker.set_visible(False)
        self.peak_label.set_visible(False)

        self.ax_magnitude.set_xlim(time_slice[0], time_slice[-1])
        self.ax_phase.set_xlim(time_slice[0], time_slice[-1])

        input_pad = max(np.ptp(input_slice) * 0.1, 0.2)
        output_pad = max(np.ptp(output_slice) * 0.1, 0.2)
        self.ax_magnitude.set_ylim(float(np.min(input_slice) - input_pad), float(np.max(input_slice) + input_pad))
        self.ax_phase.set_ylim(float(np.min(output_slice) - output_pad), float(np.max(output_slice) + output_pad))
        self.canvas.draw_idle()

    def set_excitation_overlay(self, frequency: np.ndarray, excitation_spectrum: np.ndarray) -> None:
        if len(frequency) == 0 or len(excitation_spectrum) == 0:
            self.overlay_line.set_data([], [])
            return
        overlay = excitation_spectrum.copy()
        overlay_max = float(np.max(overlay))
        if overlay_max > 0:
            overlay = overlay / overlay_max
            overlay *= max(float(np.max(self.magnitude)) * 0.9, 1.0)
        self.overlay_line.set_data(frequency, overlay)

    def set_hover_callback(self, callback) -> None:
        self.hover_callback = callback

    def set_hover_clear_callback(self, callback) -> None:
        self.hover_clear_callback = callback

    def _on_hover(self, event) -> None:
        if event.inaxes not in (self.ax_magnitude, self.ax_phase) or len(self.frequency) == 0 or event.xdata is None:
            self._clear_hover()
            return
        index = int(np.argmin(np.abs(self.frequency - event.xdata)))
        if self.hover_callback is not None:
            self.hover_callback(float(self.frequency[index]), float(self.magnitude[index]), float(self.phase[index]))

    def _clear_hover(self, _event=None) -> None:
        if self.hover_clear_callback is not None:
            self.hover_clear_callback()

    def save_figure(self, path: str) -> None:
        if self.watermark is None:
            self.watermark = self.figure.text(
                0.995,
                0.01,
                "Powered by Mayank Jindal",
                ha="right",
                va="bottom",
                color=THEME["muted_soft"],
                fontsize=8,
                alpha=0.9,
            )
        self.figure.savefig(path, facecolor=self.figure.get_facecolor(), dpi=160, bbox_inches="tight")

    def show_unavailable(self, message: str) -> None:
        self._rebuild_plot_artists()
        self.ax_magnitude.clear()
        self.ax_phase.clear()
        for axis, title, ylabel in (
            (self.ax_magnitude, "Simulation Unavailable", "Gain"),
            (self.ax_phase, "Details", "Phase (rad)"),
        ):
            self._style_axis(axis, title, ylabel)
        self.ax_phase.set_xlabel("Frequency (Hz)", color=THEME["muted"], labelpad=8)
        self.ax_magnitude.text(0.5, 0.5, message, ha="center", va="center", color=THEME["muted"], transform=self.ax_magnitude.transAxes, wrap=True)
        self.ax_phase.text(0.5, 0.5, "Fix the circuit topology or complete the source-connected network.", ha="center", va="center", color=THEME["muted"], transform=self.ax_phase.transAxes, wrap=True)
        self.frequency = np.array([])
        self.magnitude = np.array([])
        self.phase = np.array([])
        self.canvas.draw_idle()


class ParameterCard(ttk.Frame):
    def __init__(self, parent: tk.Widget, label: str, unit: str, value_range: tuple[float, float], variable: tk.DoubleVar, command) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(12, 12))
        self.variable = variable
        self.unit = unit
        self.command = command
        self.value_range = value_range
        self.value_var = tk.StringVar()
        self.entry_var = tk.StringVar()

        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=label, style="CardTitle.TLabel").pack(side="left")
        ttk.Label(header, textvariable=self.value_var, style="Value.TLabel").pack(side="right")

        control_row = ttk.Frame(self, style="Card.TFrame")
        control_row.pack(fill="x", pady=(12, 4))
        control_row.grid_columnconfigure(0, weight=1)

        self.slider = ttk.Scale(control_row, from_=value_range[0], to=value_range[1], variable=variable, command=lambda _v: self._handle_slider(), style="Accent.Horizontal.TScale")
        self.slider.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        entry = ttk.Entry(control_row, textvariable=self.entry_var, style="Value.TEntry", justify="center", width=8)
        entry.grid(row=0, column=1, sticky="e")
        entry.bind("<Return>", self._handle_entry)
        entry.bind("<FocusOut>", self._handle_entry)

        footer = ttk.Frame(self, style="Card.TFrame")
        footer.pack(fill="x")
        ttk.Label(footer, text=f"{value_range[0]:.2f} {unit}", style="Hint.TLabel").pack(side="left")
        ttk.Label(footer, text=f"{value_range[1]:.2f} {unit}", style="Hint.TLabel").pack(side="right")
        self.refresh_value()

    def refresh_value(self) -> None:
        self.value_var.set(f"{self.variable.get():.3f} {self.unit}")
        self.entry_var.set(f"{self.variable.get():.3f}")

    def _handle_slider(self) -> None:
        self.refresh_value()
        self.command()

    def _handle_entry(self, _event=None) -> None:
        try:
            value = float(self.entry_var.get())
        except ValueError:
            self.refresh_value()
            return
        value = min(max(value, self.value_range[0]), self.value_range[1])
        self.variable.set(value)
        self.refresh_value()
        self.command()


class StatsCard(ttk.Frame):
    def __init__(self, parent: tk.Widget, title: str, unit: str = "") -> None:
        super().__init__(parent, style="Card.TFrame", padding=(12, 12))
        ttk.Label(self, text=title, style="CardTitle.TLabel").pack(anchor="w")
        row = ttk.Frame(self, style="Card.TFrame")
        row.pack(fill="x", pady=(8, 0))
        self.value_var = tk.StringVar(value="--")
        self.unit_var = tk.StringVar(value=unit)
        ttk.Label(row, textvariable=self.value_var, style="StatValue.TLabel").pack(side="left", anchor="s")
        ttk.Label(row, textvariable=self.unit_var, style="StatUnit.TLabel").pack(side="left", anchor="s", padx=(4, 0), pady=(7, 0))

    def set_value(self, value: str, unit: str | None = None) -> None:
        self.value_var.set(value)
        if unit is not None:
            self.unit_var.set(unit)


class StatusBar(ttk.Frame):
    def __init__(self, parent: tk.Widget) -> None:
        super().__init__(parent, style="Status.TFrame", padding=(12, 8))
        self.text_var = tk.StringVar(value="Ready | Powered by Mayank Jindal")
        ttk.Label(self, textvariable=self.text_var, style="Status.TLabel").pack(fill="x")

    def set_status(self, text: str) -> None:
        self.text_var.set(f"{text} | Powered by Mayank Jindal")


class AppHeader(ttk.Frame):
    def __init__(self, parent: tk.Widget, on_navigate) -> None:
        super().__init__(parent, style="Header.TFrame", padding=(18, 14))
        title_group = ttk.Frame(self, style="Header.TFrame")
        title_group.pack(side="left")
        ttk.Label(title_group, text="LCR Analyzer Pro", style="HeaderTitle.TLabel").pack(anchor="w")
        ttk.Label(title_group, text="Circuit design, simulation, and reliability analysis workspace", style="HeaderSub.TLabel").pack(anchor="w", pady=(2, 0))
        ttk.Label(title_group, text="Powered by Mayank Jindal", style="HeaderSub.TLabel").pack(anchor="w", pady=(1, 0))

        nav_shell = ttk.Frame(self, style="Card.TFrame", padding=(6, 6))
        nav_shell.pack(side="right")
        self.nav_var = tk.StringVar(value="builder")
        for page_name, label in (("builder", "Circuit Builder"), ("simulation", "Simulation"), ("inspector", "Component Inspector")):
            ttk.Radiobutton(
                nav_shell,
                text=label,
                value=page_name,
                variable=self.nav_var,
                command=lambda p=page_name: on_navigate(p),
                style="Nav.TRadiobutton",
            ).pack(side="left", padx=4)

    def set_active_page(self, page_name: str) -> None:
        self.nav_var.set(page_name)


class SimulationPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, signal_generator: SignalGenerator, simulation_engine: SimulationEngine, fft_processor: FFTProcessor, analyzer: Analyzer, on_parameters_changed, on_hover_status, on_restore_status) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.signal_generator = signal_generator
        self.simulation_engine = simulation_engine
        self.fft_processor = fft_processor
        self.analyzer = analyzer
        self.graph_solver = GraphCircuitSolver()
        self.on_parameters_changed = on_parameters_changed
        self.on_hover_status = on_hover_status
        self.on_restore_status = on_restore_status
        self.refresh_job: str | None = None
        self.component_vars: dict[str, tk.DoubleVar] = {}
        self.parameter_cards: list[ParameterCard] = []
        self.setting_cards: list[ParameterCard] = []
        self.view_var = tk.StringVar(value="Transfer Function")
        self.trace_var = tk.StringVar(value="Circuit Current")
        self.bode_enabled = False
        self.bode_button: ttk.Button | None = None
        self.latest_simulation: SimulationResult | None = None
        self.latest_response: FrequencyResponse | None = None
        self.latest_graph_result: GraphSolveResult | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=320)
        self.grid_columnconfigure(2, minsize=300)

        self._build_controls()
        self._build_graph_panel()
        self._build_metrics_panel()

    def _child_control_specs(
        self,
        component_id: str,
        children: list[dict[str, Any]],
        prefix_parts: list[str],
        path_parts: list[int],
    ) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        for index, child in enumerate(children):
            if not isinstance(child, dict):
                continue
            child_path = path_parts + [index]
            child_label = str(child.get("display_name") or child.get("type") or child.get("container_type") or f"Item {index + 1}")
            if "type" in child and "value" in child:
                child_type = str(child.get("type"))
                if child_type in {"Resistor", "Inductor", "Capacitor"}:
                    specs.append(
                        {
                            "key": f"{component_id}|child|{'.'.join(str(part) for part in child_path)}",
                            "label": " / ".join(prefix_parts + [child_label]),
                            "type": child_type,
                            "value": float(child.get("value", 0.0)),
                        }
                    )
                continue
            container_type = str(child.get("container_type", ""))
            nested_children = child.get("children")
            if container_type in {"ParallelContainer", "SeriesContainer"} and isinstance(nested_children, list):
                specs.extend(
                    self._child_control_specs(
                        component_id,
                        cast(list[dict[str, Any]], nested_children),
                        prefix_parts + [child_label],
                        child_path,
                    )
                )
        return specs

    def _control_specs(self) -> list[dict[str, Any]]:
        specs: list[dict[str, Any]] = []
        order = {"Resistor": 0, "Inductor": 1, "Capacitor": 2}
        for component in self.state.components.values():
            component_type = component.component_type
            if component_type in {"Source", "Node"}:
                continue
            if component_type in {"Resistor", "Inductor", "Capacitor"}:
                specs.append(
                    {
                        "key": component.component_id,
                        "label": component.display_name,
                        "type": component_type,
                        "value": float(component.value),
                    }
                )
            elif component_type in {"ParallelContainer", "SeriesContainer"}:
                specs.extend(
                    self._child_control_specs(
                        component.component_id,
                        cast(list[dict[str, Any]], component.parallel_children),
                        [component.display_name],
                        [],
                    )
                )
        return sorted(specs, key=lambda spec: (order.get(str(spec["type"]), 99), str(spec["label"])))

    def _build_controls(self) -> None:
        panel = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
        panel.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(2, weight=1)
        ttk.Label(panel, text="Simulation Controls", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            panel,
            text="Parameters are shared with the builder and can also be tuned directly here.",
            style="Body.TLabel",
            wraplength=250,
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))

        self.signal_var = tk.StringVar(value=self.state.signal_type)
        scroll_shell = ttk.Frame(panel, style="Panel.TFrame")
        scroll_shell.grid(row=2, column=0, sticky="nsew")
        scroll_shell.grid_rowconfigure(0, weight=1)
        scroll_shell.grid_columnconfigure(0, weight=1)
        self.controls_canvas = tk.Canvas(scroll_shell, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.controls_canvas.grid(row=0, column=0, sticky="nsew")
        controls_scrollbar = ttk.Scrollbar(scroll_shell, orient="vertical", command=self.controls_canvas.yview, style="Dark.Vertical.TScrollbar")
        controls_scrollbar.grid(row=0, column=1, sticky="ns")
        self.controls_canvas.configure(yscrollcommand=controls_scrollbar.set)
        self.controls_inner = ttk.Frame(self.controls_canvas, style="Panel.TFrame")
        self.controls_window_id = self.controls_canvas.create_window((0, 0), window=self.controls_inner, anchor="nw")
        self.controls_inner.bind("<Configure>", self._sync_controls_scrollregion)
        self.controls_canvas.bind("<Configure>", self._resize_controls_inner)
        self.controls_canvas.bind("<MouseWheel>", self._on_controls_mousewheel)
        self.controls_canvas.bind("<Button-4>", self._on_controls_mousewheel)
        self.controls_canvas.bind("<Button-5>", self._on_controls_mousewheel)
        self.controls_inner.bind("<MouseWheel>", self._on_controls_mousewheel)
        self.controls_inner.bind("<Button-4>", self._on_controls_mousewheel)
        self.controls_inner.bind("<Button-5>", self._on_controls_mousewheel)

        self.dynamic_controls_frame = ttk.Frame(self.controls_inner, style="Panel.TFrame")
        self.dynamic_controls_frame.pack(fill="x")

        signal_card = ttk.Frame(self.controls_inner, style="Card.TFrame", padding=(12, 12))
        signal_card.pack(fill="x", pady=(10, 10))
        ttk.Label(signal_card, text="Input Signal", style="CardTitle.TLabel").pack(anchor="w")
        combo = ttk.Combobox(signal_card, values=SIGNAL_OPTIONS, textvariable=self.signal_var, state="readonly", style="Signal.TCombobox")
        combo.pack(fill="x", pady=(10, 6))
        combo.bind("<<ComboboxSelected>>", lambda _e: self.request_refresh())
        ttk.Label(signal_card, text="Shared across simulation and builder workflows.", style="Hint.TLabel").pack(anchor="w")

        self.signal_setting_vars = {
            "amplitude": tk.DoubleVar(value=self.state.signal_amplitude),
            "frequency": tk.DoubleVar(value=self.state.signal_frequency),
            "offset": tk.DoubleVar(value=self.state.signal_offset),
            "secondary_frequency": tk.DoubleVar(value=self.state.signal_frequency_2),
            "pulse_width": tk.DoubleVar(value=self.state.pulse_width),
            "chirp_end_frequency": tk.DoubleVar(value=self.state.chirp_end_frequency),
        }
        signal_settings_card = ttk.Frame(self.controls_inner, style="Card.TFrame", padding=(12, 12))
        signal_settings_card.pack(fill="x", pady=(0, 10))
        ttk.Label(signal_settings_card, text="Signal Shaping", style="CardTitle.TLabel").pack(anchor="w")
        for key, label, unit, bounds in (
            ("amplitude", "Amplitude", "V", (0.0, 5.0)),
            ("frequency", "Base Frequency", "Hz", (0.05, 20.0)),
            ("secondary_frequency", "Blend / End Freq", "Hz", (0.10, 30.0)),
            ("offset", "DC Offset", "V", (-3.0, 3.0)),
            ("pulse_width", "Pulse Width", "", (0.01, 0.95)),
        ):
            card = ParameterCard(signal_settings_card, label, unit, bounds, self.signal_setting_vars[key], self.request_refresh)
            card.pack(fill="x", pady=(10, 0))
            self.setting_cards.append(card)

        loss_card = ttk.Frame(self.controls_inner, style="Card.TFrame", padding=(12, 12))
        loss_card.pack(fill="x", pady=(0, 10))
        ttk.Label(loss_card, text="Loss Model", style="CardTitle.TLabel").pack(anchor="w")
        self.loss_vars = {
            "source_resistance": tk.DoubleVar(value=self.state.source_resistance),
            "inductor_series_resistance": tk.DoubleVar(value=self.state.inductor_series_resistance),
            "capacitor_esr": tk.DoubleVar(value=self.state.capacitor_esr),
        }
        for key, label in (
            ("source_resistance", "Source Resistance"),
            ("inductor_series_resistance", "Inductor Series R"),
            ("capacitor_esr", "Capacitor ESR"),
        ):
            card = ParameterCard(loss_card, label, "Ohm", (0.0, 2.0), self.loss_vars[key], self.request_refresh)
            card.pack(fill="x", pady=(10, 0))
            self.setting_cards.append(card)

        source_card = ttk.Frame(self.controls_inner, style="Card.TFrame", padding=(12, 12))
        source_card.pack(fill="x", pady=(0, 10))
        ttk.Label(source_card, text="Parameter Source", style="CardTitle.TLabel").pack(anchor="w")
        self.source_var = tk.StringVar(value="Manual")
        ttk.Label(source_card, textvariable=self.source_var, style="StatValue.TLabel").pack(anchor="w", pady=(8, 0))
        ttk.Label(source_card, text="Response Trace", style="Hint.TLabel").pack(anchor="w", pady=(10, 4))
        self.trace_combo = ttk.Combobox(source_card, values=["Circuit Current"], textvariable=self.trace_var, state="readonly", style="Signal.TCombobox")
        self.trace_combo.pack(fill="x")
        self.trace_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_now())

        action_card = ttk.Frame(self.controls_inner, style="Card.TFrame", padding=(12, 12))
        action_card.pack(fill="x", pady=(2, 0))
        ttk.Label(action_card, text="Actions", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(action_card, text="Quick utilities for resetting controls or exporting the current view.", style="Hint.TLabel", wraplength=240, justify="left").pack(anchor="w", pady=(6, 10))
        action_grid = ttk.Frame(action_card, style="Card.TFrame")
        action_grid.pack(fill="x")
        action_grid.grid_columnconfigure(0, weight=1)
        action_grid.grid_columnconfigure(1, weight=1)
        ttk.Button(action_grid, text="Reset", style="Secondary.TButton", command=self.reset_controls).grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
        ttk.Button(action_grid, text="Save Plot", style="Secondary.TButton", command=self.save_plot).grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=(0, 6))
        ttk.Button(action_grid, text="Refresh", style="Secondary.TButton", command=self.force_refresh).grid(row=1, column=0, sticky="ew", padx=(0, 6))
        self.bode_button = ttk.Button(action_grid, text="Bode Plot", style="Secondary.TButton", command=self.toggle_bode_plot)
        self.bode_button.grid(row=1, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(action_grid, text="Export CSV", style="Secondary.TButton", command=self.export_csv).grid(row=2, column=0, sticky="ew", padx=(0, 6), pady=(6, 0))
        ttk.Button(action_grid, text="Center Trace", style="Secondary.TButton", command=self._refresh_now).grid(row=2, column=1, sticky="ew", padx=(6, 0), pady=(6, 0))
        self._sync_bode_button()
        self.rebuild_component_controls()

    def _sync_controls_scrollregion(self, _event=None) -> None:
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def _resize_controls_inner(self, event) -> None:
        self.controls_canvas.itemconfigure(self.controls_window_id, width=event.width)

    def _on_controls_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            step = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) == 4:
            step = -1
        else:
            step = 1
        self.controls_canvas.yview_scroll(step, "units")
        return "break"

    def _on_metrics_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            step = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) == 4:
            step = -1
        else:
            step = 1
        self.metrics_canvas.yview_scroll(step, "units")
        return "break"

    def _build_graph_panel(self) -> None:
        panel = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        header = ttk.Frame(panel, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)
        ttk.Label(header, text="Frequency Response", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        view_switch = ttk.Frame(header, style="Panel.TFrame")
        view_switch.grid(row=0, column=1, sticky="e")
        ttk.Label(view_switch, text="View", style="Body.TLabel").pack(side="left", padx=(0, 8))
        view_combo = ttk.Combobox(
            view_switch,
            values=["Transfer Function", "Signal Response"],
            textvariable=self.view_var,
            state="readonly",
            style="Signal.TCombobox",
            width=17,
        )
        view_combo.pack(side="left")
        view_combo.bind("<<ComboboxSelected>>", lambda _e: self._refresh_now())

        plot_card = ttk.Frame(panel, style="Card.TFrame", padding=(8, 8))
        plot_card.grid(row=1, column=0, sticky="nsew")
        plot_card.grid_rowconfigure(0, weight=1)
        plot_card.grid_columnconfigure(0, weight=1)
        self.plot_manager = PlotManager(plot_card)
        self.plot_manager.set_hover_callback(self._handle_hover)
        self.plot_manager.set_hover_clear_callback(self.on_restore_status)

    def _build_metrics_panel(self) -> None:
        panel = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
        panel.grid(row=0, column=2, sticky="nsew", padx=(12, 0))
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)
        ttk.Label(panel, text="System Metrics", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(panel, text="Live characteristics extracted from the active transfer function.", style="Body.TLabel", wraplength=240).grid(row=0, column=0, sticky="sw", pady=(26, 14))
        shell = ttk.Frame(panel, style="Panel.TFrame")
        shell.grid(row=1, column=0, sticky="nsew")
        shell.grid_rowconfigure(0, weight=1)
        shell.grid_columnconfigure(0, weight=1)
        self.metrics_canvas = tk.Canvas(shell, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.metrics_canvas.grid(row=0, column=0, sticky="nsew")
        metrics_scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self.metrics_canvas.yview, style="Dark.Vertical.TScrollbar")
        metrics_scrollbar.grid(row=0, column=1, sticky="ns")
        self.metrics_canvas.configure(yscrollcommand=metrics_scrollbar.set)
        self.metrics_inner = ttk.Frame(self.metrics_canvas, style="Panel.TFrame")
        self.metrics_window_id = self.metrics_canvas.create_window((0, 0), window=self.metrics_inner, anchor="nw")
        self.metrics_inner.bind("<Configure>", lambda _e: self.metrics_canvas.configure(scrollregion=self.metrics_canvas.bbox("all")))
        self.metrics_canvas.bind("<Configure>", lambda e: self.metrics_canvas.itemconfigure(self.metrics_window_id, width=e.width))
        self.metrics_canvas.bind("<MouseWheel>", self._on_metrics_mousewheel)
        self.metrics_canvas.bind("<Button-4>", self._on_metrics_mousewheel)
        self.metrics_canvas.bind("<Button-5>", self._on_metrics_mousewheel)
        self.metrics_inner.bind("<MouseWheel>", self._on_metrics_mousewheel)
        self.metrics_inner.bind("<Button-4>", self._on_metrics_mousewheel)
        self.metrics_inner.bind("<Button-5>", self._on_metrics_mousewheel)
        self.stats_cards = {
            "resonance": StatsCard(self.metrics_inner, "Resonance Frequency", "Hz"),
            "peak": StatsCard(self.metrics_inner, "Peak Gain"),
            "q": StatsCard(self.metrics_inner, "Quality Factor"),
            "damping": StatsCard(self.metrics_inner, "Damping Ratio"),
            "type": StatsCard(self.metrics_inner, "System Type"),
            "rise": StatsCard(self.metrics_inner, "Rise Time", "s"),
            "settling": StatsCard(self.metrics_inner, "Settling Time", "s"),
            "overshoot": StatsCard(self.metrics_inner, "Overshoot", "%"),
            "peak_time": StatsCard(self.metrics_inner, "Peak Time", "s"),
        }
        for card in self.stats_cards.values():
            card.pack(fill="x", pady=(0, 10))

    def sync_from_state(self) -> None:
        self.rebuild_component_controls()
        self.signal_var.set(self.state.signal_type)
        self.source_var.set(self.state.derived_parameters.topology)
        self.signal_setting_vars["amplitude"].set(self.state.signal_amplitude)
        self.signal_setting_vars["frequency"].set(self.state.signal_frequency)
        self.signal_setting_vars["offset"].set(self.state.signal_offset)
        self.signal_setting_vars["secondary_frequency"].set(self.state.signal_frequency_2)
        self.signal_setting_vars["pulse_width"].set(self.state.pulse_width)
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.chirp_end_frequency)
        self.loss_vars["source_resistance"].set(self.state.source_resistance)
        self.loss_vars["inductor_series_resistance"].set(self.state.inductor_series_resistance)
        self.loss_vars["capacitor_esr"].set(self.state.capacitor_esr)
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def request_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
        self.refresh_job = self.after(80, self.refresh)

    def _refresh_now(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.refresh()

    def refresh(self) -> None:
        self.refresh_job = None
        self.state.set_signal_type(self.signal_var.get())
        self.state.set_signal_settings(
            amplitude=float(self.signal_setting_vars["amplitude"].get()),
            frequency=float(self.signal_setting_vars["frequency"].get()),
            offset=float(self.signal_setting_vars["offset"].get()),
            secondary_frequency=float(self.signal_setting_vars["secondary_frequency"].get()),
            pulse_width=float(self.signal_setting_vars["pulse_width"].get()),
            chirp_end_frequency=float(self.signal_setting_vars["chirp_end_frequency"].get()),
        )
        self.state.set_loss_settings(
            source_resistance=float(self.loss_vars["source_resistance"].get()),
            inductor_series_resistance=float(self.loss_vars["inductor_series_resistance"].get()),
            capacitor_esr=float(self.loss_vars["capacitor_esr"].get()),
        )
        for control_key, variable in self.component_vars.items():
            self.state.update_control_value(control_key, float(variable.get()))
        interpretation = CircuitInterpreter().interpret(self.state)
        self.state.update_derived_parameters(interpretation)
        graph = parse_system_state(self.state)
        graph_analysis = analyze_circuit(graph) if self.state.components else None
        if (
            self.state.derived_parameters.is_valid
            and self.state.derived_parameters.L is not None
            and self.state.derived_parameters.C is not None
            and self.state.derived_parameters.R is not None
        ):
            topology = self.state.derived_parameters.topology
            self.state.set_simulation_parameters(
                float(self.state.derived_parameters.L),
                float(self.state.derived_parameters.C),
                float(self.state.derived_parameters.R),
                topology=topology,
            )
        self.source_var.set(self.state.derived_parameters.topology)
        self.on_parameters_changed()

        excitation = self.signal_generator.generate(self.state.signal_type, self.state.time, self.state)
        graph_solution = None
        can_run_manual = (
            self.state.derived_parameters.is_valid
            and self.state.derived_parameters.L is not None
            and self.state.derived_parameters.C is not None
            and self.state.derived_parameters.R is not None
        )
        if graph_analysis is not None and graph_analysis.is_valid and graph_analysis.source_component_id is not None:
            graph_solution = self.graph_solver.simulate_signal(graph, excitation, self.state.time, self.state.dt, self.state.smoothing_window, self.state)

        if self.state.components and graph_solution is None and graph_analysis is not None and not can_run_manual:
            self.source_var.set(graph_analysis.topology_name)
            self.plot_manager.show_unavailable(graph_analysis.message if not graph_analysis.is_valid else "The graph solver could not solve this circuit.")
            self.stats_cards["resonance"].set_value("--", "Hz")
            self.stats_cards["peak"].set_value("--")
            self.stats_cards["q"].set_value("--")
            self.stats_cards["damping"].set_value("--")
            self.stats_cards["type"].set_value("Unavailable")
            for key in ("rise", "settling", "overshoot", "peak_time"):
                self.stats_cards[key].set_value("--")
            self.on_restore_status()
            return

        if graph_solution is not None:
            simulation, response, graph_result = graph_solution
        else:
            simulation = self.simulation_engine.run(
                self.state.L,
                self.state.C,
                self.state.R,
                excitation,
                self.state.time,
                self.state.dt,
                self.state,
            )
            response = self.fft_processor.compute_transfer_function(simulation.input_signal, simulation.current, self.state.dt, self.state.smoothing_window)
            graph_result = None

        self.latest_simulation = simulation
        self.latest_response = response
        self.latest_graph_result = graph_result
        trace_label, trace_values = self._selected_trace(simulation)
        transient = self.analyzer.analyze_transient(simulation, trace_values)
        frequency, magnitude, phase, summary = self.analyzer.analyze(self.state, response)
        if self.view_var.get() == "Signal Response":
            self.plot_manager.set_bode_mode(False)
            self.plot_manager.update_signal_view(simulation, trace_values, trace_label)
        else:
            self.plot_manager.set_bode_mode(self.bode_enabled)
            self.plot_manager.update(frequency, magnitude, phase, summary)
            input_spectrum = np.abs(np.fft.rfft(simulation.input_signal * np.hanning(len(simulation.input_signal))))
            mask = (response.frequency >= self.state.analysis_min_hz) & (response.frequency <= self.state.analysis_max_hz)
            self.plot_manager.set_excitation_overlay(response.frequency[mask], input_spectrum[mask])
        self.stats_cards["resonance"].set_value(f"{summary.resonance_hz:.3f}", "Hz")
        self.stats_cards["peak"].set_value(f"{summary.peak_gain:.3f}")
        self.stats_cards["q"].set_value(f"{summary.quality_factor:.3f}")
        self.stats_cards["damping"].set_value("--" if math.isnan(summary.damping_ratio) else f"{summary.damping_ratio:.3f}")
        self.stats_cards["type"].set_value(summary.system_type)
        self.stats_cards["rise"].set_value("--" if transient.rise_time is None else f"{transient.rise_time:.4f}", "s")
        self.stats_cards["settling"].set_value("--" if transient.settling_time is None else f"{transient.settling_time:.4f}", "s")
        self.stats_cards["overshoot"].set_value("--" if transient.overshoot_pct is None else f"{transient.overshoot_pct:.2f}", "%")
        self.stats_cards["peak_time"].set_value("--" if transient.peak_time is None else f"{transient.peak_time:.4f}", "s")
        self.on_restore_status()

    def _handle_hover(self, frequency: float, magnitude: float, phase: float) -> None:
        parts = [
            f"Inspecting  {frequency:.3f} Hz",
            f"Magnitude  {magnitude:.3f}",
            f"Phase  {phase:.3f} rad",
            f"Trace  {self.trace_var.get()}",
        ]
        if self.state.derived_parameters.L is not None:
            parts.append(f"L={self.state.derived_parameters.L:.3f} H")
        if self.state.derived_parameters.C is not None:
            parts.append(f"C={self.state.derived_parameters.C:.3f} F")
        if self.state.derived_parameters.R is not None:
            parts.append(f"R={self.state.derived_parameters.R:.3f} Ohm")
        self.on_hover_status(" | ".join(parts))

    def _trace_options_for_simulation(self, simulation: SimulationResult) -> list[str]:
        options = ["Circuit Current"]
        options.extend(f"{name} Voltage" for name in sorted(simulation.component_voltages))
        options.extend(f"{name} Current" for name in sorted(simulation.component_currents) if name != "Circuit Current")
        return options

    def _selected_trace(self, simulation: SimulationResult) -> tuple[str, np.ndarray]:
        options = self._trace_options_for_simulation(simulation)
        self.trace_combo.configure(values=options)
        if self.trace_var.get() not in options:
            self.trace_var.set(options[0])
        trace_name = self.trace_var.get()
        if trace_name == "Circuit Current":
            return trace_name, simulation.current
        if trace_name.endswith(" Voltage"):
            component_name = trace_name[: -len(" Voltage")]
            for component_id, values in simulation.component_voltages.items():
                if component_id == component_name:
                    return trace_name, values
                component = self.state.components.get(component_id)
                if component is not None and component.display_name == component_name:
                    return trace_name, values
        if trace_name.endswith(" Current"):
            component_name = trace_name[: -len(" Current")]
            for component_id, values in simulation.component_currents.items():
                if component_id == component_name:
                    return trace_name, values
                component = self.state.components.get(component_id)
                if component is not None and component.display_name == component_name:
                    return trace_name, values
        return "Circuit Current", simulation.current

    def rebuild_component_controls(self) -> None:
        for child in self.dynamic_controls_frame.winfo_children():
            child.destroy()
        self.component_vars.clear()
        self.parameter_cards.clear()

        controls = self._control_specs()
        if not controls:
            empty_card = ttk.Frame(self.dynamic_controls_frame, style="Card.TFrame", padding=(12, 12))
            empty_card.pack(fill="x", pady=(0, 10))
            ttk.Label(empty_card, text="No Passive Components", style="CardTitle.TLabel").pack(anchor="w")
            ttk.Label(empty_card, text="Add resistor, inductor, or capacitor parts in Circuit Builder to expose controls here.", style="Body.TLabel", wraplength=240).pack(anchor="w", pady=(8, 0))
            return

        for control in controls:
            component_type = str(control["type"])
            label = str(control["label"])
            variable = tk.DoubleVar(value=float(control["value"]))
            self.component_vars[str(control["key"])] = variable
            value_range = self._range_for_component(component_type)
            card = ParameterCard(
                self.dynamic_controls_frame,
                label,
                COMPONENT_META[component_type]["unit"],
                value_range,
                variable,
                self.request_refresh,
            )
            card.pack(fill="x", pady=(0, 10))
            self.parameter_cards.append(card)

    @staticmethod
    def _range_for_component(component_type: str) -> tuple[float, float]:
        if component_type == "Inductor":
            return (0.10, 5.00)
        if component_type == "Capacitor":
            return (0.01, 1.00)
        return (0.10, 5.00)

    def reset_controls(self) -> None:
        for control in self._control_specs():
            control_key = str(control["key"])
            control_type = str(control["type"])
            if control_key in self.component_vars:
                self.component_vars[control_key].set(COMPONENT_META[control_type]["default"])
        self.signal_var.set(self.state.default_values["signal_type"])
        self.signal_setting_vars["amplitude"].set(self.state.default_values["signal_amplitude"])
        self.signal_setting_vars["frequency"].set(self.state.default_values["signal_frequency"])
        self.signal_setting_vars["offset"].set(self.state.default_values["signal_offset"])
        self.signal_setting_vars["secondary_frequency"].set(self.state.default_values["signal_frequency_2"])
        self.signal_setting_vars["pulse_width"].set(self.state.default_values["pulse_width"])
        self.signal_setting_vars["chirp_end_frequency"].set(self.state.default_values["chirp_end_frequency"])
        self.loss_vars["source_resistance"].set(self.state.default_values["source_resistance"])
        self.loss_vars["inductor_series_resistance"].set(self.state.default_values["inductor_series_resistance"])
        self.loss_vars["capacitor_esr"].set(self.state.default_values["capacitor_esr"])
        self.trace_var.set("Circuit Current")
        for card in self.setting_cards + self.parameter_cards:
            card.refresh_value()
        self.request_refresh()

    def _sync_bode_button(self) -> None:
        if self.bode_button is None:
            return
        self.bode_button.configure(style="SecondaryActive.TButton" if self.bode_enabled else "Secondary.TButton")

    def force_refresh(self) -> None:
        if self.refresh_job is not None:
            self.after_cancel(self.refresh_job)
            self.refresh_job = None
        self.stats_cards["resonance"].set_value("0.000", "Hz")
        self.stats_cards["peak"].set_value("0.000")
        self.stats_cards["q"].set_value("0.000")
        self.stats_cards["damping"].set_value("0.000")
        self.stats_cards["type"].set_value("Refreshing")
        self.stats_cards["rise"].set_value("0.000", "s")
        self.stats_cards["settling"].set_value("0.000", "s")
        self.stats_cards["overshoot"].set_value("0.000", "%")
        self.stats_cards["peak_time"].set_value("0.000", "s")
        self.plot_manager.reset_for_refresh()
        self.plot_manager.set_bode_mode(self.bode_enabled)
        self._sync_bode_button()
        self.update_idletasks()
        self._refresh_now()

    def toggle_bode_plot(self) -> None:
        self.bode_enabled = not self.bode_enabled
        self.view_var.set("Transfer Function")
        self.force_refresh()

    def save_plot(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Simulation Plot",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
        )
        if not path:
            return
        self.plot_manager.save_figure(path)
        self.on_hover_status(f"Plot saved to {path}")

    def export_csv(self) -> None:
        if self.latest_simulation is None or self.latest_response is None:
            return
        path = filedialog.asksaveasfilename(
            title="Export Simulation Data",
            defaultextension=".csv",
            filetypes=[("CSV File", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return
        trace_label, trace_values = self._selected_trace(self.latest_simulation)
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time_s", "input_signal", trace_label.replace(" ", "_").lower()])
            for time_value, input_value, output_value in zip(self.latest_simulation.time, self.latest_simulation.input_signal, trace_values):
                writer.writerow([f"{time_value:.8f}", f"{input_value:.8f}", f"{output_value:.8f}"])
            writer.writerow([])
            writer.writerow(["frequency_hz", "magnitude", "phase_rad"])
            for frequency, magnitude, phase in zip(self.latest_response.frequency, self.latest_response.smoothed_magnitude, self.latest_response.phase):
                writer.writerow([f"{frequency:.8f}", f"{magnitude:.8f}", f"{phase:.8f}"])
        self.on_hover_status(f"Simulation data exported to {path}")


class CircuitCanvas(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_state_changed, on_status_changed, on_selection_changed=None) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(8, 8))
        self.state = state
        self.on_state_changed = on_state_changed
        self.on_status_changed = on_status_changed
        self.on_selection_changed = on_selection_changed
        self.canvas = tk.Canvas(self, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.canvas.pack(fill="both", expand=True)

        self.mode = "Select"
        self.selected_component_id: str | None = None
        self.selected_connection_id: str | None = None
        self.drag_component_id: str | None = None
        self.drag_offset = (0.0, 0.0)
        self.pending_connection: tuple[str, str] | None = None
        self.preview_line: int | None = None
        self.palette_drag_type: str | None = None
        self.palette_drag_position: tuple[float, float] | None = None
        self.animated_component_id: str | None = None
        self.animation_step = 0
        self.animation_job: str | None = None
        self.hover_terminal: tuple[str, str] | None = None
        self.hover_component_id: str | None = None
        self.show_grid = True
        self.snap_to_grid = True
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.pan_origin: tuple[float, float] | None = None
        self.pan_start: tuple[float, float] | None = None
        self.selection_box_start: tuple[float, float] | None = None
        self.selection_box_current: tuple[float, float] | None = None
        self.selection_box_active = False
        self.selected_component_ids: list[str] = []
        self._ctrl_selection_action = False
        self._pending_initial_center = True
        self.icon_assets: dict[str, Any] = self._load_component_icons()
        self.icon_cache: dict[tuple[str, int, int], Any] = {}
        self._terminal_polarity: dict[str, str] = {}
        self._shorted_power_components: set[str] = set()
        self.workspace_bg_source = self._load_workspace_background_source()
        self.workspace_bg_cache: dict[tuple[int, int], Any] = {}
        self.workspace_bg_photo: Any = None

        self.canvas.bind("<Configure>", lambda _e: self.redraw())
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_press)
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonRelease-3>", self._on_pan_release)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Shift-MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)
        self.canvas.bind("<Delete>", self._delete_selected)
        self.canvas.bind("<BackSpace>", self._delete_selected)
        self.canvas.focus_set()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.pending_connection = None
        self._clear_preview()
        self.on_status_changed(f"Builder mode: {mode}")
        self.redraw()

    def begin_palette_drop(self, component_type: str, root_x: int, root_y: int) -> None:
        self.palette_drag_type = component_type
        self.update_palette_drop(root_x, root_y)
        self.winfo_toplevel().configure(cursor="crosshair")
        self.on_status_changed(f"Drop {component_type} into the workspace.")

    def update_palette_drop(self, root_x: int, root_y: int) -> None:
        if self.palette_drag_type is not None:
            canvas_x = self.canvas.winfo_rootx()
            canvas_y = self.canvas.winfo_rooty()
            if canvas_x <= root_x <= canvas_x + self.canvas.winfo_width() and canvas_y <= root_y <= canvas_y + self.canvas.winfo_height():
                world_x, world_y = self._screen_to_world(root_x - canvas_x, root_y - canvas_y)
                self.palette_drag_position = (self._snap(world_x), self._snap(world_y))
            else:
                self.palette_drag_position = None
            self.on_status_changed(f"Dragging {self.palette_drag_type}")
            self.redraw()

    def finish_palette_drop(self, root_x: int, root_y: int) -> None:
        if self.palette_drag_type is None:
            return
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        if canvas_x <= root_x <= canvas_x + self.canvas.winfo_width() and canvas_y <= root_y <= canvas_y + self.canvas.winfo_height():
            world_x, world_y = self._screen_to_world(root_x - canvas_x, root_y - canvas_y)
            local_x = self._snap(world_x)
            local_y = self._snap(world_y)
            target_info = self._container_target_at_screen(root_x - canvas_x, root_y - canvas_y)
            target_component = None if target_info is None else self.state.components.get(target_info[0])
            dropped_into_container = False
            if target_component is not None and self.palette_drag_type in {"Resistor", "Inductor", "Capacitor", "ParallelContainer", "SeriesContainer"}:
                if self.palette_drag_type in {"ParallelContainer", "SeriesContainer"}:
                    child_spec = {
                        "container_type": self.palette_drag_type,
                        "display_name": self.state.next_component_id(self.palette_drag_type),
                        "children": [],
                    }
                    self.state._component_counter -= 1
                else:
                    meta = _meta_for_component(self.palette_drag_type)
                    child_spec = {
                        "type": self.palette_drag_type,
                        "value": COMPONENT_META[self.palette_drag_type]["default"],
                        "lambda_": float(meta.get("lambda_default", 1.0e-5)),
                        "category": str(meta.get("category", "Passive")),
                        "shape": str(meta.get("shape", "rectangle")),
                        "metadata": {},
                    }
                dropped_into_container = self.state.add_child_spec_to_container(
                    target_component.component_id,
                    child_spec,
                    [] if target_info is None else target_info[1],
                )
            if dropped_into_container and target_component is not None:
                self.selected_component_id = target_component.component_id
                self._emit_selection()
                self.on_state_changed()
                self._start_animation(target_component.component_id)
            else:
                component = self.state.add_component(self.palette_drag_type, local_x, local_y)
                self.selected_component_id = component.component_id
                self._emit_selection()
                self.on_state_changed()
                self._start_animation(component.component_id)
        self.palette_drag_type = None
        self.palette_drag_position = None
        self.winfo_toplevel().configure(cursor="")
        self.redraw()

    def redraw(self) -> None:
        if self._pending_initial_center and self.state.components:
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            if width > 64 and height > 64:
                self._pending_initial_center = False
                self.center_view()
                return
        self.canvas.delete("all")
        self._draw_workspace_background()
        self._draw_grid()
        self._draw_node_labels()
        self._draw_connections()
        self._draw_components()
        self._draw_palette_preview()
        self._draw_selection_box()

    def _load_workspace_background_source(self):
        if Image is None:
            return None
        bg_path = Path(__file__).resolve().parent / "assets" / "backgrounds" / "workspace_bg.png"
        if not bg_path.exists():
            return None
        try:
            return Image.open(bg_path).convert("RGBA")
        except Exception:
            return None

    def _draw_workspace_background(self) -> None:
        if Image is None or ImageTk is None or self.workspace_bg_source is None:
            return
        width = max(int(self.canvas.winfo_width()), 1)
        height = max(int(self.canvas.winfo_height()), 1)
        key = (width, height)
        photo = self.workspace_bg_cache.get(key)
        if photo is None:
            resized = self.workspace_bg_source.resize((width, height), Image.LANCZOS)
            photo = ImageTk.PhotoImage(resized)
            self.workspace_bg_cache[key] = photo
        self.workspace_bg_photo = photo
        self.canvas.create_image(0, 0, image=photo, anchor="nw", tags=("workspace_bg",))

    def _draw_grid(self) -> None:
        if not self.show_grid:
            return
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        scaled_grid = max(GRID_SIZE * self.view_scale, 10)
        start_x = self.pan_x % scaled_grid
        start_y = self.pan_y % scaled_grid
        for x in np.arange(start_x, width, scaled_grid):
            self.canvas.create_line(x, 0, x, height, fill=THEME["builder_grid"], width=0.3)
        for y in np.arange(start_y, height, scaled_grid):
            self.canvas.create_line(0, y, width, y, fill=THEME["builder_grid"], width=0.3)

    def _draw_connections(self) -> None:
        self._terminal_polarity, self._shorted_power_components = self._compute_terminal_polarity()
        for connection in self.state.connections.values():
            start = self._terminal_position(connection.from_component, connection.from_terminal)
            end = self._terminal_position(connection.to_component, connection.to_terminal)
            width = 2.6 if connection.connection_id == self.selected_connection_id else 2.0
            start_color = self._terminal_color(connection.from_component, connection.from_terminal)
            end_color = self._terminal_color(connection.to_component, connection.to_terminal)
            requires_split = (
                start_color != end_color
                or connection.from_component in self._shorted_power_components
                or connection.to_component in self._shorted_power_components
            )
            if not requires_split:
                self.canvas.create_line(
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                    fill=start_color,
                    width=width,
                    capstyle=tk.ROUND,
                    smooth=True,
                    tags=("wire", connection.connection_id),
                )
            else:
                # Special conflict case: when a power source is shorted, keep the power-end segment black.
                mid_x = (start[0] + end[0]) / 2.0
                mid_y = (start[1] + end[1]) / 2.0
                if connection.from_component in self._shorted_power_components:
                    start_color = "#101010"
                if connection.to_component in self._shorted_power_components:
                    end_color = "#101010"
                self.canvas.create_line(
                    start[0],
                    start[1],
                    mid_x,
                    mid_y,
                    fill=start_color,
                    width=width,
                    capstyle=tk.ROUND,
                    smooth=False,
                    tags=("wire", connection.connection_id),
                )
                self.canvas.create_line(
                    mid_x,
                    mid_y,
                    end[0],
                    end[1],
                    fill=end_color,
                    width=width,
                    capstyle=tk.ROUND,
                    smooth=False,
                    tags=("wire", connection.connection_id),
                )

    def _draw_components(self) -> None:
        for component in self.state.components.values():
            if component.component_type == "Node":
                self._draw_node_component(component)
                continue
            if component.component_type == "ParallelContainer":
                self._draw_parallel_container(component)
                continue
            if component.component_type == "SeriesContainer":
                self._draw_series_container(component)
                continue
            center_x, center_y = self._world_to_screen(component.x, component.y)
            half_width = COMPONENT_WIDTH * self.view_scale / 2
            half_height = COMPONENT_HEIGHT * self.view_scale / 2
            left = center_x - half_width
            top = center_y - half_height
            right = center_x + half_width
            bottom = center_y + half_height
            selected = component.component_id == self.selected_component_id or component.component_id in self.selected_component_ids
            outline = THEME["selection"] if selected else THEME["border_soft"]
            if component.component_id == self.hover_component_id:
                outline = THEME["secondary"]
            if component.component_id == self.animated_component_id:
                pulse = max(0, 6 - self.animation_step)
                self.canvas.create_rectangle(
                    left - pulse,
                    top - pulse,
                    right + pulse,
                    bottom + pulse,
                    outline=THEME["secondary"],
                    width=1.2,
                )
            icon = self._get_component_icon(component.component_type, right - left, bottom - top)
            if icon is not None:
                self.canvas.create_image(center_x, center_y - max(2, int(2 * self.view_scale)), image=icon, tags=("component", component.component_id))
            if selected or component.component_id == self.hover_component_id:
                halo_pad_x = (right - left) * 0.28
                halo_pad_y = (bottom - top) * 0.32
                self.canvas.create_oval(
                    left + halo_pad_x,
                    top + halo_pad_y,
                    right - halo_pad_x,
                    bottom - halo_pad_y,
                    outline=outline,
                    width=1.6 if selected else 1.0,
                    dash=(3, 2) if component.component_id == self.hover_component_id and not selected else (),
                    tags=("component", component.component_id),
                )
            title_size = max(int(9 * self.view_scale), 8)
            value_size = max(int(10 * self.view_scale), 8)
            if self.view_scale >= 0.72:
                self.canvas.create_text(left + 12, top + 14, text=component.display_name, fill=THEME["muted"], anchor="w", font=("Segoe UI", title_size, "bold"), tags=("component", component.component_id))
            if self.view_scale >= 0.92:
                self.canvas.create_text(left + 12, bottom - 14, text=f"{component.component_id}    {component.value:.3f}", fill=THEME["accent"], anchor="w", font=("Consolas", value_size, "bold"), tags=("component", component.component_id))
            elif self.view_scale >= 0.72:
                self.canvas.create_text(left + 12, bottom - 14, text=component.component_id, fill=THEME["accent"], anchor="w", font=("Consolas", value_size, "bold"), tags=("component", component.component_id))
            for terminal in ("left", "right"):
                tx, ty = self._terminal_position(component.component_id, terminal)
                fill = THEME["secondary"] if self.pending_connection == (component.component_id, terminal) else self._terminal_color(component.component_id, terminal)
                if self.hover_terminal == (component.component_id, terminal):
                    fill = THEME["accent"]
                radius = max(5 * self.view_scale, 4)
                self.canvas.create_oval(tx - radius, ty - radius, tx + radius, ty + radius, fill=fill, outline=outline, width=1.2, tags=("terminal", f"{component.component_id}:{terminal}"))

    def _terminal_color(self, component_id: str, terminal: str) -> str:
        return self._terminal_polarity.get(f"{component_id}:{terminal}", "#101010")

    def _compute_terminal_polarity(self) -> tuple[dict[str, str], set[str]]:
        terminals: list[str] = []
        for component in self.state.components.values():
            for terminal in self._terminals_for_component(component):
                terminals.append(f"{component.component_id}:{terminal}")
        if not terminals:
            return {}, set()

        parent = {terminal: terminal for terminal in terminals}

        def find(item: str) -> str:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(a: str, b: str) -> None:
            if a not in parent or b not in parent:
                return
            root_a = find(a)
            root_b = find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for connection in self.state.connections.values():
            union(f"{connection.from_component}:{connection.from_terminal}", f"{connection.to_component}:{connection.to_terminal}")

        # Node component terminals represent one electrical node (junction).
        for component in self.state.components.values():
            if component.component_type != "Node":
                continue
            node_terminals = [f"{component.component_id}:{terminal}" for terminal in self._terminals_for_component(component)]
            for terminal in node_terminals[1:]:
                union(node_terminals[0], terminal)

        # Build opposite constraints between left/right terminals of each 2-terminal component.
        opposite_graph: dict[str, set[str]] = {}
        shorted_power_components: set[str] = set()
        for component in self.state.components.values():
            term_names = self._terminals_for_component(component)
            if "left" not in term_names or "right" not in term_names:
                continue
            left_t = f"{component.component_id}:left"
            right_t = f"{component.component_id}:right"
            if left_t not in parent or right_t not in parent:
                continue
            left_root = find(left_t)
            right_root = find(right_t)
            if left_root == right_root:
                if component.component_type in {"Source", "PowerSupply", "Battery"}:
                    shorted_power_components.add(component.component_id)
                continue
            opposite_graph.setdefault(left_root, set()).add(right_root)
            opposite_graph.setdefault(right_root, set()).add(left_root)

        color_by_root: dict[str, int] = {}
        queue: list[str] = []

        def assign(root: str, color: int) -> bool:
            existing = color_by_root.get(root)
            if existing is not None:
                return existing == color
            color_by_root[root] = color
            queue.append(root)
            return True

        # Anchor power components: right(red)=1, left(black)=0
        for component in self.state.components.values():
            if component.component_type not in {"Source", "PowerSupply", "Battery"}:
                continue
            left_t = f"{component.component_id}:left"
            right_t = f"{component.component_id}:right"
            if left_t not in parent or right_t not in parent:
                continue
            left_root = find(left_t)
            right_root = find(right_t)
            if left_root == right_root:
                shorted_power_components.add(component.component_id)
                continue
            assign(left_root, 0)
            assign(right_root, 1)

        while queue:
            root = queue.pop(0)
            root_color = color_by_root[root]
            for neighbor in opposite_graph.get(root, set()):
                if not assign(neighbor, 1 - root_color):
                    # Keep deterministic fallback on conflict.
                    color_by_root[neighbor] = 0

        # Color any disconnected groups consistently.
        for terminal in terminals:
            root = find(terminal)
            if root in color_by_root:
                continue
            color_by_root[root] = 0
            queue = [root]
            while queue:
                current = queue.pop(0)
                current_color = color_by_root[current]
                for neighbor in opposite_graph.get(current, set()):
                    if neighbor not in color_by_root:
                        color_by_root[neighbor] = 1 - current_color
                        queue.append(neighbor)

        terminal_polarity: dict[str, str] = {}
        for terminal in terminals:
            root = find(terminal)
            terminal_polarity[terminal] = "#ff3030" if color_by_root.get(root, 0) == 1 else "#101010"
        return terminal_polarity, shorted_power_components

    def _load_component_icons(self) -> dict[str, Any]:
        if Image is None:
            return {}
        base_dir = Path(__file__).resolve().parent / "assets" / "icons"
        mapping = {
            "Resistor": "Resistor.png",
            "Inductor": "Inductor.png",
            "Capacitor": "Capacitor.png",
            "Diode": "Diode.png",
            "Transistor": "Transistor.png",
            "IC": "IC.png",
            "DCMotor": "DCMotor.png",
            "ACMotor": "ACMotor.png",
            "StepperMotor": "StepperMotor.png",
            "ServoMotor": "ServoMotor.png",
            "Battery": "Battery.png",
            "PowerSupply": "PowerSupply.png",
            "Source": "Source.png",
        }
        icons: dict[str, Any] = {}
        for component_type, filename in mapping.items():
            path = base_dir / filename
            if not path.exists():
                continue
            try:
                icons[component_type] = Image.open(path).convert("RGBA")
            except Exception:
                continue
        return icons

    def _get_component_icon(self, component_type: str, width: float, height: float):
        if Image is None or ImageTk is None:
            return None
        src = self.icon_assets.get(component_type)
        if src is None:
            return None
        icon_w = max(int(width * 0.52), 16)
        icon_h = max(int(height * 0.62), 16)
        key = (component_type, icon_w, icon_h)
        cached = self.icon_cache.get(key)
        if cached is not None:
            return cached
        try:
            resized = src.resize((icon_w, icon_h), Image.LANCZOS)
            tk_img = ImageTk.PhotoImage(resized)
            self.icon_cache[key] = tk_img
            return tk_img
        except Exception:
            return None

    def _draw_parallel_container(self, component: ComponentModel) -> None:
        center_x, center_y = self._world_to_screen(component.x, component.y)
        children = [child for child in component.parallel_children if isinstance(child, dict)]
        branch_count = max(len(children), 2)
        container_height = max(COMPONENT_HEIGHT * 1.9, 70 + max(branch_count - 2, 0) * 34)
        half_width = COMPONENT_WIDTH * 1.35 * self.view_scale / 2
        half_height = container_height * self.view_scale / 2
        left = center_x - half_width
        top = center_y - half_height
        right = center_x + half_width
        bottom = center_y + half_height
        selected = component.component_id == self.selected_component_id or component.component_id in self.selected_component_ids
        outline = THEME["selection"] if selected else THEME["border_soft"]
        if component.component_id == self.hover_component_id:
            outline = THEME["secondary"]

        rail_left = left + 18
        rail_right = right - 18
        self.canvas.create_line(rail_left, top + 22, rail_left, bottom - 22, fill=outline, width=1.5)
        self.canvas.create_line(rail_right, top + 22, rail_right, bottom - 22, fill=outline, width=1.5)
        self.canvas.create_text(left + 8, top + 10, text=component.display_name, fill=THEME["muted"], anchor="w", font=("Segoe UI", max(int(9 * self.view_scale), 8), "bold"))

        child_type, equivalent, count = _parallel_container_summary(component)
        branch_y = np.linspace(top + 34, bottom - 34, branch_count)
        branch_box_w = min(76 * self.view_scale, max((rail_right - rail_left) * 0.48, 46))
        branch_box_h = min(26 * self.view_scale, 22)

        for index, y in enumerate(branch_y):
            self.canvas.create_line(rail_left, y, rail_right, y, fill=THEME["wire"], width=1.2)
            if index < len(children):
                child = children[index]
                box_left = center_x - branch_box_w / 2
                box_right = center_x + branch_box_w / 2
                box_top = y - branch_box_h / 2
                box_bottom = y + branch_box_h / 2
                self.canvas.create_rectangle(box_left, box_top, box_right, box_bottom, outline=outline, width=1.0, fill=THEME["card_inner"])
                label = str(child.get("display_name") or child.get("type") or child.get("container_type") or f"B{index + 1}")
                if self.view_scale >= 0.78:
                    self.canvas.create_text(box_left + 8, y - 5, text=label, fill=THEME["accent"], anchor="w", font=("Consolas", max(int(8 * self.view_scale), 8), "bold"))
                if self.view_scale >= 0.9 and "value" in child:
                    self.canvas.create_text(
                        box_right - 8,
                        y + 5,
                        text=f"{float(child.get('value', 0.0)):.3f}",
                        fill=THEME["muted"],
                        anchor="e",
                        font=("Consolas", max(int(7 * self.view_scale), 7), "bold"),
                    )

        if equivalent is not None and child_type is not None and self.view_scale >= 0.75:
            unit = COMPONENT_META[child_type]["unit"]
            self.canvas.create_text(left + 8, bottom - 12, text=f"Eq {equivalent:.3f} {unit}", fill=THEME["accent"], anchor="w", font=("Consolas", max(int(9 * self.view_scale), 8), "bold"))
        elif self.view_scale >= 0.75:
            self.canvas.create_text(left + 8, bottom - 12, text="Stack parallel branches here", fill=THEME["muted_soft"], anchor="w", font=("Segoe UI", max(int(8 * self.view_scale), 8)))

        for terminal in ("left", "right"):
            tx, ty = self._terminal_position(component.component_id, terminal)
            radius = max(5 * self.view_scale, 4)
            fill = THEME["card_inner"]
            if self.hover_terminal == (component.component_id, terminal):
                fill = THEME["accent"]
            self.canvas.create_oval(tx - radius, ty - radius, tx + radius, ty + radius, fill=fill, outline=outline, width=1.2, tags=("terminal", f"{component.component_id}:{terminal}"))

    def _draw_series_container(self, component: ComponentModel) -> None:
        center_x, center_y = self._world_to_screen(component.x, component.y)
        half_width = COMPONENT_WIDTH * 1.45 * self.view_scale / 2
        half_height = COMPONENT_HEIGHT * 1.1 * self.view_scale / 2
        left = center_x - half_width
        top = center_y - half_height
        right = center_x + half_width
        bottom = center_y + half_height
        selected = component.component_id == self.selected_component_id or component.component_id in self.selected_component_ids
        outline = THEME["selection"] if selected else THEME["border_soft"]
        if component.component_id == self.hover_component_id:
            outline = THEME["secondary"]

        self.canvas.create_text(left + 8, top + 10, text=component.display_name, fill=THEME["muted"], anchor="w", font=("Segoe UI", max(int(9 * self.view_scale), 8), "bold"))
        child_type, equivalent, count = _series_container_summary(component)
        children = [child for child in component.parallel_children if isinstance(child, dict)]
        stage_count = max(len(children), 2)
        start_x = left + 18
        end_x = right - 18
        line_y = center_y + 6
        stage_x = np.linspace(start_x + 14, end_x - 14, stage_count)
        box_w = min(64 * self.view_scale, max((end_x - start_x) / max(stage_count, 2) - 10, 34))
        box_h = min(24 * self.view_scale, 20)
        self.canvas.create_line(start_x, line_y, end_x, line_y, fill=THEME["wire"], width=1.3)

        for index, x in enumerate(stage_x):
            if index < len(children):
                child = children[index]
                box_left = x - box_w / 2
                box_right = x + box_w / 2
                box_top = line_y - box_h / 2
                box_bottom = line_y + box_h / 2
                self.canvas.create_rectangle(box_left, box_top, box_right, box_bottom, outline=outline, width=1.0, fill=THEME["card_inner"])
                label = str(child.get("display_name") or child.get("type") or child.get("container_type") or f"S{index + 1}")
                if self.view_scale >= 0.78:
                    self.canvas.create_text(box_left + 6, line_y - 4, text=label, fill=THEME["accent"], anchor="w", font=("Consolas", max(int(8 * self.view_scale), 8), "bold"))
                if self.view_scale >= 0.9 and "value" in child:
                    self.canvas.create_text(
                        box_right - 6,
                        line_y + 4,
                        text=f"{float(child.get('value', 0.0)):.3f}",
                        fill=THEME["muted"],
                        anchor="e",
                        font=("Consolas", max(int(7 * self.view_scale), 7), "bold"),
                    )
            if index < stage_count - 1:
                self.canvas.create_line(stage_x[index] + box_w / 2, line_y, stage_x[index + 1] - box_w / 2, line_y, fill=THEME["wire"], width=1.2)

        if equivalent is not None and child_type is not None and self.view_scale >= 0.75:
            unit = COMPONENT_META[child_type]["unit"]
            self.canvas.create_text(left + 8, bottom - 10, text=f"Eq {equivalent:.3f} {unit}", fill=THEME["accent"], anchor="w", font=("Consolas", max(int(9 * self.view_scale), 8), "bold"))
        elif self.view_scale >= 0.75:
            self.canvas.create_text(left + 8, bottom - 10, text="Stack series stages here", fill=THEME["muted_soft"], anchor="w", font=("Segoe UI", max(int(8 * self.view_scale), 8)))

        for terminal in ("left", "right"):
            tx, ty = self._terminal_position(component.component_id, terminal)
            radius = max(5 * self.view_scale, 4)
            fill = THEME["card_inner"]
            if self.hover_terminal == (component.component_id, terminal):
                fill = THEME["accent"]
            self.canvas.create_oval(tx - radius, ty - radius, tx + radius, ty + radius, fill=fill, outline=outline, width=1.2, tags=("terminal", f"{component.component_id}:{terminal}"))

    def _draw_node_component(self, component: ComponentModel) -> None:
        center_x, center_y = self._world_to_screen(component.x, component.y)
        radius = max(9 * self.view_scale, 7)
        selected = component.component_id == self.selected_component_id or component.component_id in self.selected_component_ids
        outline = THEME["selection"] if selected else THEME["border_soft"]
        if component.component_id == self.hover_component_id:
            outline = THEME["secondary"]
        self.canvas.create_rectangle(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline=outline,
            width=2 if selected else 1.2,
            fill=THEME["card_inner"],
            tags=("component", component.component_id),
        )
        if self.view_scale >= 0.92:
            self.canvas.create_text(center_x + radius + 8, center_y - radius - 4, text=component.display_name, fill=THEME["muted_soft"], anchor="w", font=("Consolas", max(int(8 * self.view_scale), 8), "bold"))
        for terminal in self._terminals_for_component(component):
            tx, ty = self._terminal_position(component.component_id, terminal)
            fill = THEME["secondary"] if self.pending_connection == (component.component_id, terminal) else THEME["card_inner"]
            if self.hover_terminal == (component.component_id, terminal):
                fill = THEME["accent"]
            dot_radius = max(4 * self.view_scale, 3)
            self.canvas.create_oval(tx - dot_radius, ty - dot_radius, tx + dot_radius, ty + dot_radius, fill=fill, outline=outline, width=1.0, tags=("terminal", f"{component.component_id}:{terminal}"))

    def _draw_palette_preview(self) -> None:
        if self.palette_drag_type is None or self.palette_drag_position is None:
            return
        center_x, center_y = self._world_to_screen(*self.palette_drag_position)
        half_width = COMPONENT_WIDTH * self.view_scale / 2
        half_height = COMPONENT_HEIGHT * self.view_scale / 2
        left = center_x - half_width
        top = center_y - half_height
        right = center_x + half_width
        bottom = center_y + half_height
        # Stipple gives us a lightweight ghosted preview without changing the real component model.
        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            outline=THEME["accent"],
            width=1.5,
            fill=THEME["card_inner"],
            stipple="gray25",
            dash=(4, 3),
        )
        self.canvas.create_text(left + 12, top + 14, text=self.palette_drag_type, fill=THEME["accent"], anchor="w", font=("Segoe UI", max(int(9 * self.view_scale), 8), "bold"))

    def _on_press(self, event) -> None:
        self.canvas.focus_set()
        component_id = self._component_at(event.x, event.y)
        connection_id = self._connection_at(event.x, event.y)
        self.selection_box_active = False
        self.selection_box_start = None
        self.selection_box_current = None
        shift_pressed = bool(getattr(event, "state", 0) & 0x1)
        ctrl_pressed = bool(getattr(event, "state", 0) & 0x4)
        self._ctrl_selection_action = False
        if self.mode == "Delete":
            if component_id is not None:
                self.state.remove_component(component_id)
                self.selected_component_id = None
                self.on_state_changed()
            elif connection_id is not None:
                self.state.remove_connection(connection_id)
                self.selected_connection_id = None
                self.on_state_changed()
            self.redraw()
            return

        if self.mode == "Connect":
            terminal = self._terminal_at(event.x, event.y)
            if terminal is None:
                return
            if self.pending_connection is None:
                self.pending_connection = terminal
                self.on_status_changed(f"Connect {terminal[0]}:{terminal[1]} to another terminal.")
            else:
                connection = self.state.add_connection(self.pending_connection[0], self.pending_connection[1], terminal[0], terminal[1])
                self.pending_connection = None
                self._clear_preview()
                if connection is not None:
                    self.selected_connection_id = connection.connection_id
                    self.on_state_changed()
                    self.on_status_changed("Connection added.")
            self.redraw()
            return

        self.selected_connection_id = connection_id
        self.selected_component_id = component_id
        if shift_pressed and component_id is None and connection_id is None:
            self.drag_component_id = None
            self.selection_box_active = True
            self.selection_box_start = (event.x, event.y)
            self.selection_box_current = (event.x, event.y)
            self.selected_component_ids = []
            self._emit_selection()
        elif component_id is not None:
            component = self.state.components[component_id]
            if ctrl_pressed:
                self._ctrl_selection_action = True
                self.drag_component_id = None
                if component_id in self.selected_component_ids:
                    self.selected_component_ids = [cid for cid in self.selected_component_ids if cid != component_id]
                else:
                    self.selected_component_ids.append(component_id)
                self.selected_component_id = self.selected_component_ids[-1] if self.selected_component_ids else None
                if self.selected_component_ids:
                    self.on_status_changed(f"Multi-select: {len(self.selected_component_ids)} components")
                else:
                    self.on_status_changed("Selection cleared.")
            else:
                self.drag_component_id = component_id
                world_x, world_y = self._screen_to_world(event.x, event.y)
                self.drag_offset = (world_x - component.x, world_y - component.y)
                self.selected_component_ids = [component_id]
                self.on_status_changed(f"Selected {component.component_id}")
        else:
            self.drag_component_id = None
            self.pan_origin = (self.pan_x, self.pan_y)
            self.pan_start = (event.x, event.y)
            self.selected_component_ids = []
        self._emit_selection()
        self.redraw()

    def _on_drag(self, event) -> None:
        if self.selection_box_active and self.selection_box_start is not None:
            self.selection_box_current = (event.x, event.y)
            self.redraw()
        elif self.mode == "Select" and self.drag_component_id is not None:
            world_x, world_y = self._screen_to_world(event.x, event.y)
            self.state.update_component_position(self.drag_component_id, self._snap(world_x - self.drag_offset[0]), self._snap(world_y - self.drag_offset[1]))
            self.redraw()
        elif self.mode == "Select" and self.pan_origin is not None and self.pan_start is not None:
            self.pan_x = self.pan_origin[0] + (event.x - self.pan_start[0])
            self.pan_y = self.pan_origin[1] + (event.y - self.pan_start[1])
            self.redraw()

    def _on_release(self, event) -> None:
        animation_target = self.drag_component_id
        if self.drag_component_id is not None:
            dragged = self.state.components.get(self.drag_component_id)
            if dragged is not None and dragged.component_type in {"Resistor", "Inductor", "Capacitor", "ParallelContainer", "SeriesContainer"}:
                release_x = getattr(event, "x", None)
                release_y = getattr(event, "y", None)
                if release_x is None or release_y is None:
                    screen_x, screen_y = self._world_to_screen(dragged.x, dragged.y)
                else:
                    screen_x, screen_y = float(release_x), float(release_y)
                target_info = self._container_target_at_screen(
                    screen_x,
                    screen_y,
                    exclude_component_id=dragged.component_id,
                )
                target_component = None if target_info is None else self.state.components.get(target_info[0])
                absorbed = False
                if target_component is not None:
                    absorbed = self.state.add_child_spec_to_container(
                        target_component.component_id,
                        self.state._component_to_child_spec(dragged),
                        [] if target_info is None else target_info[1],
                    )
                if absorbed and target_component is not None:
                    self.state.remove_component(dragged.component_id)
                    self.selected_component_id = target_component.component_id
                    self.selected_component_ids = [target_component.component_id]
                    animation_target = target_component.component_id
            self.on_state_changed()
            if animation_target is not None:
                self._start_animation(animation_target)
        if self.selection_box_active and self.selection_box_start is not None and self.selection_box_current is not None:
            self._apply_selection_box()
        self.drag_component_id = None
        self.pan_origin = None
        self.pan_start = None
        self.selection_box_active = False
        self.selection_box_start = None
        self.selection_box_current = None
        self.redraw()

    def _on_motion(self, event) -> None:
        self.hover_terminal = self._terminal_at(event.x, event.y)
        self.hover_component_id = self._component_at(event.x, event.y)
        if self.mode == "Connect" and self.pending_connection is not None:
            self._clear_preview()
            start = self._terminal_position(self.pending_connection[0], self.pending_connection[1])
            self.preview_line = self.canvas.create_line(start[0], start[1], event.x, event.y, fill=THEME["wire_pending"], dash=(4, 4), width=1.8)
        self.redraw()

    def _on_pan_press(self, event) -> None:
        self.pan_origin = (self.pan_x, self.pan_y)
        self.pan_start = (event.x, event.y)
        self.canvas.configure(cursor="fleur")

    def _on_pan_drag(self, event) -> None:
        if self.pan_origin is None or self.pan_start is None:
            return
        self.pan_x = self.pan_origin[0] + (event.x - self.pan_start[0])
        self.pan_y = self.pan_origin[1] + (event.y - self.pan_start[1])
        self.redraw()

    def _on_pan_release(self, _event) -> None:
        self.pan_origin = None
        self.pan_start = None
        self.canvas.configure(cursor="")

    def _on_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            direction = 1 if event.delta > 0 else -1
        elif getattr(event, "num", None) == 4:
            direction = 1
        else:
            direction = -1
        factor = 1.12 if direction > 0 else 1 / 1.12
        self._zoom_at(event.x, event.y, factor)
        return "break"

    def _on_double_click(self, event) -> None:
        child_target = self._container_child_at(event.x, event.y)
        if child_target is not None:
            self._open_child_value_editor(child_target[0], child_target[1])
            return
        component_id = self._component_at(event.x, event.y)
        if component_id is not None:
            self._open_rename_editor(component_id)

    def _container_child_at(self, screen_x: float, screen_y: float) -> tuple[str, int] | None:
        for component in reversed(list(self.state.components.values())):
            if component.component_type not in {"ParallelContainer", "SeriesContainer"}:
                continue
            children = [child for child in component.parallel_children if isinstance(child, dict)]
            if not children:
                continue
            center_x, center_y = self._world_to_screen(component.x, component.y)
            if component.component_type == "ParallelContainer":
                half_width = COMPONENT_WIDTH * 1.35 * self.view_scale / 2
                half_height = COMPONENT_HEIGHT * 1.9 * self.view_scale / 2
                left = center_x - half_width
                top = center_y - half_height
                right = center_x + half_width
                bottom = center_y + half_height
                rail_left = left + 18
                rail_right = right - 18
                branch_count = max(len(children), 2)
                branch_y = np.linspace(top + 34, bottom - 34, branch_count)
                branch_box_w = min(76 * self.view_scale, max((rail_right - rail_left) * 0.48, 46))
                branch_box_h = min(26 * self.view_scale, 22)
                for index, y in enumerate(branch_y[: len(children)]):
                    box_left = center_x - branch_box_w / 2
                    box_right = center_x + branch_box_w / 2
                    box_top = y - branch_box_h / 2
                    box_bottom = y + branch_box_h / 2
                    if box_left <= screen_x <= box_right and box_top <= screen_y <= box_bottom:
                        return component.component_id, index
            else:
                half_width = COMPONENT_WIDTH * 1.45 * self.view_scale / 2
                left = center_x - half_width
                right = center_x + half_width
                start_x = left + 18
                end_x = right - 18
                line_y = center_y + 6
                stage_count = max(len(children), 2)
                stage_x = np.linspace(start_x + 14, end_x - 14, stage_count)
                box_w = min(64 * self.view_scale, max((end_x - start_x) / max(stage_count, 2) - 10, 34))
                box_h = min(24 * self.view_scale, 20)
                for index, x in enumerate(stage_x[: len(children)]):
                    box_left = x - box_w / 2
                    box_right = x + box_w / 2
                    box_top = line_y - box_h / 2
                    box_bottom = line_y + box_h / 2
                    if box_left <= screen_x <= box_right and box_top <= screen_y <= box_bottom:
                        return component.component_id, index
        return None

    def _open_child_value_editor(self, component_id: str, child_index: int) -> None:
        component = self.state.components[component_id]
        if child_index < 0 or child_index >= len(component.parallel_children):
            return
        child = component.parallel_children[child_index]
        if not isinstance(child, dict) or "value" not in child:
            return
        child_label = str(child.get("display_name") or child.get("type") or f"Stage {child_index + 1}")
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit {child_label}")
        dialog.configure(bg=THEME["panel"])
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        container = ttk.Frame(dialog, style="Panel.TFrame", padding=(16, 16))
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=f"{child_label} Value", style="SectionTitle.TLabel").pack(anchor="w")
        ttk.Label(container, text=f"Update the stacked value inside {component.display_name}.", style="Body.TLabel").pack(anchor="w", pady=(4, 12))
        value_var = tk.StringVar(value=f"{float(child.get('value', 0.0)):.3f}")
        entry = ttk.Entry(container, textvariable=value_var, style="Value.TEntry", justify="center", width=18)
        entry.pack(fill="x")
        entry.focus_set()
        entry.selection_range(0, tk.END)

        def commit() -> None:
            try:
                new_value = float(value_var.get())
            except ValueError:
                return
            if new_value <= 0:
                return
            if self.state.update_container_child_value(component_id, child_index, new_value):
                dialog.destroy()
                self.on_state_changed()
                self.redraw()

        buttons = ttk.Frame(container, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="Apply", style="Secondary.TButton", command=commit).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
        entry.bind("<Return>", lambda _e: commit())

    def _open_rename_editor(self, component_id: str) -> None:
        component = self.state.components[component_id]
        dialog = tk.Toplevel(self)
        dialog.title(f"Rename {component.component_id}")
        dialog.configure(bg=THEME["panel"])
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        container = ttk.Frame(dialog, style="Panel.TFrame", padding=(16, 16))
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=f"{component.component_type} Name", style="SectionTitle.TLabel").pack(anchor="w")
        ttk.Label(container, text=f"Rename {component.component_id} for the workspace and simulation controls.", style="Body.TLabel").pack(anchor="w", pady=(4, 12))
        value_var = tk.StringVar(value=component.display_name)
        entry = ttk.Entry(container, textvariable=value_var, style="Value.TEntry", justify="left", width=18)
        entry.pack(fill="x")
        entry.focus_set()
        entry.selection_range(0, tk.END)

        def commit() -> None:
            new_name = value_var.get().strip()
            if not new_name:
                return
            self.state.rename_component(component_id, new_name)
            dialog.destroy()
            self.on_state_changed()
            self.redraw()

        buttons = ttk.Frame(container, style="Panel.TFrame")
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text="Apply", style="Secondary.TButton", command=commit).pack(side="left")
        ttk.Button(buttons, text="Cancel", style="Secondary.TButton", command=dialog.destroy).pack(side="right")
        entry.bind("<Return>", lambda _e: commit())

    def _delete_selected(self, _event=None) -> None:
        if self.selected_component_ids:
            for component_id in list(self.selected_component_ids):
                if component_id in self.state.components:
                    self.state.remove_component(component_id)
            self.selected_component_id = None
            self.selected_component_ids = []
            self.on_state_changed()
        elif self.selected_component_id is not None:
            self.state.remove_component(self.selected_component_id)
            self.selected_component_id = None
            self.selected_component_ids = []
            self.on_state_changed()
        elif self.selected_connection_id is not None:
            self.state.remove_connection(self.selected_connection_id)
            self.selected_connection_id = None
            self.on_state_changed()
        self._emit_selection()
        self.redraw()

    def _clear_preview(self) -> None:
        if self.preview_line is not None:
            self.canvas.delete(self.preview_line)
            self.preview_line = None

    def _draw_node_labels(self) -> None:
        node_positions = self._compute_node_positions()
        for index, (node_id, (x, y)) in enumerate(sorted(node_positions.items()), start=1):
            self.canvas.create_text(x, y - 12, text=f"N{index}", fill=THEME["muted_soft"], font=("Consolas", 8, "bold"))

    def _compute_node_positions(self) -> dict[str, tuple[float, float]]:
        terminals = []
        for component in self.state.components.values():
            terminals.extend([f"{component.component_id}:{terminal}" for terminal in self._terminals_for_component(component)])
        if not terminals:
            return {}
        parent = {terminal: terminal for terminal in terminals}

        def find(item: str) -> str:
            while parent[item] != item:
                parent[item] = parent[parent[item]]
                item = parent[item]
            return item

        def union(a: str, b: str) -> None:
            root_a = find(a)
            root_b = find(b)
            if root_a != root_b:
                parent[root_b] = root_a

        for connection in self.state.connections.values():
            union(f"{connection.from_component}:{connection.from_terminal}", f"{connection.to_component}:{connection.to_terminal}")

        grouped_positions: dict[str, list[tuple[float, float]]] = {}
        for terminal in terminals:
            component_id, side = terminal.split(":")
            grouped_positions.setdefault(find(terminal), []).append(self._terminal_position(component_id, side))

        node_positions: dict[str, tuple[float, float]] = {}
        for node_id, positions in grouped_positions.items():
            avg_x = sum(position[0] for position in positions) / len(positions)
            avg_y = sum(position[1] for position in positions) / len(positions)
            node_positions[node_id] = (avg_x, avg_y)
        return node_positions

    def _start_animation(self, component_id: str) -> None:
        self.animated_component_id = component_id
        self.animation_step = 0
        if self.animation_job is not None:
            self.after_cancel(self.animation_job)
        self._animate_pulse()

    def _animate_pulse(self) -> None:
        self.redraw()
        self.animation_step += 1
        if self.animation_step <= 6:
            self.animation_job = self.after(38, self._animate_pulse)
        else:
            self.animation_job = None
            self.animated_component_id = None
            self.redraw()

    def _snap(self, value: float) -> float:
        if not self.snap_to_grid:
            return value
        return round(value / GRID_SIZE) * GRID_SIZE

    def toggle_grid(self) -> None:
        self.show_grid = not self.show_grid
        self.redraw()

    def toggle_snap(self) -> None:
        self.snap_to_grid = not self.snap_to_grid

    def zoom_in(self) -> None:
        width = self.canvas.winfo_width() / 2
        height = self.canvas.winfo_height() / 2
        self._zoom_at(width, height, 1.15)

    def zoom_out(self) -> None:
        width = self.canvas.winfo_width() / 2
        height = self.canvas.winfo_height() / 2
        self._zoom_at(width, height, 1 / 1.15)

    def reset_view(self) -> None:
        self.view_scale = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._pending_initial_center = False
        self.redraw()

    def center_view(self) -> None:
        if not self.state.components:
            self.reset_view()
            return
        xs = [component.x for component in self.state.components.values()]
        ys = [component.y for component in self.state.components.values()]
        target_x = (min(xs) + max(xs)) / 2
        target_y = (min(ys) + max(ys)) / 2
        width = self.canvas.winfo_width() or 1
        height = self.canvas.winfo_height() or 1
        if width <= 64 or height <= 64:
            self._pending_initial_center = True
            self.after_idle(self.redraw)
            return
        self._pending_initial_center = False
        self.pan_x = width / 2 - target_x * self.view_scale
        self.pan_y = height / 2 - target_y * self.view_scale
        self.redraw()

    def select_component(self, component_id: str | None) -> None:
        self.selected_component_id = component_id
        self.selected_connection_id = None
        self.selected_component_ids = [component_id] if component_id is not None else []
        self._emit_selection()
        self.redraw()

    def duplicate_selected(self) -> bool:
        if self.selected_component_id is None or self.selected_component_id not in self.state.components:
            return False
        source = self.state.components[self.selected_component_id]
        duplicate = self.state.add_component(source.component_type, source.x + GRID_SIZE * 2, source.y + GRID_SIZE * 2, source.value)
        duplicate.lambda_ = source.lambda_
        duplicate.category = source.category
        duplicate.shape = source.shape
        duplicate.metadata = deepcopy(source.metadata)
        duplicate.parallel_children = deepcopy(source.parallel_children)
        self.selected_component_id = duplicate.component_id
        self.selected_component_ids = [duplicate.component_id]
        self._emit_selection()
        self.on_state_changed()
        self._start_animation(duplicate.component_id)
        return True

    def export_workspace(self) -> str | None:
        path = filedialog.asksaveasfilename(
            title="Export Circuit Workspace",
            defaultextension=".ps",
            filetypes=[("PostScript", "*.ps"), ("All Files", "*.*")],
        )
        if not path:
            return None
        self.canvas.postscript(file=path, colormode="color")
        return path

    def _world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return x * self.view_scale + self.pan_x, y * self.view_scale + self.pan_y

    def _screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        return (x - self.pan_x) / self.view_scale, (y - self.pan_y) / self.view_scale

    def _zoom_at(self, screen_x: float, screen_y: float, factor: float) -> None:
        old_scale = self.view_scale
        new_scale = min(max(old_scale * factor, 0.65), 1.9)
        if math.isclose(new_scale, old_scale, rel_tol=1e-6):
            return
        world_x, world_y = self._screen_to_world(screen_x, screen_y)
        self.view_scale = new_scale
        self.pan_x = screen_x - world_x * self.view_scale
        self.pan_y = screen_y - world_y * self.view_scale
        self.redraw()

    def _emit_selection(self) -> None:
        self.state.selected_component_id = self.selected_component_id
        self.state.selected_component_ids = list(self.selected_component_ids)
        self.state.ctrl_multiselect_redirect = self._ctrl_selection_action and len(self.selected_component_ids) > 1
        if self.on_selection_changed is not None:
            self.on_selection_changed(self.selected_component_id)

    def _apply_selection_box(self) -> None:
        if self.selection_box_start is None or self.selection_box_current is None:
            return
        x1, y1 = self.selection_box_start
        x2, y2 = self.selection_box_current
        left, right = sorted((x1, x2))
        top, bottom = sorted((y1, y2))
        selected_ids: list[str] = []
        for component in self.state.components.values():
            screen_x, screen_y = self._world_to_screen(component.x, component.y)
            if component.component_type == "Node":
                half_width = GRID_SIZE * self.view_scale * 0.5
                half_height = GRID_SIZE * self.view_scale * 0.5
            else:
                half_width = COMPONENT_WIDTH * self.view_scale / 2
                half_height = COMPONENT_HEIGHT * self.view_scale / 2
            comp_left = screen_x - half_width
            comp_right = screen_x + half_width
            comp_top = screen_y - half_height
            comp_bottom = screen_y + half_height
            if not (comp_right < left or comp_left > right or comp_bottom < top or comp_top > bottom):
                selected_ids.append(component.component_id)
        self.selected_component_ids = selected_ids
        self.selected_component_id = selected_ids[0] if selected_ids else None
        self.selected_connection_id = None
        self._emit_selection()

    def _terminal_position(self, component_id: str, terminal: str) -> tuple[float, float]:
        component = self.state.components[component_id]
        if component.component_type == "Node":
            node_offset = GRID_SIZE * 0.75
            if terminal == "left":
                return self._world_to_screen(component.x - node_offset, component.y)
            if terminal == "right":
                return self._world_to_screen(component.x + node_offset, component.y)
            if terminal == "up":
                return self._world_to_screen(component.x, component.y - node_offset)
            return self._world_to_screen(component.x, component.y + node_offset)
        offset = (COMPONENT_WIDTH * 1.2 / 2) if component.component_type in {"ParallelContainer", "SeriesContainer"} else (COMPONENT_WIDTH / 2)
        world_x = component.x - offset if terminal == "left" else component.x + offset
        return self._world_to_screen(world_x, component.y)

    def _component_at(self, x: float, y: float) -> str | None:
        world_x, world_y = self._screen_to_world(x, y)
        for component in reversed(list(self.state.components.values())):
            if component.component_type == "Node":
                node_half = GRID_SIZE * 0.5
                if abs(world_x - component.x) <= node_half and abs(world_y - component.y) <= node_half:
                    return component.component_id
                continue
            half_width = COMPONENT_WIDTH * 1.2 / 2 if component.component_type in {"ParallelContainer", "SeriesContainer"} else COMPONENT_WIDTH / 2
            if component.component_type == "ParallelContainer":
                children = [child for child in component.parallel_children if isinstance(child, dict)]
                branch_count = max(len(children), 2)
                container_height = max(COMPONENT_HEIGHT * 1.9, 70 + max(branch_count - 2, 0) * 34)
                half_height = container_height / 2
            elif component.component_type == "SeriesContainer":
                half_height = COMPONENT_HEIGHT * 1.05 / 2
            else:
                half_height = COMPONENT_HEIGHT / 2
            if (
                abs(world_x - component.x) <= half_width
                and abs(world_y - component.y) <= half_height
            ):
                return component.component_id
        return None

    def _terminal_at(self, x: float, y: float) -> tuple[str, str] | None:
        world_x, world_y = self._screen_to_world(x, y)
        terminal_radius = max(10 / self.view_scale, 8)
        for component in reversed(list(self.state.components.values())):
            for terminal in self._terminals_for_component(component):
                if component.component_type == "Node":
                    tx, ty = self._terminal_position(component.component_id, terminal)
                    terminal_world_x, terminal_world_y = self._screen_to_world(tx, ty)
                else:
                    terminal_world_x = component.x - COMPONENT_WIDTH / 2 if terminal == "left" else component.x + COMPONENT_WIDTH / 2
                    terminal_world_y = component.y
                if abs(world_x - terminal_world_x) <= terminal_radius and abs(world_y - terminal_world_y) <= terminal_radius:
                    return component.component_id, terminal
        component_id = self._component_at(x, y)
        if component_id is None:
            return None
        component = self.state.components[component_id]
        if component.component_type == "Node":
            dx = world_x - component.x
            dy = world_y - component.y
            if abs(dx) >= abs(dy):
                return component_id, "left" if dx < 0 else "right"
            return component_id, "up" if dy < 0 else "down"
        return component_id, "left" if world_x < component.x else "right"

    def _connection_at(self, x: float, y: float) -> str | None:
        point = np.array([x, y], dtype=float)
        threshold = 8.0
        for connection in reversed(list(self.state.connections.values())):
            start = np.array(self._terminal_position(connection.from_component, connection.from_terminal), dtype=float)
            end = np.array(self._terminal_position(connection.to_component, connection.to_terminal), dtype=float)
            segment = end - start
            length_squared = float(np.dot(segment, segment))
            if length_squared == 0:
                continue
            projection = float(np.dot(point - start, segment) / length_squared)
            projection = min(max(projection, 0.0), 1.0)
            closest = start + projection * segment
            if np.linalg.norm(point - closest) <= threshold:
                return connection.connection_id
        return None

    def _terminals_for_component(self, component: ComponentModel) -> tuple[str, ...]:
        if component.component_type == "Node":
            return ("left", "right", "up", "down")
        return ("left", "right")

    def _container_at_world(
        self,
        world_x: float,
        world_y: float,
        exclude_component_id: str | None = None,
    ) -> ComponentModel | None:
        for component in reversed(list(self.state.components.values())):
            if component.component_id == exclude_component_id or component.component_type not in {"ParallelContainer", "SeriesContainer"}:
                continue
            half_width = COMPONENT_WIDTH * 1.2 / 2
            if component.component_type == "ParallelContainer":
                children = [child for child in component.parallel_children if isinstance(child, dict)]
                branch_count = max(len(children), 2)
                container_height = max(COMPONENT_HEIGHT * 1.9, 70 + max(branch_count - 2, 0) * 34)
                half_height = container_height / 2
            else:
                half_height = COMPONENT_HEIGHT * 1.05 / 2
            if abs(world_x - component.x) <= half_width and abs(world_y - component.y) <= half_height:
                return component
        return None

    def _container_target_at_screen(
        self,
        screen_x: float,
        screen_y: float,
        exclude_component_id: str | None = None,
    ) -> tuple[str, list[int]] | None:
        for component in reversed(list(self.state.components.values())):
            if component.component_id == exclude_component_id:
                continue
            if component.component_type not in {"ParallelContainer", "SeriesContainer"}:
                continue
            nested = self._nested_container_target_in_component(component, screen_x, screen_y)
            if nested is not None:
                return nested
            world_x, world_y = self._screen_to_world(screen_x, screen_y)
            if self._container_at_world(world_x, world_y, exclude_component_id=exclude_component_id) == component:
                return component.component_id, []
        return None

    def _nested_container_target_in_component(
        self,
        component: ComponentModel,
        screen_x: float,
        screen_y: float,
    ) -> tuple[str, list[int]] | None:
        children = [child for child in component.parallel_children if isinstance(child, dict)]
        if not children:
            return None
        center_x, center_y = self._world_to_screen(component.x, component.y)
        if component.component_type == "ParallelContainer":
            half_width = COMPONENT_WIDTH * 1.35 * self.view_scale / 2
            half_height = COMPONENT_HEIGHT * 1.9 * self.view_scale / 2
            left = center_x - half_width
            top = center_y - half_height
            right = center_x + half_width
            bottom = center_y + half_height
            rail_left = left + 18
            rail_right = right - 18
            branch_count = max(len(children), 2)
            branch_y = np.linspace(top + 34, bottom - 34, branch_count)
            branch_box_w = min(76 * self.view_scale, max((rail_right - rail_left) * 0.48, 46))
            branch_box_h = min(26 * self.view_scale, 22)
            for index, y in enumerate(branch_y[: len(children)]):
                child = children[index]
                if str(child.get("container_type", "")) not in {"ParallelContainer", "SeriesContainer"}:
                    continue
                box_left = center_x - branch_box_w / 2
                box_right = center_x + branch_box_w / 2
                box_top = y - branch_box_h / 2
                box_bottom = y + branch_box_h / 2
                if box_left <= screen_x <= box_right and box_top <= screen_y <= box_bottom:
                    return component.component_id, [index]
        elif component.component_type == "SeriesContainer":
            half_width = COMPONENT_WIDTH * 1.45 * self.view_scale / 2
            left = center_x - half_width
            right = center_x + half_width
            start_x = left + 18
            end_x = right - 18
            line_y = center_y + 6
            stage_count = max(len(children), 2)
            stage_x = np.linspace(start_x + 14, end_x - 14, stage_count)
            box_w = min(64 * self.view_scale, max((end_x - start_x) / max(stage_count, 2) - 10, 34))
            box_h = min(24 * self.view_scale, 20)
            for index, x in enumerate(stage_x[: len(children)]):
                child = children[index]
                if str(child.get("container_type", "")) not in {"ParallelContainer", "SeriesContainer"}:
                    continue
                box_left = x - box_w / 2
                box_right = x + box_w / 2
                box_top = line_y - box_h / 2
                box_bottom = line_y + box_h / 2
                if box_left <= screen_x <= box_right and box_top <= screen_y <= box_bottom:
                    return component.component_id, [index]
        return None

    def _draw_selection_box(self) -> None:
        if not self.selection_box_active or self.selection_box_start is None or self.selection_box_current is None:
            return
        x1, y1 = self.selection_box_start
        x2, y2 = self.selection_box_current
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=THEME["accent"], dash=(4, 4), width=1.2, fill=THEME["card_inner"], stipple="gray25")


class ComponentPalette(ttk.Frame):
    def __init__(self, parent: tk.Widget, start_drag) -> None:
        super().__init__(parent, style="Panel.TFrame", padding=(14, 14))
        self.start_drag = start_drag
        self.cards: list[tuple[str, ttk.Frame]] = []
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        ttk.Label(self, text="Component Palette", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(self, text="Drag components into the workspace, wire them, then inspect the equivalent model.", style="Body.TLabel", wraplength=250).grid(row=1, column=0, sticky="w", pady=(4, 14))

        scroll_shell = ttk.Frame(self, style="Panel.TFrame")
        scroll_shell.grid(row=2, column=0, sticky="nsew")
        scroll_shell.grid_columnconfigure(0, weight=1)
        scroll_shell.grid_rowconfigure(0, weight=1)

        self.scroll_canvas = tk.Canvas(scroll_shell, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.scroll_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(scroll_shell, orient="vertical", command=self.scroll_canvas.yview, style="Dark.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)

        self.inner = ttk.Frame(self.scroll_canvas, style="Panel.TFrame")
        self.window_id = self.scroll_canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._sync_scrollregion)
        self.scroll_canvas.bind("<Configure>", self._resize_inner)
        self.scroll_canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scroll_canvas.bind("<Button-4>", self._on_mousewheel)
        self.scroll_canvas.bind("<Button-5>", self._on_mousewheel)

        library_order = (
            "Resistor",
            "Capacitor",
            "Inductor",
            "Diode",
            "Transistor",
            "IC",
            "DCMotor",
            "ACMotor",
            "StepperMotor",
            "ServoMotor",
            "Battery",
            "PowerSupply",
            "ParallelContainer",
            "SeriesContainer",
            "Source",
            "Node",
        )
        for component_type in library_order:
            card = ttk.Frame(self.inner, style="Card.TFrame", padding=(12, 12))
            card.pack(fill="x", pady=(0, 10))
            self.cards.append((component_type, card))
            ttk.Label(card, text=component_type, style="CardTitle.TLabel").pack(anchor="w")
            if component_type == "Node":
                hint = "4-way routing junction"
            elif component_type == "ParallelContainer":
                hint = "Drop same-type R/L/C parts inside"
            elif component_type == "SeriesContainer":
                hint = "Drop parts in sequence"
            else:
                meta = COMPONENT_META[component_type]
                unit = str(meta["unit"]).strip()
                value_text = f"{meta['default']:.2f}" + (f" {unit}" if unit else "")
                hint = f"{meta.get('category', 'Passive')} | default {value_text} | lambda {float(meta.get('lambda_default', 1.0e-5)):.2e}"
            ttk.Label(card, text=hint, style="Hint.TLabel").pack(anchor="w", pady=(4, 0))
            self._bind_drag(card, component_type)
            self._bind_scroll(card)
            for child in card.winfo_children():
                self._bind_drag(child, component_type)
                self._bind_scroll(child)
        self.bind("<MouseWheel>", self._on_mousewheel)
        self.bind("<Button-4>", self._on_mousewheel)
        self.bind("<Button-5>", self._on_mousewheel)
        self.inner.bind("<MouseWheel>", self._on_mousewheel)
        self.inner.bind("<Button-4>", self._on_mousewheel)
        self.inner.bind("<Button-5>", self._on_mousewheel)

    def set_filter(self, query: str) -> None:
        normalized = query.strip().casefold()
        compact_query = normalized.replace(" ", "").replace("-", "").replace("_", "")
        for component_type, card in self.cards:
            type_text = component_type.casefold()
            spaced_text = "".join([f" {ch.lower()}" if ch.isupper() else ch for ch in component_type]).strip()
            compact_type = type_text.replace(" ", "").replace("-", "").replace("_", "")
            visible = (
                not normalized
                or normalized in type_text
                or normalized in spaced_text
                or (compact_query and compact_query in compact_type)
            )
            if visible and not card.winfo_manager():
                card.pack(fill="x", pady=(0, 10))
            elif not visible and card.winfo_manager():
                card.pack_forget()
        self._sync_scrollregion()

    def _bind_drag(self, widget: tk.Widget, component_type: str) -> None:
        widget.bind("<ButtonPress-1>", lambda event, c=component_type: self.start_drag(c, event))
        widget.bind("<B1-Motion>", lambda event, c=component_type: self.start_drag(c, event, drag=True))
        widget.bind("<ButtonRelease-1>", lambda event, c=component_type: self.start_drag(c, event, release=True))

    def _bind_scroll(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    def _sync_scrollregion(self, _event=None) -> None:
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _resize_inner(self, event) -> None:
        self.scroll_canvas.itemconfigure(self.window_id, width=event.width)

    def _on_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            step = -1 if event.delta > 0 else 1
        elif getattr(event, "num", None) == 4:
            step = -1
        else:
            step = 1
        self.scroll_canvas.yview_scroll(step, "units")
        return "break"


class BuilderInspectorPanel(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_apply, on_duplicate, on_delete) -> None:
        super().__init__(parent, style="Card.TFrame", padding=(12, 12))
        self.state = state
        self.on_apply = on_apply
        self.on_duplicate = on_duplicate
        self.on_delete = on_delete
        self.selected_component_id: str | None = None
        self.value_var = tk.StringVar()

        ttk.Label(self, text="Component Inspector", style="CardTitle.TLabel").pack(anchor="w")
        self.name_var = tk.StringVar(value="No selection")
        ttk.Label(self, textvariable=self.name_var, style="Value.TLabel").pack(anchor="w", pady=(8, 2))
        self.meta_var = tk.StringVar(value="Select a component in the workspace.")
        ttk.Label(self, textvariable=self.meta_var, style="Hint.TLabel", wraplength=220, justify="left").pack(anchor="w")

        value_row = ttk.Frame(self, style="Card.TFrame")
        value_row.pack(fill="x", pady=(10, 8))
        self.value_entry = ttk.Entry(value_row, textvariable=self.value_var, style="Value.TEntry", justify="center", width=10)
        self.value_entry.pack(side="left", fill="x", expand=True)
        self.value_entry.bind("<Return>", lambda _e: self.apply())
        ttk.Button(value_row, text="Apply", style="Secondary.TButton", command=self.apply).pack(side="left", padx=(8, 0))

        action_row = ttk.Frame(self, style="Card.TFrame")
        action_row.pack(fill="x")
        ttk.Button(action_row, text="Duplicate", style="Secondary.TButton", command=self.on_duplicate).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(action_row, text="Delete", style="Secondary.TButton", command=self.on_delete).pack(side="left", fill="x", expand=True, padx=(6, 0))

        ttk.Label(
            self,
            text="Shortcuts: S Select  |  C Connect  |  D Delete  |  Ctrl+Z Undo  |  Ctrl+Y Redo",
            style="Hint.TLabel",
            wraplength=220,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))

    def set_selected_component(self, component_id: str | None) -> None:
        self.selected_component_id = component_id
        if component_id is None or component_id not in self.state.components:
            self.name_var.set("No selection")
            self.meta_var.set("Select a component in the workspace.")
            self.value_var.set("")
            self.value_entry.state(["disabled"])
            return
        component = self.state.components[component_id]
        self.name_var.set(component.display_name)
        if component.component_type == "Node":
            self.meta_var.set("4-way routing node. Use it to split or merge branches.")
            self.value_var.set("")
            self.value_entry.state(["disabled"])
        elif component.component_type == "ParallelContainer":
            child_type, equivalent, count = _parallel_container_summary(component)
            if child_type is None or equivalent is None:
                self.meta_var.set(f"Parallel container with {count} branch parts. Drop same-type R/L/C parts into it.")
            else:
                unit = COMPONENT_META[child_type]["unit"]
                self.meta_var.set(f"Parallel {child_type} container | {count} branches | Eq {equivalent:.3f} {unit}")
            self.value_var.set("")
            self.value_entry.state(["disabled"])
        elif component.component_type == "SeriesContainer":
            child_type, equivalent, count = _series_container_summary(component)
            if child_type is None or equivalent is None:
                self.meta_var.set(f"Series container with {count} staged parts. Drop parts in sequence.")
            else:
                unit = COMPONENT_META[child_type]["unit"]
                self.meta_var.set(f"Series {child_type} container | {count} stages | Eq {equivalent:.3f} {unit}")
            self.value_var.set("")
            self.value_entry.state(["disabled"])
        else:
            self.meta_var.set(f"{component.component_type}  {component.component_id} | Value in {COMPONENT_META[component.component_type]['unit']}")
            self.value_var.set(f"{component.value:.3f}")
            self.value_entry.state(["!disabled"])

    def apply(self) -> None:
        if self.selected_component_id is None or self.selected_component_id not in self.state.components:
            return
        if self.state.components[self.selected_component_id].component_type in {"Node", "ParallelContainer", "SeriesContainer"}:
            return
        try:
            value = float(self.value_var.get())
        except ValueError:
            self.set_selected_component(self.selected_component_id)
            return
        if value <= 0:
            return
        self.on_apply(self.selected_component_id, value)


class ComponentInspectorPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, on_component_updated, on_status_changed) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.on_component_updated = on_component_updated
        self.on_status_changed = on_status_changed
        self.selected_component_id: str | None = None
        self._updating_fields = False
        self.rng = np.random.default_rng()
        self._drag_pan_state: tuple[float, float, tuple[float, float], tuple[float, float]] | None = None
        self.component_selector_ids: list[str] = []
        self._axis_bounds: dict[int, tuple[float, float, float, float]] = {}

        self.grid_columnconfigure(0, weight=0, minsize=360)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_shell = ttk.Frame(self, style="Panel.TFrame")
        left_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left_shell.grid_rowconfigure(0, weight=1)
        left_shell.grid_columnconfigure(0, weight=1)

        self.left_panel_canvas = tk.Canvas(left_shell, bg=THEME["panel"], highlightthickness=0, bd=0, relief="flat")
        self.left_panel_canvas.grid(row=0, column=0, sticky="nsew")
        left_panel_scrollbar = ttk.Scrollbar(left_shell, orient="vertical", command=self.left_panel_canvas.yview, style="Dark.Vertical.TScrollbar")
        left_panel_scrollbar.grid(row=0, column=1, sticky="ns")
        self.left_panel_canvas.configure(yscrollcommand=left_panel_scrollbar.set)

        left = ttk.Frame(self.left_panel_canvas, style="Panel.TFrame", padding=(14, 14))
        self.left_panel_window = self.left_panel_canvas.create_window((0, 0), window=left, anchor="nw")
        left.bind("<Configure>", lambda _e: self.left_panel_canvas.configure(scrollregion=self.left_panel_canvas.bbox("all")))
        self.left_panel_canvas.bind("<Configure>", lambda e: self.left_panel_canvas.itemconfigure(self.left_panel_window, width=e.width))
        self.left_panel_canvas.bind("<MouseWheel>", self._on_left_panel_mousewheel)
        self.left_panel_canvas.bind("<Button-4>", self._on_left_panel_mousewheel)
        self.left_panel_canvas.bind("<Button-5>", self._on_left_panel_mousewheel)
        left.bind("<MouseWheel>", self._on_left_panel_mousewheel)
        left.bind("<Button-4>", self._on_left_panel_mousewheel)
        left.bind("<Button-5>", self._on_left_panel_mousewheel)
        left.grid_columnconfigure(0, weight=1)

        ttk.Label(left, text="Component Inspector", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left, text="Edit Name, lambda, category, and metadata for selected workspace component.", style="Body.TLabel", wraplength=320).grid(row=1, column=0, sticky="w", pady=(4, 12))

        form = ttk.Frame(left, style="Card.TFrame", padding=(12, 12))
        form.grid(row=2, column=0, sticky="ew")
        form.grid_columnconfigure(1, weight=1)

        self.component_name_var = tk.StringVar(value="")
        self.lambda_var = tk.StringVar(value="")
        self.category_var = tk.StringVar(value="Passive")
        self.metadata_var = tk.StringVar(value="")
        self.selection_var = tk.StringVar(value="No component selected")
        self.validation_var = tk.StringVar(value="Select a component in the builder workspace.")

        ttk.Label(form, textvariable=self.selection_var, style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(form, text="Name", style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.component_name_var, style="Value.TEntry").grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Lambda", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.lambda_var, style="Value.TEntry").grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Category", style="Body.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        category_combo = ttk.Combobox(form, values=["Passive", "Active", "Motor", "Power"], textvariable=self.category_var, state="readonly", style="Signal.TCombobox")
        category_combo.grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(form, text="Metadata", style="Body.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(form, textvariable=self.metadata_var, style="Value.TEntry").grid(row=4, column=1, sticky="ew", pady=4)
        ttk.Label(form, textvariable=self.validation_var, style="Hint.TLabel", wraplength=320).grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))

        selector_card = ttk.Frame(left, style="Card.TFrame", padding=(12, 12))
        selector_card.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        selector_card.grid_columnconfigure(0, weight=1)
        selector_card.grid_rowconfigure(2, weight=1)
        ttk.Label(selector_card, text="Element Selector (Multi-select)", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(selector_card, text="Ctrl/Shift click to select one or many elements.", style="Hint.TLabel").grid(row=1, column=0, sticky="w", pady=(4, 6))
        self.component_listbox = tk.Listbox(
            selector_card,
            selectmode=tk.EXTENDED,
            height=8,
            exportselection=False,
            bg=THEME["card_inner"],
            fg=THEME["text"],
            highlightthickness=1,
            highlightbackground=THEME["border_soft"],
            selectbackground=THEME["accent"],
            selectforeground=THEME["bg"],
            relief="flat",
        )
        self.component_listbox.grid(row=2, column=0, sticky="ew")
        selector_scrollbar = ttk.Scrollbar(selector_card, orient="vertical", command=self.component_listbox.yview, style="Dark.Vertical.TScrollbar")
        selector_scrollbar.grid(row=2, column=1, sticky="ns", padx=(6, 0))
        self.component_listbox.configure(yscrollcommand=selector_scrollbar.set)
        self.component_listbox.bind("<<ListboxSelect>>", lambda _e: self._on_component_list_select())
        self.component_listbox.bind("<MouseWheel>", self._on_selector_mousewheel)
        self.component_listbox.bind("<Button-4>", self._on_selector_mousewheel)
        self.component_listbox.bind("<Button-5>", self._on_selector_mousewheel)
        self.component_listbox.bind("<Enter>", lambda _e: self.component_listbox.focus_set())
        selector_card.bind("<MouseWheel>", self._on_selector_mousewheel)
        selector_card.bind("<Button-4>", self._on_selector_mousewheel)
        selector_card.bind("<Button-5>", self._on_selector_mousewheel)
        selector_scrollbar.bind("<MouseWheel>", self._on_selector_mousewheel)
        selector_scrollbar.bind("<Button-4>", self._on_selector_mousewheel)
        selector_scrollbar.bind("<Button-5>", self._on_selector_mousewheel)

        actions = ttk.Frame(left, style="Panel.TFrame")
        actions.grid(row=4, column=0, sticky="ew", pady=(10, 6))
        ttk.Button(actions, text="Apply Changes", style="Secondary.TButton", command=self.apply_fields).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(actions, text="Multi-Parameter Dialog", style="MiniToolbarAccent.TButton", command=self.open_multi_parameter_dialog).pack(side="left", fill="x", expand=True, padx=(6, 0))

        mode_card = ttk.Frame(left, style="Card.TFrame", padding=(12, 12))
        mode_card.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(mode_card, text="Reliability Simulation Mode", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w")
        self.mode_var = tk.StringVar(value="Snapshot")
        ttk.Radiobutton(mode_card, text="Snapshot", value="Snapshot", variable=self.mode_var, style="InspectorMode.TRadiobutton").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Radiobutton(mode_card, text="Lifetime", value="Lifetime", variable=self.mode_var, style="InspectorMode.TRadiobutton").grid(row=1, column=1, sticky="w", pady=(6, 0))

        self.t_max_var = tk.StringVar(value="10000")
        self.trials_var = tk.StringVar(value="2500")
        self.target_r_var = tk.StringVar(value="0.90")
        ttk.Label(mode_card, text="Time Horizon (h)", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 2))
        ttk.Entry(mode_card, textvariable=self.t_max_var, style="Value.TEntry").grid(row=2, column=1, sticky="ew", pady=(8, 2))
        ttk.Label(mode_card, text="Trials", style="Body.TLabel").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Entry(mode_card, textvariable=self.trials_var, style="Value.TEntry").grid(row=3, column=1, sticky="ew", pady=2)
        ttk.Label(mode_card, text="Target Reliability", style="Body.TLabel").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Entry(mode_card, textvariable=self.target_r_var, style="Value.TEntry").grid(row=4, column=1, sticky="ew", pady=2)
        ttk.Button(mode_card, text="Run Reliability Analysis", style="Primary.TButton", command=self.run_reliability_analysis).grid(row=5, column=0, sticky="ew", pady=(8, 0), padx=(0, 4))
        ttk.Button(mode_card, text="Save Plot", style="Secondary.TButton", command=self.save_plot).grid(row=5, column=1, sticky="ew", pady=(8, 0), padx=(4, 0))
        mode_card.grid_columnconfigure(1, weight=1)

        plot_panel = ttk.Frame(self, style="Card.TFrame", padding=(8, 8))
        plot_panel.grid(row=0, column=1, sticky="nsew")
        plot_panel.grid_rowconfigure(0, weight=1)
        plot_panel.grid_columnconfigure(0, weight=1)

        self.figure = Figure(figsize=(9.4, 6.8), facecolor=THEME["card"], dpi=100)
        self.ax_a = self.figure.add_subplot(211)
        self.ax_b = self.figure.add_subplot(212)
        self.figure.tight_layout(pad=2.0)
        self.plot_canvas = FigureCanvasTkAgg(self.figure, master=plot_panel)
        self.plot_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.figure_watermark = self.figure.text(
            0.995,
            0.01,
            "Powered by Mayank Jindal",
            ha="right",
            va="bottom",
            color=THEME["muted_soft"],
            fontsize=8,
            alpha=0.9,
        )
        self._render_placeholder()

        self.component_name_var.trace_add("write", self._apply_trace_fields)
        self.lambda_var.trace_add("write", self._apply_trace_fields)
        self.category_var.trace_add("write", self._apply_trace_fields)
        self.metadata_var.trace_add("write", self._apply_trace_fields)
        category_combo.bind("<<ComboboxSelected>>", lambda _e: self.apply_fields())

    def _render_placeholder(self) -> None:
        self.ax_a.clear()
        self.ax_b.clear()
        self.ax_a.text(0.5, 0.5, "Inspector defaults to full-circuit summary.\nCtrl + click multi-select in builder to target component set.", ha="center", va="center", color=THEME["muted"], transform=self.ax_a.transAxes)
        self.ax_b.text(0.5, 0.5, "Snapshot mode: Exact + Monte Carlo\nLifetime mode: Histogram + Empirical R(t)", ha="center", va="center", color=THEME["muted"], transform=self.ax_b.transAxes)
        self.ax_a.set_xticks([])
        self.ax_a.set_yticks([])
        self.ax_b.set_xticks([])
        self.ax_b.set_yticks([])
        self.ax_a.set_facecolor(THEME["card"])
        self.ax_b.set_facecolor(THEME["card"])
        self.plot_canvas.draw_idle()

    def sync_from_state(self, prefer_selection: bool = False) -> None:
        previous_selector_ids = self._selected_component_ids_from_listbox()
        self._refresh_component_selector()
        if prefer_selection:
            state_ids = [component_id for component_id in self.state.selected_component_ids if component_id in self.state.components]
            valid_selected_ids = state_ids if state_ids else [component_id for component_id in previous_selector_ids if component_id in self.state.components]
            if len(valid_selected_ids) > 1:
                self._reselect_component_ids(valid_selected_ids)
                self.selected_component_id = None
                self._updating_fields = True
                self.selection_var.set(f"{len(valid_selected_ids)} elements selected")
                self.validation_var.set("Multiple elements selected manually. Reliability analysis uses this set.")
                self._updating_fields = False
            elif len(valid_selected_ids) == 1:
                self._reselect_component_ids(valid_selected_ids)
                self.set_selected_component(valid_selected_ids[0])
            else:
                self.set_selected_component(self.state.selected_component_id)
        else:
            self.show_circuit_summary()
        self.after_idle(self.run_reliability_analysis)

    def show_circuit_summary(self) -> None:
        component_count = len(self.state.components)
        selected_count = len(self.state.selected_component_ids)
        self.selected_component_id = None
        self._updating_fields = True
        self.selection_var.set("Complete Circuit")
        self.component_name_var.set("Complete Circuit")
        self.lambda_var.set("")
        self.category_var.set("Passive")
        self.metadata_var.set("")
        self.validation_var.set(
            f"Components: {component_count} | Ctrl-multi-selected: {selected_count} | "
            f"Topology: {self.state.derived_parameters.topology}"
        )
        if hasattr(self, "component_listbox"):
            self.component_listbox.selection_set(0, tk.END)
        self.state.selected_component_id = None
        self.state.selected_component_ids = list(self.component_selector_ids)
        self._updating_fields = False

    def set_selected_component(self, component_id: str | None) -> None:
        self.selected_component_id = component_id
        if component_id is None or component_id not in self.state.components:
            self._updating_fields = True
            self.selection_var.set("No component selected")
            self.component_name_var.set("")
            self.lambda_var.set("")
            self.category_var.set("Passive")
            self.metadata_var.set("")
            self.validation_var.set("Select a component in the builder workspace.")
            self._updating_fields = False
            return
        component = self.state.components[component_id]
        self._updating_fields = True
        self.selection_var.set(f"{component.display_name} ({component.component_id})")
        self.component_name_var.set(component.display_name)
        self.lambda_var.set(f"{component.lambda_:.8g}")
        self.category_var.set(component.category)
        self.metadata_var.set(str(component.metadata.get("notes", "")))
        self.validation_var.set(f"Type: {component.component_type} | Shape: {component.shape}")
        if component_id in self.component_selector_ids:
            list_index = self.component_selector_ids.index(component_id)
            self.component_listbox.selection_clear(0, tk.END)
            self.component_listbox.selection_set(list_index)
            self.component_listbox.see(list_index)
        self.state.selected_component_id = component_id
        self.state.selected_component_ids = [component_id]
        self._updating_fields = False

    def _refresh_component_selector(self) -> None:
        if not hasattr(self, "component_listbox"):
            return
        self.component_listbox.delete(0, tk.END)
        self.component_selector_ids = []
        components = sorted(self.state.components.values(), key=lambda c: (c.component_type, c.component_id))
        for component in components:
            label = f"{component.display_name} [{component.component_type}] ({component.component_id})"
            self.component_listbox.insert(tk.END, label)
            self.component_selector_ids.append(component.component_id)

    def _selected_component_ids_from_listbox(self) -> list[str]:
        if not hasattr(self, "component_listbox"):
            return []
        selected_indices = cast(tuple[int, ...], self.component_listbox.curselection())
        ids = [self.component_selector_ids[index] for index in selected_indices if 0 <= index < len(self.component_selector_ids)]
        return [component_id for component_id in ids if component_id in self.state.components]

    def _reselect_component_ids(self, component_ids: list[str]) -> None:
        if not hasattr(self, "component_listbox"):
            return
        self.component_listbox.selection_clear(0, tk.END)
        for index, cid in enumerate(self.component_selector_ids):
            if cid in component_ids:
                self.component_listbox.selection_set(index)
        if component_ids:
            self.component_listbox.see(next((i for i, cid in enumerate(self.component_selector_ids) if cid in component_ids), 0))

    def _on_component_list_select(self) -> None:
        ids = self._selected_component_ids_from_listbox()
        if len(ids) == 1:
            self.set_selected_component(ids[0])
        elif len(ids) > 1:
            self.selected_component_id = None
            self._updating_fields = True
            preview_names = [self.state.components[component_id].display_name for component_id in ids[:4] if component_id in self.state.components]
            suffix = " ..." if len(ids) > 4 else ""
            self.selection_var.set(f"{len(ids)} elements selected: {', '.join(preview_names)}{suffix}")
            self.component_name_var.set(f"Multiple ({len(ids)})")
            lambdas = {
                f"{self.state.components[component_id].lambda_:.8g}"
                for component_id in ids
                if component_id in self.state.components
            }
            categories = {
                self.state.components[component_id].category
                for component_id in ids
                if component_id in self.state.components
            }
            self.lambda_var.set(next(iter(lambdas)) if len(lambdas) == 1 else "")
            self.category_var.set(next(iter(categories)) if len(categories) == 1 else "Passive")
            self.metadata_var.set("")
            self.validation_var.set("Multiple elements selected manually. Apply changes now affects all selected elements.")
            self._updating_fields = False
            self.state.selected_component_id = None
            self.state.selected_component_ids = list(ids)
            self.after_idle(self.run_reliability_analysis)
        else:
            self.show_circuit_summary()

    def _on_selector_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            step = int(-event.delta / 120) if abs(int(event.delta)) >= 120 else (-1 if event.delta > 0 else 1)
        elif getattr(event, "num", None) == 4:
            step = -1
        else:
            step = 1
        self.component_listbox.yview_scroll(step, "units")
        return "break"

    def _on_left_panel_mousewheel(self, event) -> str:
        if hasattr(event, "delta") and event.delta:
            step = int(-event.delta / 120) if abs(int(event.delta)) >= 120 else (-1 if event.delta > 0 else 1)
        elif getattr(event, "num", None) == 4:
            step = -1
        else:
            step = 1
        self.left_panel_canvas.yview_scroll(step, "units")
        return "break"

    def _apply_trace_fields(self, *_args) -> None:
        if self._updating_fields:
            return
        self.apply_fields(silent=True)

    def apply_fields(self, silent: bool = False) -> None:
        selected_ids = self._selected_component_ids_from_listbox()
        if selected_ids:
            targets = selected_ids
        elif self.selected_component_id is not None and self.selected_component_id in self.state.components:
            targets = [self.selected_component_id]
        else:
            self.validation_var.set("Circuit-level view active. Select one or many elements to edit.")
            return
        name = self.component_name_var.get().strip()
        metadata_text = self.metadata_var.get().strip()
        try:
            lambda_value = float(self.lambda_var.get())
        except ValueError:
            self.validation_var.set("Lambda must be a float > 0.")
            return
        if lambda_value <= 0:
            self.validation_var.set("Lambda must be a float > 0.")
            return
        category = self.category_var.get().strip() or "Passive"
        updated_count = 0
        for component_id in targets:
            updated = self.state.update_component_profile(
                component_id,
                display_name=name if len(targets) == 1 else None,
                lambda_=lambda_value,
                category=category,
                metadata_text=metadata_text,
            )
            if updated:
                updated_count += 1
        if updated_count == 0:
            self.validation_var.set("Unable to apply component profile.")
            return
        if len(targets) == 1:
            component = self.state.components[targets[0]]
            self.validation_var.set(f"Updated {component.display_name} | lambda {component.lambda_:.3e} | {component.category}")
        else:
            self.validation_var.set(f"Updated {updated_count} components | lambda {lambda_value:.3e} | category {category}")
        self.state.selected_component_ids = list(targets)
        self.state.selected_component_id = targets[0] if len(targets) == 1 else None
        self.on_component_updated()
        self._refresh_component_selector()
        self._reselect_component_ids(targets)
        if len(targets) == 1:
            self.set_selected_component(targets[0])
        elif len(targets) > 1:
            self.selected_component_id = None
            self.selection_var.set(f"{len(targets)} elements selected")
            self.validation_var.set(f"Updated {updated_count} components | lambda {lambda_value:.3e} | category {category}")
        self.after_idle(self.run_reliability_analysis)
        if not silent:
            self.on_status_changed(f"Inspector updated {updated_count} component(s)")

    def open_multi_parameter_dialog(self) -> None:
        if self.selected_component_id is None or self.selected_component_id not in self.state.components:
            self.validation_var.set("Select a component before opening the editor.")
            return
        component = self.state.components[self.selected_component_id]
        dialog = tk.Toplevel(self)
        dialog.title(f"Edit Parameters - {component.display_name}")
        dialog.configure(bg=THEME["panel"])
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        frame = ttk.Frame(dialog, style="Panel.TFrame", padding=(14, 14))
        frame.pack(fill="both", expand=True)
        frame.grid_columnconfigure(1, weight=1)

        name_var = tk.StringVar(value=component.display_name)
        lambda_var = tk.StringVar(value=f"{component.lambda_:.8g}")
        category_var = tk.StringVar(value=component.category)
        metadata_var = tk.StringVar(value=str(component.metadata.get("notes", "")))

        ttk.Label(frame, text="Name", style="Body.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=name_var, style="Value.TEntry").grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Lambda", style="Body.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=lambda_var, style="Value.TEntry").grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Category", style="Body.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, values=["Passive", "Active", "Motor", "Power"], textvariable=category_var, state="readonly", style="Signal.TCombobox").grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(frame, text="Metadata", style="Body.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=metadata_var, style="Value.TEntry").grid(row=3, column=1, sticky="ew", pady=4)
        message_var = tk.StringVar(value="Live update enabled.")
        ttk.Label(frame, textvariable=message_var, style="Hint.TLabel", wraplength=320).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 8))

        def apply_live(*_args) -> None:
            self.component_name_var.set(name_var.get())
            self.lambda_var.set(lambda_var.get())
            self.category_var.set(category_var.get())
            self.metadata_var.set(metadata_var.get())
            self.apply_fields(silent=True)
            message_var.set(self.validation_var.get())

        name_var.trace_add("write", apply_live)
        lambda_var.trace_add("write", apply_live)
        category_var.trace_add("write", apply_live)
        metadata_var.trace_add("write", apply_live)

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.grid(row=5, column=0, columnspan=2, sticky="ew")
        ttk.Button(buttons, text="Apply", style="Secondary.TButton", command=apply_live).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ttk.Button(buttons, text="Close", style="Primary.TButton", command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def run_reliability_analysis(self) -> None:
        selected_ids = self._selected_component_ids_from_listbox()
        if selected_ids:
            nodes: list[tuple[float, ReliabilityNode]] = []
            for component_id in selected_ids:
                component = self.state.components.get(component_id)
                if component is None or component.component_type in {"Source", "Node"}:
                    continue
                if component.component_type == "ParallelContainer":
                    children = [child for child in component.parallel_children if isinstance(child, dict)]
                    child_nodes = [node for node in (_reliability_node_from_child(child, component.display_name) for child in children) if node is not None]
                    if child_nodes:
                        nodes.append((component.x, ReliabilityParallelNode(child_nodes)))
                elif component.component_type == "SeriesContainer":
                    children = [child for child in component.parallel_children if isinstance(child, dict)]
                    child_nodes = [node for node in (_reliability_node_from_child(child, component.display_name) for child in children) if node is not None]
                    if child_nodes:
                        nodes.append((component.x, ReliabilitySeriesNode(child_nodes)))
                else:
                    lambda_ = _normalize_lambda(component.lambda_, float(_meta_for_component(component.component_type).get("lambda_default", 1.0e-5)))
                    nodes.append((component.x, ReliabilityComponentNode(component.display_name, lambda_)))
            ordered_nodes = [node for _, node in sorted(nodes, key=lambda pair: pair[0])]
            if ordered_nodes:
                topology_text = self.state.derived_parameters.topology.lower()
                system = ReliabilityParallelNode(ordered_nodes) if topology_text.startswith("parallel") else ReliabilitySeriesNode(ordered_nodes)
            else:
                system = None
        else:
            system = build_reliability_system(self.state)
        if system is None:
            self.validation_var.set("Add reliability components in workspace before running analysis.")
            self._render_placeholder()
            return

        try:
            t_max = max(float(self.t_max_var.get()), 1.0)
        except ValueError:
            t_max = 10000.0
            self.t_max_var.set("10000")
        try:
            trials = max(int(float(self.trials_var.get())), 50)
        except ValueError:
            trials = 2500
            self.trials_var.set("2500")
        try:
            target_r = min(max(float(self.target_r_var.get()), 1.0e-6), 0.999999)
        except ValueError:
            target_r = 0.90
            self.target_r_var.set("0.90")

        self.ax_a.clear()
        self.ax_b.clear()
        if self.mode_var.get() == "Snapshot":
            time_grid = np.linspace(0.0, t_max, 70)
            exact = np.array([system.reliability(float(t)) for t in time_grid], dtype=float)
            monte = np.array([reliability_snapshot_monte_carlo(system, float(t), trials, self.rng) for t in time_grid], dtype=float)
            warranty_t = reliability_calculate_warranty(system, target_r)

            self.ax_a.plot(time_grid, exact, label="Exact Reliability", color=THEME["accent"], linewidth=2.0)
            self.ax_a.plot(time_grid, monte, label="Monte Carlo", color=THEME["secondary"], linewidth=1.4)
            self.ax_a.axhline(y=target_r, linestyle="--", color=THEME["muted_soft"], label="Target Reliability")
            self.ax_a.axvline(x=warranty_t, linestyle="--", color=THEME["danger"], label="Warranty Time")
            self.ax_a.set_title("Snapshot Mode: Reliability vs Time", color=THEME["text"])
            self.ax_a.set_xlabel("Time (hours)")
            self.ax_a.set_ylabel("Reliability")
            self.ax_a.set_ylim(0, 1.05)
            self.ax_a.grid(alpha=0.25)
            self.ax_a.legend()

            self.ax_b.text(
                0.02,
                0.9,
                f"Warranty for target R={target_r:.3f}: {format_duration_hours(warranty_t)}",
                ha="left",
                va="top",
                color=THEME["text"],
                transform=self.ax_b.transAxes,
            )
            self.ax_b.text(
                0.02,
                0.72,
                "Snapshot checks P(system alive at time t)",
                ha="left",
                va="top",
                color=THEME["muted"],
                transform=self.ax_b.transAxes,
            )
            self.ax_b.set_xticks([])
            self.ax_b.set_yticks([])
            self.validation_var.set("Snapshot simulation complete.")
            self.on_status_changed("Reliability snapshot simulation complete.")
        else:
            failure_times = reliability_lifetime_samples(system, trials, self.rng)
            t_grid, empirical = reliability_empirical_curve(failure_times, points=90)

            self.ax_a.hist(failure_times, bins=36, color=THEME["accent"], alpha=0.8, edgecolor=THEME["border"])
            self.ax_a.set_title("Lifetime Mode: Failure Time Histogram", color=THEME["text"])
            self.ax_a.set_xlabel("Failure Time (hours)")
            self.ax_a.set_ylabel("Count")
            self.ax_a.grid(alpha=0.25)

            self.ax_b.plot(t_grid, empirical, color=THEME["secondary"], linewidth=2.0, label="Empirical R(t)=P(T>t)")
            self.ax_b.set_title("Lifetime Mode: Empirical Reliability Curve", color=THEME["text"])
            self.ax_b.set_xlabel("Time (hours)")
            self.ax_b.set_ylabel("Reliability")
            self.ax_b.set_ylim(0, 1.05)
            self.ax_b.grid(alpha=0.25)
            self.ax_b.legend()
            self.validation_var.set("Lifetime simulation complete.")
            self.on_status_changed("Reliability lifetime simulation complete.")

        for axis in (self.ax_a, self.ax_b):
            axis.set_facecolor(THEME["card"])
            axis.tick_params(colors=THEME["muted"])
            axis.xaxis.label.set_color(THEME["muted"])
            axis.yaxis.label.set_color(THEME["muted"])
            axis.title.set_color(THEME["text"])
            for spine in axis.spines.values():
                spine.set_color(THEME["border_soft"])
        self._record_axis_bounds(self.ax_a)
        self._record_axis_bounds(self.ax_b)
        self.figure.tight_layout(pad=2.0)
        self.plot_canvas.draw_idle()

    def save_plot(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Reliability Plot",
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")],
        )
        if not path:
            return
        self.figure.savefig(path, facecolor=self.figure.get_facecolor(), dpi=160, bbox_inches="tight")
        self.on_status_changed(f"Reliability plot saved to {path}")

    def _on_graph_scroll(self, event) -> None:
        axis = event.inaxes
        if axis is None or event.xdata is None or event.ydata is None:
            return
        button = str(getattr(event, "button", ""))
        step = getattr(event, "step", 0)
        direction = 1 if step > 0 or button == "up" else -1
        scale = 0.9 if direction > 0 else 1.1
        x_left, x_right = axis.get_xlim()
        y_bottom, y_top = axis.get_ylim()
        x_center = float(event.xdata)
        y_center = float(event.ydata)
        x_span = max(abs(x_right - x_left), 1e-6)
        y_span = max(abs(y_top - y_bottom), 1e-6)
        new_half_x = max(x_span * scale * 0.5, 1e-6)
        new_half_y = max(y_span * scale * 0.5, 1e-6)
        axis.set_xlim(x_center - new_half_x, x_center + new_half_x)
        axis.set_ylim(y_center - new_half_y, y_center + new_half_y)
        self._clamp_axis_limits(axis)
        self.plot_canvas.draw_idle()

    def _on_graph_press(self, event) -> None:
        if event.button != 1 or event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        axis = event.inaxes
        self._drag_pan_state = (float(event.xdata), float(event.ydata), axis.get_xlim(), axis.get_ylim())

    def _on_graph_motion(self, event) -> None:
        if self._drag_pan_state is None or event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        start_x, start_y, (x0, x1), (y0, y1) = self._drag_pan_state
        dx = float(event.xdata) - start_x
        dy = float(event.ydata) - start_y
        if not (math.isfinite(dx) and math.isfinite(dy)):
            return
        event.inaxes.set_xlim(x0 - dx, x1 - dx)
        event.inaxes.set_ylim(y0 - dy, y1 - dy)
        self._clamp_axis_limits(event.inaxes)
        self.plot_canvas.draw_idle()

    def _on_graph_release(self, _event) -> None:
        self._drag_pan_state = None

    def _record_axis_bounds(self, axis) -> None:
        x_left, x_right = axis.get_xlim()
        y_bottom, y_top = axis.get_ylim()
        if not (math.isfinite(x_left) and math.isfinite(x_right) and math.isfinite(y_bottom) and math.isfinite(y_top)):
            return
        self._axis_bounds[id(axis)] = (float(min(x_left, x_right)), float(max(x_left, x_right)), float(min(y_bottom, y_top)), float(max(y_bottom, y_top)))

    def _clamp_axis_limits(self, axis) -> None:
        bounds = self._axis_bounds.get(id(axis))
        if bounds is None:
            return
        data_x_min, data_x_max, data_y_min, data_y_max = bounds
        x_left, x_right = axis.get_xlim()
        y_bottom, y_top = axis.get_ylim()
        if not (math.isfinite(x_left) and math.isfinite(x_right) and math.isfinite(y_bottom) and math.isfinite(y_top)):
            axis.set_xlim(data_x_min, data_x_max)
            axis.set_ylim(data_y_min, data_y_max)
            return
        x_span = max(abs(x_right - x_left), 1e-6)
        y_span = max(abs(y_top - y_bottom), 1e-6)
        max_x_span = max((data_x_max - data_x_min) * 3.0, 1.0)
        max_y_span = max((data_y_max - data_y_min) * 3.0, 1.0)
        x_span = min(max(x_span, 1e-6), max_x_span)
        y_span = min(max(y_span, 1e-6), max_y_span)
        x_center = (x_left + x_right) * 0.5
        y_center = (y_bottom + y_top) * 0.5
        x_margin = max((data_x_max - data_x_min) * 1.5, 1.0)
        y_margin = max((data_y_max - data_y_min) * 1.5, 1.0)
        x_center = min(max(x_center, data_x_min - x_margin), data_x_max + x_margin)
        y_center = min(max(y_center, data_y_min - y_margin), data_y_max + y_margin)
        axis.set_xlim(x_center - x_span * 0.5, x_center + x_span * 0.5)
        axis.set_ylim(y_center - y_span * 0.5, y_center + y_span * 0.5)


class CircuitBuilderPage(ttk.Frame):
    def __init__(self, parent: tk.Widget, state: SystemState, interpreter: CircuitInterpreter, on_circuit_change, on_status_changed, on_undo, on_redo, on_save, on_load, on_reset_workspace, on_apply_preset) -> None:
        super().__init__(parent, style="App.TFrame", padding=(14, 12))
        self.state = state
        self.interpreter = interpreter
        self.on_circuit_change = on_circuit_change
        self.on_status_changed = on_status_changed
        self.on_undo = on_undo
        self.on_redo = on_redo
        self.on_save = on_save
        self.on_load = on_load
        self.on_reset_workspace = on_reset_workspace
        self.on_apply_preset = on_apply_preset
        self.mode_var = tk.StringVar(value="Select")
        self.snap_var = tk.BooleanVar(value=True)
        self.grid_var = tk.BooleanVar(value=True)
        self.preset_var = tk.StringVar(value=next(iter(PRESET_LIBRARY)))
        self.topology_badge_var = tk.StringVar(value="Topology: Manual")
        self.shortcuts_enabled = False
        self.zoom_bindings_active = False
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, minsize=300)
        self.grid_columnconfigure(2, minsize=280)

        search_strip = ttk.Frame(self, style="Panel.TFrame", padding=(14, 6))
        search_strip.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 6))
        ttk.Label(search_strip, text="Search Tools", style="Body.TLabel").pack(side="left")
        self.tool_search_var = tk.StringVar(value="")
        tool_search_entry = ttk.Entry(search_strip, textvariable=self.tool_search_var, style="Value.TEntry", width=34)
        tool_search_entry.pack(side="left", padx=(8, 8))
        ttk.Label(search_strip, text="Type component name to filter palette cards.", style="Hint.TLabel").pack(side="left")

        toolbar = ttk.Frame(self, style="Panel.TFrame", padding=(14, 10))
        toolbar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 12))
        ttk.Label(toolbar, text="Circuit Builder", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(toolbar, text="Drag, connect, interpret, and simulate in one shared workspace.", style="Body.TLabel").pack(side="left", padx=(12, 0))
        mode_group = ttk.Frame(toolbar, style="Panel.TFrame")
        mode_group.pack(side="right")
        for mode in ("Select", "Connect", "Delete"):
            ttk.Radiobutton(mode_group, text=mode, value=mode, variable=self.mode_var, command=lambda m=mode: self.set_mode(m), style="Tool.TRadiobutton").pack(side="left", padx=(6, 0))
        action_group = ttk.Frame(toolbar, style="Panel.TFrame")
        action_group.pack(side="right", padx=(0, 14))
        ttk.Button(action_group, text="Undo\nCtrl+Z", style="Ribbon.TButton", command=self.on_undo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Redo\nCtrl+Y", style="Ribbon.TButton", command=self.on_redo).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Save\nProject", style="RibbonAccent.TButton", command=self.on_save).pack(side="left", padx=(0, 6))
        ttk.Button(action_group, text="Load\nProject", style="Ribbon.TButton", command=self.on_load).pack(side="left")
        preset_group = ttk.Frame(toolbar, style="Panel.TFrame")
        preset_group.pack(side="right", padx=(0, 14))
        ttk.Label(preset_group, text="Preset", style="Body.TLabel").pack(side="left", padx=(0, 8))
        preset_combo = ttk.Combobox(preset_group, values=list(PRESET_LIBRARY.keys()), textvariable=self.preset_var, state="readonly", style="Signal.TCombobox", width=18)
        preset_combo.pack(side="left", padx=(0, 6))
        ttk.Button(preset_group, text="Load Preset", style="MiniToolbarAccent.TButton", command=self._load_preset).pack(side="left")

        left_column = ttk.Frame(self, style="Panel.TFrame")
        left_column.grid(row=2, column=0, sticky="nsw", padx=(0, 12))
        left_column.grid_rowconfigure(0, weight=1)
        left_column.grid_rowconfigure(1, weight=0)
        left_column.grid_columnconfigure(0, weight=1)

        self.palette = ComponentPalette(left_column, self._handle_palette_drag)
        self.palette.grid(row=0, column=0, sticky="nsew")

        self.builder_info = BuilderInspectorPanel(left_column, self.state, self._apply_component_value, self._duplicate_selected, self._delete_selected)
        self.builder_info.grid(row=1, column=0, sticky="ew", pady=(12, 0))

        center = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
        center.grid(row=2, column=1, sticky="nsew")
        center.grid_rowconfigure(1, weight=1)
        center.grid_columnconfigure(0, weight=1)
        workspace_header = ttk.Frame(center, style="Panel.TFrame")
        workspace_header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        workspace_header.grid_columnconfigure(1, weight=1)
        title_col = ttk.Frame(workspace_header, style="Panel.TFrame")
        title_col.grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Label(title_col, text="Workspace", style="SectionTitle.TLabel").pack(side="left")
        ttk.Label(title_col, textvariable=self.topology_badge_var, style="Body.TLabel").pack(side="left", padx=(12, 0))
        tool_row = ttk.Frame(workspace_header, style="Panel.TFrame")
        tool_row.grid(row=0, column=2, sticky="e")
        primary_tools = ttk.Frame(tool_row, style="Panel.TFrame")
        primary_tools.pack(side="left")
        ttk.Button(primary_tools, text="Reset", style="MiniToolbar.TButton", command=self.on_reset_workspace).pack(side="left", padx=(0, 4))
        ttk.Button(primary_tools, text="Center", style="MiniToolbar.TButton", command=self._center_view).pack(side="left", padx=(0, 4))
        ttk.Button(primary_tools, text="Clean", style="MiniToolbar.TButton", command=self._cleanup_wires).pack(side="left", padx=(0, 4))
        ttk.Button(primary_tools, text="Dup", style="MiniToolbar.TButton", command=self._duplicate_selected).pack(side="left", padx=(0, 4))
        ttk.Button(primary_tools, text="Export", style="MiniToolbarAccent.TButton", command=self._export_workspace).pack(side="left", padx=(0, 8))
        view_tools = ttk.Frame(tool_row, style="Panel.TFrame")
        view_tools.pack(side="left")
        ttk.Button(view_tools, text="-", width=3, style="MiniToolbar.TButton", command=self._zoom_out).pack(side="left", padx=(0, 4))
        ttk.Button(view_tools, text="+", width=3, style="MiniToolbar.TButton", command=self._zoom_in).pack(side="left", padx=(0, 6))
        ttk.Checkbutton(view_tools, text="Grid", variable=self.grid_var, command=self._toggle_grid, style="Tool.TCheckbutton").pack(side="left", padx=(0, 4))
        ttk.Checkbutton(view_tools, text="Snap", variable=self.snap_var, command=self._toggle_snap, style="Tool.TCheckbutton").pack(side="left")
        self.canvas_workspace = CircuitCanvas(center, self.state, self._handle_workspace_change, self.on_status_changed, self._handle_selection_changed)
        self.canvas_workspace.grid(row=1, column=0, sticky="nsew")

        dashboard = ttk.Frame(self, style="Panel.TFrame", padding=(14, 14))
        dashboard.grid(row=2, column=2, sticky="nse", padx=(12, 0))
        dashboard.grid_columnconfigure(0, weight=1)
        ttk.Label(dashboard, text="Circuit Dashboard", style="SectionTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            dashboard,
            text="Equivalent parameters update when the graph matches a supported topology.",
            style="Body.TLabel",
            wraplength=240,
        ).grid(row=1, column=0, sticky="w", pady=(4, 14))
        self.topology_card = StatsCard(dashboard, "Detected Topology")
        self.topology_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.L_card = StatsCard(dashboard, "Equivalent Inductance", "H")
        self.L_card.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.C_card = StatsCard(dashboard, "Equivalent Capacitance", "F")
        self.C_card.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        self.R_card = StatsCard(dashboard, "Equivalent Resistance", "Ohm")
        self.R_card.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        info_card = ttk.Frame(dashboard, style="Card.TFrame", padding=(12, 12))
        info_card.grid(row=6, column=0, sticky="ew", pady=(0, 10))
        ttk.Label(info_card, text="Interpreter Status", style="CardTitle.TLabel").pack(anchor="w")
        self.message_var = tk.StringVar(value="")
        ttk.Label(info_card, textvariable=self.message_var, style="Body.TLabel", wraplength=220).pack(anchor="w", pady=(8, 0))

        self.bind_all("<KeyPress-s>", self._handle_shortcut, add="+")
        self.bind_all("<KeyPress-c>", self._handle_shortcut, add="+")
        self.bind_all("<KeyPress-d>", self._handle_shortcut, add="+")
        self.bind_all("<Delete>", self._handle_shortcut, add="+")
        self.bind_all("<BackSpace>", self._handle_shortcut, add="+")
        self.bind_all("<Control-z>", self._handle_shortcut, add="+")
        self.bind_all("<Control-y>", self._handle_shortcut, add="+")
        self.bind_all("<Control-d>", self._handle_shortcut, add="+")
        self.tool_search_var.trace_add("write", lambda *_args: self.palette.set_filter(self.tool_search_var.get()))

    def refresh_dashboard(self) -> None:
        derived = self.state.derived_parameters
        self.topology_card.set_value(derived.topology)
        if derived.L is not None:
            self.L_card.set_value(f"{derived.L:.3f}", "H")
        else:
            self.L_card.set_value("--", "H")
        if derived.C is not None:
            self.C_card.set_value(f"{derived.C:.3f}", "F")
        else:
            self.C_card.set_value("--", "F")
        if derived.R is not None:
            self.R_card.set_value(f"{derived.R:.3f}", "Ohm")
        else:
                 self.R_card.set_value("--", "Ohm")
        self.message_var.set(derived.message)
        self.topology_badge_var.set(f"Topology: {derived.topology}")
        self.builder_info.set_selected_component(self.canvas_workspace.selected_component_id)
        self.canvas_workspace.redraw()

    def _handle_workspace_change(self) -> None:
        self.state.update_derived_parameters(self.interpreter.interpret(self.state))
        self.refresh_dashboard()
        self.on_circuit_change()

    def _handle_palette_drag(self, component_type: str, event, drag: bool = False, release: bool = False) -> None:
        if release:
            self.canvas_workspace.finish_palette_drop(event.x_root, event.y_root)
        elif drag:
            self.canvas_workspace.update_palette_drop(event.x_root, event.y_root)
        else:
            self.canvas_workspace.begin_palette_drop(component_type, event.x_root, event.y_root)

    def set_shortcuts_enabled(self, enabled: bool) -> None:
        self.shortcuts_enabled = enabled
        if enabled and not self.zoom_bindings_active:
            self.canvas_workspace.canvas.focus_set()
            self.bind_all("<Control-MouseWheel>", self._handle_zoom_gesture, add="+")
            self.bind_all("<MouseWheel>", self._handle_zoom_gesture, add="+")
            self.zoom_bindings_active = True
        elif not enabled and self.zoom_bindings_active:
            self.unbind_all("<Control-MouseWheel>")
            self.unbind_all("<MouseWheel>")
            self.zoom_bindings_active = False

    def set_mode(self, mode: str) -> None:
        self.mode_var.set(mode)
        self.canvas_workspace.set_mode(mode)
        self.canvas_workspace.canvas.focus_set()

    def _handle_selection_changed(self, component_id: str | None) -> None:
        self.state.selected_component_id = component_id
        self.state.selected_component_ids = list(self.canvas_workspace.selected_component_ids)
        self.builder_info.set_selected_component(component_id)

    def _apply_component_value(self, component_id: str, value: float) -> None:
        self.state.update_component_value(component_id, value)
        self._handle_workspace_change()

    def _duplicate_selected(self) -> None:
        if self.canvas_workspace.duplicate_selected():
            self.on_status_changed("Component duplicated.")

    def _delete_selected(self) -> None:
        self.canvas_workspace._delete_selected()

    def _toggle_grid(self) -> None:
        self.canvas_workspace.toggle_grid()

    def _toggle_snap(self) -> None:
        self.canvas_workspace.toggle_snap()
        self.on_status_changed(f"Snap to grid {'enabled' if self.snap_var.get() else 'disabled'}.")

    def _zoom_in(self) -> None:
        self.canvas_workspace.zoom_in()

    def _zoom_out(self) -> None:
        self.canvas_workspace.zoom_out()

    def _center_view(self) -> None:
        self.canvas_workspace.center_view()

    def _export_workspace(self) -> None:
        path = self.canvas_workspace.export_workspace()
        if path:
            self.on_status_changed(f"Workspace exported to {path}")

    def _cleanup_wires(self) -> None:
        passive_components = [component for component in self.state.components.values() if component.component_type != "Source"]
        if not self.state.components:
            return
        if self.state.derived_parameters.topology == "Series LCR":
            ordered = sorted(self.state.components.values(), key=lambda component: component.x)
            start_x = 144
            y = 216
            for index, component in enumerate(ordered):
                self.state.update_component_position(component.component_id, start_x + index * 168, y)
        elif self.state.derived_parameters.topology == "Parallel LCR":
            sources = [component for component in self.state.components.values() if component.component_type == "Source"]
            source = sources[0] if sources else None
            if source is not None:
                self.state.update_component_position(source.component_id, 168, 228)
            sorted_passives = sorted(passive_components, key=lambda component: component.component_type)
            for index, component in enumerate(sorted_passives):
                self.state.update_component_position(component.component_id, 432, 144 + index * 120)
        else:
            for component in self.state.components.values():
                self.state.update_component_position(component.component_id, round(component.x / GRID_SIZE) * GRID_SIZE, round(component.y / GRID_SIZE) * GRID_SIZE)
        self._handle_workspace_change()
        self.canvas_workspace.center_view()
        self.on_status_changed("Workspace cleanup applied.")

    def _load_preset(self) -> None:
        self.on_apply_preset(self.preset_var.get())

    def _handle_shortcut(self, event) -> str | None:
        if not self.shortcuts_enabled:
            return None
        widget_class = event.widget.winfo_class()
        if widget_class in {"TEntry", "Entry", "Text", "TCombobox", "Listbox"}:
            return None

        key = event.keysym.lower()
        if key == "s":
            self.set_mode("Select")
            return "break"
        if key == "c":
            self.set_mode("Connect")
            return "break"
        if key == "d":
            self.set_mode("Delete")
            return "break"
        if event.state & 0x4 and key == "z":
            self.on_undo()
            return "break"
        if event.state & 0x4 and key == "y":
            self.on_redo()
            return "break"
        if event.state & 0x4 and key == "d":
            self._duplicate_selected()
            return "break"
        if event.keysym in {"Delete", "BackSpace"}:
            self.canvas_workspace._delete_selected()
            return "break"
        return None

    def _handle_zoom_gesture(self, event) -> str | None:
        if not self.shortcuts_enabled:
            return None
        widget = event.widget
        try:
            widget_class = widget.winfo_class()
        except tk.TclError:
            return None
        if widget_class in {"TEntry", "Entry", "Text", "TCombobox", "Listbox"}:
            return None
        if event.widget is self.canvas_workspace.canvas or str(event.widget).startswith(str(self.canvas_workspace.canvas)):
            return self.canvas_workspace._on_mousewheel(event)
        if getattr(event, "state", 0) & 0x4:
            return self.canvas_workspace._on_mousewheel(event)
        return None


class AppController:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.state = SystemState()
        self.signal_generator = SignalGenerator()
        self.simulation_engine = SimulationEngine()
        self.fft_processor = FFTProcessor()
        self.analyzer = Analyzer()
        self.interpreter = CircuitInterpreter()
        self.active_page = "builder"
        self.undo_stack: list[dict[str, object]] = []
        self.redo_stack: list[dict[str, object]] = []
        self._configure_root()
        self._configure_styles()
        self._build_shell()
        self._seed_demo_circuit()
        self._push_undo_state()
        self.handle_circuit_change()
        self.show_page("builder")

    def _configure_root(self) -> None:
        self.root.title("LCR Analyzer Pro")
        self.root.geometry("1520x900")
        self.root.minsize(1320, 800)
        self.root.configure(bg=THEME["bg"])
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _configure_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("App.TFrame", background=THEME["bg"])
        style.configure("Panel.TFrame", background=THEME["panel"])
        style.configure("Card.TFrame", background=THEME["card"], relief="flat")
        style.configure("Header.TFrame", background=THEME["bg"])
        style.configure("Status.TFrame", background="#121212")
        style.configure("HeaderTitle.TLabel", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 18, "bold"))
        style.configure("HeaderSub.TLabel", background=THEME["bg"], foreground=THEME["muted"], font=("Segoe UI", 10))
        style.configure("SectionTitle.TLabel", background=THEME["panel"], foreground=THEME["text"], font=("Segoe UI", 12, "bold"))
        style.configure("Body.TLabel", background=THEME["panel"], foreground=THEME["muted"], font=("Segoe UI", 9))
        style.configure("CardTitle.TLabel", background=THEME["card"], foreground=THEME["muted"], font=("Segoe UI", 9, "bold"))
        style.configure("Value.TLabel", background=THEME["card"], foreground=THEME["accent"], font=("Consolas", 10, "bold"))
        style.configure("Hint.TLabel", background=THEME["card"], foreground=THEME["muted_soft"], font=("Segoe UI", 8))
        style.configure("StatValue.TLabel", background=THEME["card"], foreground=THEME["accent"], font=("Consolas", 16, "bold"))
        style.configure("StatUnit.TLabel", background=THEME["card"], foreground=THEME["muted"], font=("Segoe UI", 9))
        style.configure("Status.TLabel", background="#121212", foreground=THEME["accent"], font=("Segoe UI", 9))
        style.configure("Value.TEntry", fieldbackground=THEME["card_inner"], background=THEME["card_inner"], foreground=THEME["text"], insertcolor=THEME["accent"], bordercolor=THEME["border_soft"], lightcolor=THEME["border_soft"], darkcolor=THEME["border_soft"], padding=5)
        style.configure("Accent.Horizontal.TScale", background=THEME["card"], troughcolor=THEME["card_inner"], bordercolor=THEME["card_inner"], lightcolor=THEME["card_inner"], darkcolor=THEME["card_inner"])
        style.configure("Secondary.TButton", background=THEME["card_alt"], foreground=THEME["text"], bordercolor=THEME["border"], focusthickness=0, focuscolor=THEME["panel"], padding=(10, 8))
        style.map("Secondary.TButton", background=[("active", "#313131")], foreground=[("active", THEME["text"])])
        style.configure("SecondaryActive.TButton", background="#21443d", foreground="#7dffd9", bordercolor="#41d9b5", focusthickness=0, focuscolor=THEME["panel"], padding=(10, 8))
        style.map("SecondaryActive.TButton", background=[("active", "#2a5a51")], foreground=[("active", "#9affea")])
        style.configure("Toolbar.TButton", background=THEME["card"], foreground=THEME["text"], bordercolor=THEME["border_soft"], focusthickness=0, focuscolor=THEME["panel"], padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("Toolbar.TButton", background=[("active", "#343434")], foreground=[("active", THEME["text"])])
        style.configure("ToolbarAccent.TButton", background=THEME["card_alt"], foreground=THEME["accent"], bordercolor=THEME["accent"], focusthickness=0, focuscolor=THEME["panel"], padding=(12, 8), font=("Segoe UI", 9, "bold"))
        style.map("ToolbarAccent.TButton", background=[("active", "#2f3b39")], foreground=[("active", THEME["accent"])])
        style.configure("MiniToolbar.TButton", background=THEME["card"], foreground=THEME["text"], bordercolor=THEME["border_soft"], focusthickness=0, focuscolor=THEME["panel"], padding=(8, 6), font=("Segoe UI", 8, "bold"))
        style.map("MiniToolbar.TButton", background=[("active", "#343434")], foreground=[("active", THEME["text"])])
        style.configure("MiniToolbarAccent.TButton", background=THEME["card_alt"], foreground=THEME["accent"], bordercolor=THEME["accent"], focusthickness=0, focuscolor=THEME["panel"], padding=(8, 6), font=("Segoe UI", 8, "bold"))
        style.map("MiniToolbarAccent.TButton", background=[("active", "#2f3b39")], foreground=[("active", THEME["accent"])])
        style.configure("Ribbon.TButton", background=THEME["card"], foreground=THEME["text"], bordercolor=THEME["border_soft"], focusthickness=0, focuscolor=THEME["panel"], padding=(12, 10), font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
        style.map("Ribbon.TButton", background=[("active", "#343434")], foreground=[("active", THEME["text"])])
        style.configure("RibbonAccent.TButton", background=THEME["card_alt"], foreground=THEME["accent"], bordercolor=THEME["accent"], focusthickness=0, focuscolor=THEME["panel"], padding=(12, 10), font=("Segoe UI", 9, "bold"), anchor="center", justify="center")
        style.map("RibbonAccent.TButton", background=[("active", "#2f3b39")], foreground=[("active", THEME["accent"])])
        style.configure("Nav.TRadiobutton", background=THEME["card"], foreground=THEME["text"], focuscolor=THEME["card"], indicatorrelief="flat", indicatormargin=0, padding=(14, 8))
        style.map("Nav.TRadiobutton", background=[("selected", THEME["card_alt"]), ("active", "#303030")], foreground=[("selected", THEME["accent"]), ("active", THEME["text"])])
        style.configure(
            "Signal.TCombobox",
            fieldbackground=THEME["card_alt"],
            background=THEME["card_alt"],
            foreground=THEME["text"],
            arrowcolor=THEME["accent"],
            bordercolor=THEME["border"],
            lightcolor=THEME["border"],
            darkcolor=THEME["border"],
            padding=6,
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "Signal.TCombobox",
            fieldbackground=[("readonly", THEME["card_alt"]), ("!disabled", THEME["card_alt"])],
            background=[("readonly", THEME["card_alt"]), ("!disabled", THEME["card_alt"])],
            foreground=[("readonly", THEME["text"]), ("!disabled", THEME["text"])],
            arrowcolor=[("readonly", THEME["accent"]), ("active", THEME["accent"])],
        )
        style.configure("Tool.TRadiobutton", background=THEME["panel"], foreground=THEME["text"], focuscolor=THEME["panel"])
        style.map("Tool.TRadiobutton", background=[("active", THEME["panel"])], foreground=[("active", THEME["accent"])])
        style.configure("InspectorMode.TRadiobutton", background=THEME["card"], foreground=THEME["muted"], focuscolor=THEME["card"])
        style.map("InspectorMode.TRadiobutton", background=[("active", THEME["card"]), ("selected", THEME["card"])], foreground=[("active", THEME["accent"]), ("selected", THEME["accent"])])
        style.configure("Tool.TCheckbutton", background=THEME["panel"], foreground=THEME["text"], focuscolor=THEME["panel"])
        style.map("Tool.TCheckbutton", background=[("active", THEME["panel"])], foreground=[("active", THEME["accent"])])
        style.configure(
            "Dark.Vertical.TScrollbar",
            background=THEME["card_alt"],
            troughcolor=THEME["panel"],
            bordercolor=THEME["border"],
            arrowcolor=THEME["accent"],
            darkcolor=THEME["card_alt"],
            lightcolor=THEME["card_alt"],
            gripcount=0,
        )
        style.map("Dark.Vertical.TScrollbar", background=[("active", "#303030")])
        self.root.option_add("*TCombobox*Listbox*Background", THEME["card"])
        self.root.option_add("*TCombobox*Listbox*Foreground", THEME["text"])
        self.root.option_add("*TCombobox*Listbox*selectBackground", THEME["accent"])
        self.root.option_add("*TCombobox*Listbox*selectForeground", THEME["bg"])
        self.root.option_add("*TCombobox*Listbox*Font", ("Segoe UI", 10, "bold"))

    def _build_shell(self) -> None:
        self.header = AppHeader(self.root, self.show_page)
        self.header.grid(row=0, column=0, sticky="ew")

        self.page_container = ttk.Frame(self.root, style="App.TFrame")
        self.page_container.grid(row=1, column=0, sticky="nsew")
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "builder": CircuitBuilderPage(self.page_container, self.state, self.interpreter, self.handle_circuit_change, self.set_status, self.undo, self.redo, self.save_project, self.load_project, self.reset_workspace, self.apply_preset),
            "simulation": SimulationPage(self.page_container, self.state, self.signal_generator, self.simulation_engine, self.fft_processor, self.analyzer, self.handle_manual_parameter_change, self.set_status, self.restore_status),
            "inspector": ComponentInspectorPage(self.page_container, self.state, self.handle_circuit_change, self.set_status),
        }
        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

        self.status_bar = StatusBar(self.root)
        self.status_bar.grid(row=2, column=0, sticky="ew")

    def _seed_demo_circuit(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=False)

    def apply_preset(self, preset_name: str, push_undo: bool = True) -> None:
        preset = PRESET_LIBRARY.get(preset_name)
        if preset is None:
            return
        self.state.clear_circuit()
        component_ids: list[str] = []
        for component_type, x, y, value in preset["components"]:
            component = self.state.add_component(component_type, x, y, value)
            component_ids.append(component.component_id)
        for from_index, from_terminal, to_index, to_terminal in preset["connections"]:
            self.state.add_connection(component_ids[from_index], from_terminal, component_ids[to_index], to_terminal)
        self.state.update_derived_parameters(self.interpreter.interpret(self.state))
        if push_undo:
            self._push_undo_state()
        self.pages["builder"].canvas_workspace.center_view()
        self.pages["builder"].refresh_dashboard()
        self.pages["simulation"].sync_from_state()
        self.pages["inspector"].sync_from_state()
        self.set_status(f"Preset loaded: {preset_name}")

    def show_page(self, page_name: str, prefer_selection: bool = False) -> None:
        self.active_page = page_name
        self.header.set_active_page(page_name)
        self.pages["builder"].set_shortcuts_enabled(page_name == "builder")
        if page_name == "simulation":
            self.pages["simulation"].sync_from_state()
        elif page_name == "inspector":
            self.pages["inspector"].sync_from_state(prefer_selection=prefer_selection)
            self.state.ctrl_multiselect_redirect = False
        else:
            self.pages["builder"].refresh_dashboard()
        self.pages[page_name].tkraise()
        if page_name == "builder":
            self.root.after_idle(self.pages["builder"].canvas_workspace.center_view)
        self.restore_status()

    def handle_circuit_change(self) -> None:
        self._push_undo_state()
        self.pages["builder"].refresh_dashboard()
        self.pages["simulation"].sync_from_state()
        self.pages["inspector"].sync_from_state(prefer_selection=self.active_page == "inspector")
        self.restore_status()

    def handle_manual_parameter_change(self) -> None:
        self.pages["builder"].refresh_dashboard()
        self.pages["inspector"].sync_from_state(prefer_selection=self.active_page == "inspector")
        self.restore_status()

    def set_status(self, text: str) -> None:
        self.status_bar.set_status(text)

    def restore_status(self) -> None:
        details: list[str] = [
            f"Topology: {self.state.derived_parameters.topology}",
            f"Signal: {self.state.signal_type}",
        ]
        if self.state.derived_parameters.L is not None:
            details.append(f"L={self.state.derived_parameters.L:.3f} H")
        if self.state.derived_parameters.C is not None:
            details.append(f"C={self.state.derived_parameters.C:.3f} F")
        if self.state.derived_parameters.R is not None:
            details.append(f"R={self.state.derived_parameters.R:.3f} Ohm")
        self.status_bar.set_status(" | ".join(details))

    def _push_undo_state(self) -> None:
        snapshot = self.state.snapshot()
        if self.undo_stack and json.dumps(self.undo_stack[-1], sort_keys=True) == json.dumps(snapshot, sort_keys=True):
            return
        self.undo_stack.append(snapshot)
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def _restore_snapshot(self, snapshot: dict[str, object], log_message: str) -> None:
        self.state.restore_snapshot(snapshot)
        self.pages["builder"].refresh_dashboard()
        self.pages["simulation"].sync_from_state()
        self.pages["inspector"].sync_from_state(prefer_selection=self.active_page == "inspector")
        self.restore_status()

    def undo(self) -> None:
        if len(self.undo_stack) <= 1:
            return
        current = self.undo_stack.pop()
        self.redo_stack.append(current)
        self._restore_snapshot(self.undo_stack[-1], "Undo applied.")

    def redo(self) -> None:
        if not self.redo_stack:
            return
        snapshot = self.redo_stack.pop()
        self.undo_stack.append(snapshot)
        self._restore_snapshot(snapshot, "Redo applied.")

    def save_project(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Save Circuit Project",
            defaultextension=".json",
            filetypes=[("Circuit Project", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(self.state.snapshot(), handle, indent=2)
        self.set_status(f"Project saved to {path}")

    def load_project(self) -> None:
        path = filedialog.askopenfilename(
            title="Load Circuit Project",
            defaultextension=".json",
            filetypes=[("Circuit Project", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        with open(path, "r", encoding="utf-8") as handle:
            snapshot = json.load(handle)
        self.state.restore_snapshot(snapshot)
        self.state.update_derived_parameters(self.interpreter.interpret(self.state))
        self._push_undo_state()
        self.pages["builder"].refresh_dashboard()
        self.pages["simulation"].sync_from_state()
        self.pages["inspector"].sync_from_state()
        self.restore_status()

    def reset_workspace(self) -> None:
        self.apply_preset("Series RLC Resonator", push_undo=True)
        self.pages["builder"].canvas_workspace.center_view()
        self.set_status("Workspace reset to the starter circuit.")


def main() -> None:
    root = tk.Tk()
    AppController(root)
    root.mainloop()


if __name__ == "__main__":
    main()
