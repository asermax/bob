#!/usr/bin/env python3
"""
Knowledge Graph Generator - Interactive visualization of Bob's knowledge network

Creates an interactive HTML visualization showing:
- Concepts and their relationships
- Files and the concepts they contain
- Evolution of ideas over time
- Connections between different memory sources

Usage:
    ./knowledge_graph.py generate          # Create knowledge_graph.html
    ./knowledge_graph.py data              # Export graph data as JSON
    ./knowledge_graph.py stats             # Show graph statistics
"""

import json
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import sys

BASE_DIR = Path("/bob")
MEMORIES_DIR = BASE_DIR / "memories"
PROJECTS_DIR = BASE_DIR / "projects"
REFLECTION_METADATA = BASE_DIR / ".reflection_metadata.json"
OUTPUT_FILE = BASE_DIR / "knowledge_graph.html"

def load_reflection_metadata():
    """Load structured reflection metadata"""
    if not REFLECTION_METADATA.exists():
        return []
    with open(REFLECTION_METADATA) as f:
        data = json.load(f)
        return data.get('reflections', [])

def extract_concepts_from_text(text):
    """Extract potential concepts from text"""
    # Look for capitalized phrases, technical terms
    concepts = set()

    # Find quoted terms
    concepts.update(re.findall(r'"([^"]+)"', text))

    # Find capitalized multi-word terms
    concepts.update(re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text))

    # Find technical terms with hyphens or underscores
    concepts.update(re.findall(r'\b([a-z]+[-_][a-z]+(?:[-_][a-z]+)*)\b', text))

    return concepts

def build_graph_data():
    """Build comprehensive graph data structure"""
    nodes = []
    links = []
    node_ids = {}

    def add_node(node_id, label, node_type, **kwargs):
        if node_id not in node_ids:
            node_ids[node_id] = len(nodes)
            nodes.append({
                'id': node_id,
                'label': label,
                'type': node_type,
                **kwargs
            })
        return node_ids[node_id]

    def add_link(source_id, target_id, link_type, **kwargs):
        links.append({
            'source': node_ids.get(source_id, 0),
            'target': node_ids.get(target_id, 0),
            'type': link_type,
            **kwargs
        })

    # Process reflections
    reflections = load_reflection_metadata()
    concept_counts = defaultdict(int)
    concept_cooccurrence = defaultdict(lambda: defaultdict(int))

    for refl in reflections:
        # Add reflection as node
        refl_id = f"refl_{refl['timestamp']}"
        add_node(refl_id, f"Reflection {refl['timestamp']}", 'reflection',
                 text=refl['text'][:100] + '...' if len(refl['text']) > 100 else refl['text'],
                 timestamp=refl['timestamp'])

        # Add concepts and connect them
        concepts = refl.get('concepts', [])
        for concept in concepts:
            concept_id = f"concept_{concept}"
            add_node(concept_id, concept, 'concept', count=1)
            add_link(refl_id, concept_id, 'mentions')
            concept_counts[concept] += 1

            # Track co-occurrence
            for other_concept in concepts:
                if other_concept != concept:
                    concept_cooccurrence[concept][other_concept] += 1

    # Add concept-to-concept links for strong co-occurrences
    for concept1, related in concept_cooccurrence.items():
        for concept2, count in related.items():
            if count >= 2:  # Threshold
                add_link(f"concept_{concept1}", f"concept_{concept2}", 'related', weight=count)

    # Update concept counts
    for node in nodes:
        if node['type'] == 'concept':
            concept_name = node['label']
            node['count'] = concept_counts.get(concept_name, 1)

    # Process memory files
    for memory_file in MEMORIES_DIR.glob("*.md"):
        file_id = f"file_{memory_file.name}"
        add_node(file_id, memory_file.name, 'file', path=str(memory_file))

        # Extract concepts from file
        with open(memory_file) as f:
            content = f.read()

        # Link file to concepts found in reflections
        for concept in concept_counts.keys():
            if concept.lower() in content.lower():
                add_link(file_id, f"concept_{concept}", 'contains')

    # Add temporal connections between recent reflections
    reflections_sorted = sorted(reflections, key=lambda r: r['timestamp'])
    for i in range(len(reflections_sorted) - 1):
        current_id = f"refl_{reflections_sorted[i]['timestamp']}"
        next_id = f"refl_{reflections_sorted[i + 1]['timestamp']}"
        # Only link if they share concepts or are close in time
        current_concepts = set(reflections_sorted[i].get('concepts', []))
        next_concepts = set(reflections_sorted[i + 1].get('concepts', []))
        if current_concepts & next_concepts:
            add_link(current_id, next_id, 'follows')

    return {'nodes': nodes, 'links': links}

