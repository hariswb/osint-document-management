import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { Network, RefreshCw, Loader2, X, FolderKanban } from "lucide-react";
import { api, Project } from "../services/api";

interface Node extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  confidence: number | null;
  connectionCount?: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  relationship_type: string;
  confidence: number | null;
}

interface NetworkData {
  nodes: Node[];
  links: Link[];
}

const ENTITY_TYPES = [
  { type: "PER", label: "Person", color: "#3b82f6" }, // blue-500
  { type: "ORG", label: "Organization", color: "#a855f7" }, // purple-500
  { type: "GPE", label: "Location", color: "#22c55e" }, // green-500
  { type: "DAT", label: "Date", color: "#eab308" }, // yellow-500
  { type: "EVT", label: "Event", color: "#ef4444" }, // red-500
];

const getNodeColor = (type: string): string => {
  const typeConfig = ENTITY_TYPES.find((t) => t.type === type);
  return typeConfig?.color || "#6b7280";
};

interface NetworkGraphProps {
  currentProject: Project;
}

export default function NetworkGraph({ currentProject }: NetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [data, setData] = useState<NetworkData>({ nodes: [], links: [] });
  const [filteredData, setFilteredData] = useState<NetworkData>({
    nodes: [],
    links: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTypes, setSelectedTypes] = useState<string[]>(
    ENTITY_TYPES.map((t) => t.type)
  );
  const [hideInput, setHideInput] = useState("");
  const [excludedEntities, setExcludedEntities] = useState<string[]>([]);

  // Fetch network data from API
  const fetchNetworkData = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: {
        projectId?: number;
        entityTypes?: string;
        excludeEntities?: string;
      } = {
        projectId: currentProject.id,
      };

      if (selectedTypes.length > 0 && selectedTypes.length < ENTITY_TYPES.length) {
        filters.entityTypes = selectedTypes.join(",");
      }

      if (excludedEntities.length > 0) {
        filters.excludeEntities = excludedEntities.join(",");
      }

      const result = await api.getNetworkData(filters);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  // Apply client-side filtering
  useEffect(() => {
    if (!data.nodes.length) {
      setFilteredData({ nodes: [], links: [] });
      return;
    }

    // Filter nodes by type
    const typeFilteredNodes = data.nodes.filter((node) =>
      selectedTypes.includes(node.type)
    );

    const nodeIds = new Set(typeFilteredNodes.map((n) => n.id));

    // Filter links to only include visible nodes
    const filteredLinks = data.links.filter(
      (link) =>
        nodeIds.has(typeof link.source === "string" ? link.source : link.source.id) &&
        nodeIds.has(typeof link.target === "string" ? link.target : link.target.id)
    );

    // Calculate connection counts for dynamic sizing
    const connectionCounts: Record<string, number> = {};
    filteredLinks.forEach((link) => {
      const sourceId =
        typeof link.source === "string" ? link.source : link.source.id;
      const targetId =
        typeof link.target === "string" ? link.target : link.target.id;
      connectionCounts[sourceId] = (connectionCounts[sourceId] || 0) + 1;
      connectionCounts[targetId] = (connectionCounts[targetId] || 0) + 1;
    });

    const nodesWithConnections = typeFilteredNodes.map((node) => ({
      ...node,
      connectionCount: connectionCounts[node.id] || 0,
    }));

    setFilteredData({
      nodes: nodesWithConnections,
      links: filteredLinks,
    });
  }, [data, selectedTypes]);

  // Initial data fetch
  useEffect(() => {
    fetchNetworkData();
  }, [excludedEntities, currentProject.id]);

  // Render D3 graph with Canvas
  useEffect(() => {
    if (!containerRef.current || loading) return;

    const width = containerRef.current.clientWidth;
    const height = 500;

    containerRef.current.innerHTML = "";

    const canvas = document.createElement("canvas");
    canvas.width = width * window.devicePixelRatio;
    canvas.height = height * window.devicePixelRatio;
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    canvas.style.display = "block";

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    containerRef.current.appendChild(canvas);

    if (filteredData.nodes.length === 0) {
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("No data available", width / 2, height / 2);
      return;
    }

    let transform = d3.zoomIdentity;

    const draw = () => {
      ctx.save();
      ctx.clearRect(0, 0, width, height);
      ctx.translate(transform.x, transform.y);
      ctx.scale(transform.k, transform.k);

      ctx.strokeStyle = "#4b5563";
      ctx.globalAlpha = 0.6;
      ctx.lineWidth = 1.5;
      filteredData.links.forEach((link) => {
        const source = link.source as Node;
        const target = link.target as Node;
        if (!source.x || !source.y || !target.x || !target.y) return;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.stroke();
      });

      ctx.globalAlpha = 1;
      filteredData.nodes.forEach((node) => {
        if (!node.x || !node.y) return;
        const baseSize = 18;
        const connectionBonus = Math.min((node.connectionCount || 0) * 2, 15);
        const radius = baseSize + connectionBonus;

        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        ctx.fillStyle = getNodeColor(node.type);
        ctx.fill();
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();

        if (transform.k > 0.5) {
          ctx.fillStyle = "#fff";
          ctx.font = "bold 9px sans-serif";
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(node.type, node.x, node.y);
        }

        if (transform.k > 0.7) {
          ctx.font = "500 11px sans-serif";
          ctx.textBaseline = "top";
          ctx.fillText(node.name, node.x, node.y + radius + 4);
        }
      });

      ctx.restore();
    };

    let needsRedraw = false;

    const simulation = d3
      .forceSimulation(filteredData.nodes)
      .alphaDecay(0.05)
      .velocityDecay(0.5)
      .alphaMin(0.05)
      .force(
        "link",
        d3
          .forceLink(filteredData.links)
          .id((d: any) => d.id)
          .distance(120)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

    simulation.on("tick", () => {
      if (!needsRedraw) {
        needsRedraw = true;
        requestAnimationFrame(() => {
          needsRedraw = false;
          draw();
        });
      }
    });

    const zoom = d3
      .zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        transform = event.transform;
        if (!needsRedraw) {
          needsRedraw = true;
          requestAnimationFrame(() => {
            needsRedraw = false;
            draw();
          });
        }
      });

    d3.select(canvas).call(zoom);

    let draggedNode: Node | null = null;

    const getMousePos = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left - transform.x) / transform.k,
        y: (e.clientY - rect.top - transform.y) / transform.k,
      };
    };

    const findNode = (x: number, y: number): Node | null => {
      for (const node of filteredData.nodes) {
        if (!node.x || !node.y) continue;
        const baseSize = 18;
        const connectionBonus = Math.min((node.connectionCount || 0) * 2, 15);
        const radius = baseSize + connectionBonus;
        const dx = x - node.x;
        const dy = y - node.y;
        if (dx * dx + dy * dy < radius * radius) return node;
      }
      return null;
    };

    canvas.addEventListener("mousedown", (e) => {
      const pos = getMousePos(e);
      draggedNode = findNode(pos.x, pos.y);
      if (draggedNode) {
        draggedNode.fx = draggedNode.x;
        draggedNode.fy = draggedNode.y;
        simulation.alphaTarget(0.3).restart();
      }
    });

    canvas.addEventListener("mousemove", (e) => {
      if (!draggedNode) return;
      const pos = getMousePos(e);
      draggedNode.fx = pos.x;
      draggedNode.fy = pos.y;
    });

    canvas.addEventListener("mouseup", () => {
      if (draggedNode) {
        draggedNode.fx = null;
        draggedNode.fy = null;
        draggedNode = null;
        simulation.alphaTarget(0);
      }
    });

    canvas.addEventListener("mouseleave", () => {
      if (draggedNode) {
        draggedNode.fx = null;
        draggedNode.fy = null;
        draggedNode = null;
        simulation.alphaTarget(0);
      }
    });

    canvas.style.cursor = "grab";
    canvas.addEventListener("mousedown", () => {
      if (draggedNode) canvas.style.cursor = "grabbing";
    });
    canvas.addEventListener("mouseup", () => {
      canvas.style.cursor = "grab";
    });

    return () => {
      simulation.stop();
    };
  }, [filteredData, loading]);

  // Handle type filter toggle
  const toggleType = (type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  // Handle hide input submit
  const handleHideSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && hideInput.trim()) {
      const newEntity = hideInput.trim();
      if (!excludedEntities.includes(newEntity)) {
        setExcludedEntities([...excludedEntities, newEntity]);
      }
      setHideInput("");
    }
  };

  // Remove excluded entity
  const removeExcluded = (entity: string) => {
    setExcludedEntities(excludedEntities.filter((e) => e !== entity));
  };

  return (
    <div className="p-6">
      {/* Project Header */}
      <div className="mb-6 pb-4 border-b border-slate-700">
        <div className="flex items-center gap-2 mb-2">
          <FolderKanban className="w-5 h-5 text-blue-400" />
          <span className="text-sm text-slate-400">Project:</span>
          <span className="text-lg font-semibold text-slate-200">{currentProject.name}</span>
        </div>
        <p className="text-sm text-slate-500">
          Showing network of entities from documents in this project
        </p>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <Network className="w-6 h-6" />
            Network
          </h2>
          <p className="text-slate-400">
            Interactive graph of entities and their relationships
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchNetworkData}
            disabled={loading}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-sm transition-colors disabled:opacity-50"
          >
            <RefreshCw
              className={`w-5 h-5 ${loading ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Entity Type Filters */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400 mr-2">Show:</span>
            {ENTITY_TYPES.map(({ type, label, color }) => (
              <button
                key={type}
                onClick={() => toggleType(type)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  selectedTypes.includes(type)
                    ? "ring-1 ring-offset-1 ring-offset-gray-900"
                    : "opacity-40"
                }`}
                style={{
                  backgroundColor: color + "20",
                  color: color,
                }}
                title={label}
              >
                {type}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-gray-700" />

          {/* Hide Input */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Hide:</span>
            <input
              type="text"
              value={hideInput}
              onChange={(e) => setHideInput(e.target.value)}
              onKeyDown={handleHideSubmit}
              placeholder="Enter entity name & press Enter"
              className="px-3 py-1.5 bg-gray-900 border border-gray-700 rounded-md text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 w-48"
            />
          </div>
        </div>

        {/* Exclusion Pills */}
        {excludedEntities.length > 0 && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-700/50">
            <span className="text-xs text-gray-500">Hidden:</span>
            {excludedEntities.map((entity) => (
              <span
                key={entity}
                className="inline-flex items-center gap-1 px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded-full"
              >
                {entity}
                <button
                  onClick={() => removeExcluded(entity)}
                  className="hover:text-red-300"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mb-4">
        {ENTITY_TYPES.filter(({ type }) => selectedTypes.includes(type)).map(
          ({ type, label, color }) => (
            <div key={type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: color }}
              />
              <span className="text-sm text-gray-400">{label}</span>
            </div>
          )
        )}
      </div>

      {/* Graph Container */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-[500px]">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <span className="ml-3 text-gray-400">Loading network data...</span>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-[500px]">
            <div className="text-center">
              <p className="text-red-400 mb-2">{error}</p>
              <button
                onClick={fetchNetworkData}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
              >
                Retry
              </button>
            </div>
          </div>
        ) : (
          <div ref={containerRef} className="w-full" style={{ height: "500px" }} />
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-white">{data.nodes.length}</p>
          <p className="text-sm text-gray-400">Total Nodes</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-primary-400">
            {data.links.length}
          </p>
          <p className="text-sm text-gray-400">Total Relationships</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-400">
            {filteredData.nodes.length}
          </p>
          <p className="text-sm text-gray-400">Filtered Nodes</p>
        </div>
      </div>
    </div>
  );
}
