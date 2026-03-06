import { useEffect, useRef } from "react";
import * as d3 from "d3";
import { Network, ZoomIn, ZoomOut, RefreshCw } from "lucide-react";

interface Node extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  group: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  value: number;
}

const mockData = {
  nodes: [
    { id: "1", name: "Prabowo Subianto", type: "PER", group: 1 },
    { id: "2", name: "Gerindra", type: "ORG", group: 2 },
    { id: "3", name: "Indonesia", type: "GPE", group: 3 },
    { id: "4", name: "Joko Widodo", type: "PER", group: 1 },
    { id: "5", name: "PDI-P", type: "ORG", group: 2 },
    { id: "6", name: "Jakarta", type: "GPE", group: 3 },
    { id: "7", name: "Gibran Rakabuming", type: "PER", group: 1 },
    { id: "8", name: "Surakarta", type: "GPE", group: 3 },
  ] as Node[],
  links: [
    { source: "1", target: "2", value: 1 },
    { source: "1", target: "3", value: 1 },
    { source: "1", target: "4", value: 1 },
    { source: "2", target: "3", value: 1 },
    { source: "4", target: "5", value: 1 },
    { source: "4", target: "3", value: 1 },
    { source: "1", target: "6", value: 1 },
    { source: "1", target: "7", value: 1 },
    { source: "4", target: "7", value: 1 },
    { source: "1", target: "8", value: 1 },
  ] as Link[],
};

const colorScale: Record<number, string> = {
  1: "#3b82f6", // Blue for people
  2: "#a855f7", // Purple for organizations
  3: "#22c55e", // Green for locations
};

export default function NetworkGraph() {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const width = svgRef.current.clientWidth;
    const height = 600;

    svg.attr("width", width).attr("height", height);

    // Add zoom behavior
    const g = svg.append("g");

    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Create force simulation
    const simulation = d3
      .forceSimulation(mockData.nodes)
      .force(
        "link",
        d3.forceLink(mockData.links).id((d: any) => d.id).distance(100)
      )
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = g
      .append("g")
      .selectAll("line")
      .data(mockData.links)
      .enter()
      .append("line")
      .attr("stroke", "#4b5563")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => Math.sqrt(d.value) * 2);

    // Create nodes
    const node = g
      .append("g")
      .selectAll("g")
      .data(mockData.nodes)
      .enter()
      .append("g")
      .call(
        d3
          .drag<any, any>()
          .on("start", (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    // Add circles to nodes
    node
      .append("circle")
      .attr("r", (d) => (d.type === "PER" ? 25 : 20))
      .attr("fill", (d) => colorScale[d.group] || "#6b7280")
      .attr("stroke", "#fff")
      .attr("stroke-width", 2);

    // Add labels to nodes
    node
      .append("text")
      .text((d) => d.name)
      .attr("x", 0)
      .attr("y", (d) => (d.type === "PER" ? 40 : 35))
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .attr("font-size", "12px")
      .attr("font-weight", "500");

    // Add type labels
    node
      .append("text")
      .text((d) => d.type)
      .attr("x", 0)
      .attr("y", 5)
      .attr("text-anchor", "middle")
      .attr("fill", "#fff")
      .attr("font-size", "10px")
      .attr("font-weight", "bold");

    // Update positions on tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, []);

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
            <Network className="w-6 h-6" />
            Network Visualization
          </h2>
          <p className="text-gray-400">
            Interactive graph of entities and their relationships
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <ZoomIn className="w-5 h-5" />
          </button>
          <button className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <ZoomOut className="w-5 h-5" />
          </button>
          <button className="p-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors">
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-500" />
          <span className="text-sm text-gray-400">People</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-purple-500" />
          <span className="text-sm text-gray-400">Organizations</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-500" />
          <span className="text-sm text-gray-400">Locations</span>
        </div>
      </div>

      {/* Graph */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
        <svg ref={svgRef} className="w-full" style={{ height: "600px" }} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-white">8</p>
          <p className="text-sm text-gray-400">Nodes</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-primary-400">10</p>
          <p className="text-sm text-gray-400">Relationships</p>
        </div>
        <div className="bg-gray-800 rounded-lg p-4">
          <p className="text-2xl font-bold text-green-400">3</p>
          <p className="text-sm text-gray-400">Communities</p>
        </div>
      </div>
    </div>
  );
}