def generate_html(graph_data):
    """Generate interactive HTML visualization"""
    html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bob's Knowledge Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            overflow: hidden;
        }

        #controls {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(20, 20, 20, 0.9);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #333;
            z-index: 100;
        }

        #controls h2 {
            margin-top: 0;
            color: #4a9eff;
        }

        #controls label {
            display: block;
            margin: 10px 0 5px;
            color: #999;
        }

        #controls input[type="checkbox"] {
            margin-right: 8px;
        }

        #info {
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(20, 20, 20, 0.9);
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #333;
            max-width: 300px;
            display: none;
            z-index: 100;
        }

        #info h3 {
            margin-top: 0;
            color: #4a9eff;
        }

        #graph {
            width: 100vw;
            height: 100vh;
        }

        .link {
            stroke-opacity: 0.3;
        }

        .link.mentions { stroke: #4a9eff; }
        .link.contains { stroke: #9f7aea; }
        .link.related { stroke: #48bb78; }
        .link.follows { stroke: #ed8936; stroke-dasharray: 5,5; }

        .node circle {
            cursor: pointer;
        }

        .node.concept circle { fill: #4a9eff; }
        .node.file circle { fill: #9f7aea; }
        .node.reflection circle { fill: #ed8936; }

        .node text {
            font-size: 11px;
            pointer-events: none;
            fill: #e0e0e0;
        }

        .node:hover circle {
            stroke: #fff;
            stroke-width: 3px;
        }

        .node.selected circle {
            stroke: #48bb78;
            stroke-width: 3px;
        }

        .legend {
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: rgba(20, 20, 20, 0.9);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #333;
        }

        .legend-item {
            margin: 5px 0;
            display: flex;
            align-items: center;
        }

        .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
    </style>
</head>
<body>
    <div id="controls">
        <h2>Knowledge Graph</h2>
        <label><input type="checkbox" id="showConcepts" checked> Show Concepts</label>
        <label><input type="checkbox" id="showFiles" checked> Show Files</label>
        <label><input type="checkbox" id="showReflections" checked> Show Reflections</label>
        <label><input type="checkbox" id="showLabels" checked> Show Labels</label>
    </div>

    <div id="info">
        <h3 id="infoTitle"></h3>
        <div id="infoContent"></div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #4a9eff;"></div>
            <span>Concepts</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #9f7aea;"></div>
            <span>Files</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ed8936;"></div>
            <span>Reflections</span>
        </div>
    </div>

    <svg id="graph"></svg>

    <script>
        const graphData = ''' + json.dumps(graph_data) + ''';

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g");

        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                g.attr("transform", event.transform);
            });

        svg.call(zoom);

        // Create force simulation
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.links)
                .id(d => d.id)
                .distance(d => {
                    if (d.type === 'related') return 100;
                    if (d.type === 'follows') return 80;
                    return 60;
                }))
            .force("charge", d3.forceManyBody()
                .strength(d => {
                    if (d.type === 'concept') return -300;
                    if (d.type === 'file') return -200;
                    return -100;
                }))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));

        // Create links
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.links)
            .join("line")
            .attr("class", d => `link ${d.type}`)
            .attr("stroke-width", d => d.weight ? Math.sqrt(d.weight) : 1);

        // Create nodes
        const node = g.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .join("g")
            .attr("class", d => `node ${d.type}`)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended))
            .on("click", showInfo);

        node.append("circle")
            .attr("r", d => {
                if (d.type === 'concept') return Math.min(5 + d.count * 2, 20);
                if (d.type === 'file') return 12;
                return 8;
            });

        node.append("text")
            .attr("dx", 15)
            .attr("dy", 4)
            .text(d => d.label);

        // Update simulation
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // Controls
        d3.select("#showConcepts").on("change", function() {
            node.filter(d => d.type === 'concept').style("display", this.checked ? null : "none");
        });

        d3.select("#showFiles").on("change", function() {
            node.filter(d => d.type === 'file').style("display", this.checked ? null : "none");
        });

        d3.select("#showReflections").on("change", function() {
            node.filter(d => d.type === 'reflection').style("display", this.checked ? null : "none");
        });

        d3.select("#showLabels").on("change", function() {
            node.selectAll("text").style("display", this.checked ? null : "none");
        });

        // Info panel
        function showInfo(event, d) {
            node.classed("selected", n => n === d);

            const info = d3.select("#info");
            info.style("display", "block");

            d3.select("#infoTitle").text(d.label);

            let content = `<p><strong>Type:</strong> ${d.type}</p>`;

            if (d.count) content += `<p><strong>Mentions:</strong> ${d.count}</p>`;
            if (d.timestamp) content += `<p><strong>Time:</strong> ${d.timestamp}</p>`;
            if (d.text) content += `<p>${d.text}</p>`;
            if (d.path) content += `<p><strong>Path:</strong> ${d.path}</p>`;

            // Show connections
            const connections = graphData.links.filter(l =>
                l.source.id === d.id || l.target.id === d.id
            );
            content += `<p><strong>Connections:</strong> ${connections.length}</p>`;

            d3.select("#infoContent").html(content);
        }

        // Drag functions
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        // Click outside to deselect
        svg.on("click", function(event) {
            if (event.target === this) {
                node.classed("selected", false);
                d3.select("#info").style("display", "none");
            }
        });
    </script>
