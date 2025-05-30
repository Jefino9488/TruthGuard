"use client"

import { useEffect, useRef } from "react"
import * as d3 from "d3"

interface Node {
  id: string
  group: number
  value: number
}

interface Link {
  source: string
  target: string
  value: number
}

interface Graph {
  nodes: Node[]
  links: Link[]
}

// Sample data for topic clusters
const data: Graph = {
  nodes: [
    { id: "Economy", group: 1, value: 25 },
    { id: "Inflation", group: 1, value: 18 },
    { id: "Interest Rates", group: 1, value: 15 },
    { id: "Jobs", group: 1, value: 20 },
    { id: "Stock Market", group: 1, value: 12 },
    { id: "Politics", group: 2, value: 30 },
    { id: "Elections", group: 2, value: 22 },
    { id: "Policy", group: 2, value: 18 },
    { id: "Legislation", group: 2, value: 15 },
    { id: "Climate", group: 3, value: 20 },
    { id: "Environment", group: 3, value: 15 },
    { id: "Renewable Energy", group: 3, value: 12 },
    { id: "Carbon Emissions", group: 3, value: 10 },
    { id: "Healthcare", group: 4, value: 18 },
    { id: "Pandemic", group: 4, value: 15 },
    { id: "Insurance", group: 4, value: 10 },
    { id: "Technology", group: 5, value: 22 },
    { id: "AI", group: 5, value: 18 },
    { id: "Social Media", group: 5, value: 15 },
  ],
  links: [
    { source: "Economy", target: "Inflation", value: 8 },
    { source: "Economy", target: "Interest Rates", value: 7 },
    { source: "Economy", target: "Jobs", value: 9 },
    { source: "Economy", target: "Stock Market", value: 6 },
    { source: "Inflation", target: "Interest Rates", value: 5 },
    { source: "Politics", target: "Elections", value: 9 },
    { source: "Politics", target: "Policy", value: 8 },
    { source: "Politics", target: "Legislation", value: 7 },
    { source: "Politics", target: "Economy", value: 5 },
    { source: "Climate", target: "Environment", value: 7 },
    { source: "Climate", target: "Renewable Energy", value: 6 },
    { source: "Climate", target: "Carbon Emissions", value: 5 },
    { source: "Climate", target: "Politics", value: 4 },
    { source: "Healthcare", target: "Pandemic", value: 6 },
    { source: "Healthcare", target: "Insurance", value: 5 },
    { source: "Healthcare", target: "Politics", value: 4 },
    { source: "Technology", target: "AI", value: 7 },
    { source: "Technology", target: "Social Media", value: 6 },
    { source: "Technology", target: "Economy", value: 3 },
  ],
}

export function TopicCluster() {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!svgRef.current) return

    const width = 800
    const height = 500

    // Clear any existing SVG content
    d3.select(svgRef.current).selectAll("*").remove()

    const svg = d3
      .select(svgRef.current)
      .attr("viewBox", `0 0 ${width} ${height}`)
      .attr("width", "100%")
      .attr("height", "100%")

    // Color scale for different groups
    const color = d3.scaleOrdinal(d3.schemeCategory10)

    // Create a force simulation
    const simulation = d3
      .forceSimulation(data.nodes as d3.SimulationNodeDatum[])
      .force(
        "link",
        d3
          .forceLink(data.links)
          .id((d: any) => d.id)
          .distance((d: any) => 100 / d.value),
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force(
        "collision",
        d3.forceCollide().radius((d: any) => d.value + 10),
      )

    // Create links
    const link = svg
      .append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => Math.sqrt(d.value))

    // Create nodes
    const node = svg
      .append("g")
      .selectAll("g")
      .data(data.nodes)
      .enter()
      .append("g")
      .call(d3.drag<SVGGElement, Node>().on("start", dragstarted).on("drag", dragged).on("end", dragended) as any)

    // Add circles to nodes
    node
      .append("circle")
      .attr("r", (d) => d.value * 0.8)
      .attr("fill", (d) => color(d.group.toString()))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)

    // Add labels to nodes
    node
      .append("text")
      .text((d) => d.id)
      .attr("x", 0)
      .attr("y", (d) => -d.value - 5)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("font-weight", "bold")

    // Update positions on simulation tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y)

      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`)
    })

    // Drag functions
    function dragstarted(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      d.fx = d.x
      d.fy = d.y
    }

    function dragged(event: any, d: any) {
      d.fx = event.x
      d.fy = event.y
    }

    function dragended(event: any, d: any) {
      if (!event.active) simulation.alphaTarget(0)
      d.fx = null
      d.fy = null
    }

    return () => {
      simulation.stop()
    }
  }, [])

  return (
    <div className="w-full h-[500px] overflow-hidden">
      <svg ref={svgRef} className="w-full h-full"></svg>
    </div>
  )
}
