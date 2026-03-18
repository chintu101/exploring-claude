"use client";

import { useState, useEffect } from "react";
import type { ClassNode, OopConcept } from "@/types/game";
import { CLASS_COLORS } from "@/types/game";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

// ─── Tree node ────────────────────────────────────────────────────────────────

function ClassTreeNode({
  node,
  depth,
  selected,
  onSelect,
}: {
  node: ClassNode;
  depth: number;
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  const [expanded, setExpanded] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;
  const isSelected = selected === node.name;
  const color = CLASS_COLORS[node.name] ?? "#6b7280";

  return (
    <div>
      <div
        onClick={() => {
          onSelect(node.name);
          if (hasChildren) setExpanded((e) => !e);
        }}
        className={`flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
          isSelected ? "bg-gray-700" : "hover:bg-gray-800"
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {/* Expand/collapse arrow */}
        <span className="text-gray-600 text-xs w-3">
          {hasChildren ? (expanded ? "▾" : "▸") : "·"}
        </span>

        {/* Type badge */}
        <span
          className="text-xs font-mono font-bold px-1.5 py-0.5 rounded shrink-0"
          style={{
            color,
            backgroundColor: `${color}18`,
            border: `1px solid ${color}33`,
          }}
        >
          {node.name}
        </span>

        {/* Abstract / Concrete tag */}
        <span
          className={`text-xs px-1 py-0.5 rounded shrink-0 ${
            node.type === "abstract"
              ? "text-yellow-500 bg-yellow-950/30 border border-yellow-900/50"
              : "text-gray-500 bg-gray-800 border border-gray-700"
          }`}
        >
          {node.type === "abstract" ? "ABC" : "impl"}
        </span>
      </div>

      {/* Children */}
      {expanded && hasChildren && (
        <div>
          {node.children!.map((child) => (
            <ClassTreeNode
              key={child.name}
              node={child}
              depth={depth + 1}
              selected={selected}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Detail pane ─────────────────────────────────────────────────────────────

function ClassDetail({
  node,
  hierarchy,
}: {
  node: ClassNode | null;
  hierarchy: ClassNode | null;
}) {
  if (!node) {
    return (
      <div className="flex items-center justify-center h-full text-gray-600 text-sm">
        Click a class to see its details
      </div>
    );
  }

  const color = CLASS_COLORS[node.name] ?? "#6b7280";

  // Build inheritance chain from root
  function findChain(
    root: ClassNode,
    target: string,
    chain: string[] = []
  ): string[] | null {
    if (root.name === target) return [...chain, root.name];
    for (const child of root.children ?? []) {
      const found = findChain(child, target, [...chain, root.name]);
      if (found) return found;
    }
    return null;
  }

  const chain = hierarchy ? findChain(hierarchy, node.name) : [node.name];

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span
          className="text-base font-mono font-bold px-2 py-1 rounded"
          style={{ color, backgroundColor: `${color}15`, border: `1px solid ${color}30` }}
        >
          {node.name}
        </span>
        <span
          className={`text-xs px-2 py-0.5 rounded border ${
            node.type === "abstract"
              ? "text-yellow-400 border-yellow-800 bg-yellow-950/30"
              : "text-gray-400 border-gray-700"
          }`}
        >
          {node.type === "abstract" ? "Abstract Class (ABC)" : "Concrete Class"}
        </span>
      </div>

      <p className="text-gray-300 text-sm">{node.description}</p>

      {chain && chain.length > 1 && (
        <div>
          <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider">Inheritance chain</p>
          <div className="flex items-center gap-1 flex-wrap">
            {chain.map((cls, i) => (
              <span key={cls} className="flex items-center gap-1">
                <span
                  className="text-xs font-mono px-1.5 py-0.5 rounded"
                  style={{
                    color: CLASS_COLORS[cls] ?? "#6b7280",
                    backgroundColor: `${CLASS_COLORS[cls] ?? "#6b7280"}15`,
                    border: `1px solid ${CLASS_COLORS[cls] ?? "#6b7280"}30`,
                  }}
                >
                  {cls}
                </span>
                {i < chain.length - 1 && <span className="text-gray-700 text-xs">→</span>}
              </span>
            ))}
          </div>
        </div>
      )}

      {node.type === "abstract" && (
        <div className="bg-yellow-950/20 border border-yellow-900/40 rounded-lg p-2">
          <p className="text-yellow-400 text-xs">
            Abstract class: cannot be instantiated directly. Subclasses must implement its abstract methods.
          </p>
        </div>
      )}
    </div>
  );
}

// ─── Concepts tab ─────────────────────────────────────────────────────────────

function ConceptsTab({ concepts }: { concepts: OopConcept[] }) {
  const [open, setOpen] = useState<string | null>(null);

  return (
    <div className="space-y-1">
      {concepts.map((c) => (
        <div
          key={c.name}
          className="border border-gray-700 rounded-lg overflow-hidden"
        >
          <button
            onClick={() => setOpen(open === c.name ? null : c.name)}
            className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-gray-800 transition-colors"
          >
            <span className="text-sm font-semibold text-purple-300">{c.name}</span>
            <span className="text-gray-500 text-xs">{open === c.name ? "▲" : "▼"}</span>
          </button>
          {open === c.name && (
            <div className="px-3 py-2 border-t border-gray-700 bg-gray-900/50">
              <p className="text-xs text-gray-300 mb-2">{c.description}</p>
              <pre className="text-xs font-mono text-green-300 bg-gray-950 p-2 rounded whitespace-pre-wrap">
                {c.example}
              </pre>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

// ─── Main ClassExplorer ───────────────────────────────────────────────────────

export function ClassExplorer() {
  const [hierarchy, setHierarchy] = useState<ClassNode | null>(null);
  const [concepts, setConcepts] = useState<OopConcept[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<"tree" | "concepts">("tree");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cached = sessionStorage.getItem("cq_hierarchy");
    if (cached) {
      const parsed = JSON.parse(cached);
      setHierarchy(parsed.hierarchy);
      setConcepts(parsed.concepts);
      setLoading(false);
      return;
    }

    fetch(`${API_BASE}/api/class-hierarchy`)
      .then((r) => r.json())
      .then((data) => {
        setHierarchy(data.hierarchy);
        setConcepts(data.concepts);
        sessionStorage.setItem("cq_hierarchy", JSON.stringify(data));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const selectedNode = hierarchy
    ? findNode(hierarchy, selected)
    : null;

  function findNode(root: ClassNode, name: string | null): ClassNode | null {
    if (!name) return null;
    if (root.name === name) return root;
    for (const child of root.children ?? []) {
      const found = findNode(child, name);
      if (found) return found;
    }
    return null;
  }

  return (
    <div className="bg-gray-900 border border-gray-700 rounded-2xl overflow-hidden">
      {/* Header + tabs */}
      <div className="px-4 py-3 border-b border-gray-700">
        <div className="flex items-center justify-between mb-2">
          <span className="text-white font-semibold text-sm">Class Explorer</span>
        </div>
        <div className="flex gap-1">
          {(["tree", "concepts"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                tab === t ? "bg-purple-700 text-white" : "text-gray-400 hover:text-white"
              }`}
            >
              {t === "tree" ? "Hierarchy" : "OOP Concepts"}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-6 text-center text-gray-500 text-sm animate-pulse">
          Loading hierarchy…
        </div>
      ) : tab === "tree" ? (
        <div className="flex divide-x divide-gray-700 h-72">
          {/* Tree panel */}
          <div className="w-1/2 overflow-y-auto p-2">
            {hierarchy && (
              <ClassTreeNode
                node={hierarchy}
                depth={0}
                selected={selected}
                onSelect={setSelected}
              />
            )}
          </div>
          {/* Detail panel */}
          <div className="w-1/2 p-3 overflow-y-auto">
            <ClassDetail node={selectedNode} hierarchy={hierarchy} />
          </div>
        </div>
      ) : (
        <div className="p-3 max-h-72 overflow-y-auto">
          <ConceptsTab concepts={concepts} />
        </div>
      )}
    </div>
  );
}