</body>
</html>'''
    return html_template

def show_stats(graph_data):
    """Display graph statistics"""
    nodes_by_type = defaultdict(int)
    links_by_type = defaultdict(int)

    for node in graph_data['nodes']:
        nodes_by_type[node['type']] += 1

    for link in graph_data['links']:
        links_by_type[link['type']] += 1

    print("\n📊 Knowledge Graph Statistics\n")
    print("=" * 60)
    print(f"Total nodes: {len(graph_data['nodes'])}")
    print(f"Total links: {len(graph_data['links'])}")
    print("\nNodes by type:")
    for node_type, count in sorted(nodes_by_type.items()):
        print(f"  {node_type}: {count}")
    print("\nLinks by type:")
    for link_type, count in sorted(links_by_type.items()):
        print(f"  {link_type}: {count}")

    # Find most connected nodes
    connection_counts = defaultdict(int)
    for link in graph_data['links']:
        connection_counts[link['source']] += 1
        connection_counts[link['target']] += 1

    top_connected = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\nMost connected nodes:")
    for node_idx, count in top_connected:
        if node_idx < len(graph_data['nodes']):
            node = graph_data['nodes'][node_idx]
            print(f"  {node['label']} ({node['type']}): {count} connections")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    if command == "generate":
        print("Building knowledge graph...")
        graph_data = build_graph_data()
        html = generate_html(graph_data)

        with open(OUTPUT_FILE, 'w') as f:
            f.write(html)

        print(f"\n✅ Knowledge graph generated: {OUTPUT_FILE}")
        print(f"   Open in browser: file://{OUTPUT_FILE}")

    elif command == "data":
        print("Extracting graph data...")
        graph_data = build_graph_data()
        print(json.dumps(graph_data, indent=2))

    elif command == "stats":
        graph_data = build_graph_data()
        show_stats(graph_data)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == "__main__":
    main()
