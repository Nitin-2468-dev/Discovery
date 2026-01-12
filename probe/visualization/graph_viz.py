try:
    import networkx as nx
except Exception:
    nx = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

# Optional plotting/export dependencies - import if available, otherwise keep None.
try:
    import pydot
except Exception:
    pydot = None

try:
    import kaleido
except Exception:
    kaleido = None

from typing import Optional, TYPE_CHECKING
from probe.core.map import Map
import json

if TYPE_CHECKING:
    # Type checkers can resolve these when available; these imports are optional at runtime.
    try:  # pragma: no cover - only for static analysis
        import pydot  # type: ignore
        import kaleido  # type: ignore
    except Exception:
        pass

class GraphVisualizer:
    """Visualize the Probe knowledge graph using NetworkX + Plotly.

    Features:
    - build_graph(entity_name=None, depth=2)
    - plot_interactive(output_path='graph.html')
    - export_to_gephi(output_path='graph.gexf')
    - export_dot(output_path='graph.dot')
    - get_stats()

    If `networkx` or `plotly` are not available, a minimal fallback will
    produce a simple HTML listing nodes and edges so the CLI remains usable
    in minimal environments (CI or systems without plotting libs).
    """

    def __init__(self, map_obj: Map):
        self.map = map_obj
        if nx:
            self.G = nx.DiGraph()
        else:
            # simple fallback representation
            self.G = {"nodes": {}, "edges": []}

    def _add_node(self, nid, **attrs):
        if nx:
            self.G.add_node(nid, **attrs)
        else:
            if nid not in self.G["nodes"]:
                self.G["nodes"][nid] = attrs

    def _add_edge(self, a, b, **attrs):
        if nx:
            self.G.add_edge(a, b, **attrs)
        else:
            self.G["edges"].append((a, b, attrs))

    def build_graph(self, entity_name: Optional[str] = None, depth: int = 2):
        if entity_name:
            ent = self.map.get_entity(entity_name)
            if not ent:
                return
            self._add_entity_subgraph(ent, depth)
        else:
            self._add_all_nodes()

    def _add_entity_subgraph(self, entity, depth, current_depth=0):
        if current_depth > depth:
            return

        ent_id = f"entity_{entity.id}"
        self._add_node(ent_id, type="entity", name=entity.name, label=entity.name, color="#FF6B6B")

        # documents
        docs = self.map.get_entity_documents(entity.name)
        for d in docs:
            doc_id = f"doc_{d.id}"
            self._add_node(doc_id, type="document", name=d.title, label=f"{d.doc_type}: {d.title[:30]}", color="#4ECDC4")
            self._add_edge(ent_id, doc_id, relation="has_document")

        # related entities
        related = self.map.get_related_entities(entity.name)
        for r in related:
            r_id = f"entity_{r.id}"
            if nx:
                if r_id not in self.G:
                    self._add_node(r_id, type="entity", name=r.name, label=r.name, color="#FF6B6B")
                    if current_depth < depth:
                        self._add_entity_subgraph(r, depth, current_depth + 1)
            else:
                if r_id not in self.G["nodes"]:
                    self._add_node(r_id, type="entity", name=r.name, label=r.name, color="#FF6B6B")
                    if current_depth < depth:
                        self._add_entity_subgraph(r, depth, current_depth + 1)
            self._add_edge(ent_id, r_id, relation="related_to")

    def _add_all_nodes(self):
        cur = self.map.conn.cursor()
        cur.execute("SELECT id, name FROM entities")
        for row in cur.fetchall():
            nid = f"entity_{row['id']}"
            self._add_node(nid, type='entity', name=row['name'], label=row['name'], color="#FF6B6B")

        cur.execute("SELECT id, title, doc_type FROM documents")
        for row in cur.fetchall():
            nid = f"doc_{row['id']}"
            self._add_node(nid, type='document', name=row['title'], label=f"{row['doc_type']}: {row['title'][:30]}", color="#4ECDC4")

        cur.execute("SELECT * FROM edges")
        for row in cur.fetchall():
            from_id = f"{row['from_type']}_{row['from_id']}"
            to_id = f"{row['to_type']}_{row['to_id']}"
            self._add_edge(from_id, to_id, relation=row['relation'])

    def plot_interactive(self, output_path: str = "graph.html") -> str:
        # Lazy import: if plotting libs weren't available at module import time, try now.
        global nx, go
        try:
            if nx is None:
                import importlib
                nx = importlib.import_module('networkx')
        except Exception:
            nx = None

        try:
            if go is None:
                import importlib
                go = importlib.import_module('plotly.graph_objects')
        except Exception:
            go = None

        # If we have upgraded to networkx after a fallback, convert the fallback graph to a NetworkX graph
        if nx and not isinstance(self.G, nx.DiGraph):
            G_new = nx.DiGraph()
            # nodes stored in self.G['nodes'] and edges in self.G['edges']
            for nid, attrs in self.G.get('nodes', {}).items():
                G_new.add_node(nid, **attrs)
            for a, b, attrs in self.G.get('edges', []):
                G_new.add_edge(a, b, **(attrs or {}))
            self.G = G_new

        # If plotly/networkx are available, render a force layout interactive graph.
        if nx and go:
            pos = nx.spring_layout(self.G, k=0.5, iterations=50)

            edge_x = []
            edge_y = []
            edge_annotations = []  # (a,b,relation,mid_x,mid_y)

            for a, b, edata in self.G.edges(data=True):
                if a not in pos or b not in pos:
                    continue
                x0, y0 = pos[a]
                x1, y1 = pos[b]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                rel = edata.get('relation') if isinstance(edata, dict) else edata
                mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
                edge_annotations.append((a, b, rel, mx, my))

            edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=0.5, color='#888'), hoverinfo='none', mode='lines')

            node_x = []
            node_y = []
            node_color = []
            node_text = []
            node_hover = []
            node_size = []

            for node in self.G.nodes(data=True):
                n_id = node[0]
                nd = node[1]
                if n_id not in pos:
                    continue
                x, y = pos[n_id]
                node_x.append(x)
                node_y.append(y)
                node_color.append(nd.get('color', '#888'))
                label = nd.get('label', n_id)
                node_text.append(label)
                # hover text: include name, type and optional extra metadata
                hover_info = {'name': nd.get('name'), 'type': nd.get('type')}
                hover_info.update({k: v for k, v in nd.items() if k not in ('name', 'type', 'label', 'color')})
                node_hover.append(json.dumps(hover_info))
                deg = self.G.degree(n_id)
                node_size.append(10 + deg * 6)

            # Node scatter with hover text showing label + metadata
            node_trace = go.Scatter(
                x=node_x,
                y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=node_text,
                textposition='top center',
                hovertext=node_hover,
                marker=dict(color=node_color, size=node_size, line=dict(width=2, color='white'))
            )

            # Create edge labels as annotations at the midpoints
            annotations = []
            for ea, eb, etext, ex, ey in edge_annotations:
                if etext:
                    annotations.append(dict(x=ex, y=ey, xref='x', yref='y', text=str(etext), showarrow=False, font=dict(size=10, color='#333')))

            # Legend entries (create dummy traces)
            entity_legend = go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color='#FF6B6B'), name='Entity')
            doc_legend = go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color='#4ECDC4'), name='Document')
            page_legend = go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=12, color='#FFD166'), name='Page')

            fig = go.Figure(data=[edge_trace, node_trace, entity_legend, doc_legend, page_legend], layout=go.Layout(title='Probe Knowledge Graph', showlegend=True, hovermode='closest', margin=dict(b=0, l=0, r=0, t=40), xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False), annotations=annotations))

            fig.write_html(output_path)
            # store the figure for potential export
            self._last_fig = fig
            return output_path

        # Fallback: generate an interactive D3 force-directed graph HTML (no python plotting deps)
        nodes = []
        links = []
        if nx:
            for n, attr in self.G.nodes(data=True):
                nodes.append({"id": n, **attr})
            for a, b, attr in self.G.edges(data=True):
                links.append({"source": a, "target": b, "relation": attr.get("relation") if isinstance(attr, dict) else attr})
        else:
            for nid, attrs in self.G["nodes"].items():
                nodes.append({"id": nid, **attrs})
            for a, b, attrs in self.G["edges"]:
                links.append({"source": a, "target": b, "relation": attrs.get("relation") if isinstance(attrs, dict) else attrs})

        data = {"nodes": nodes, "links": links}

        template = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Probe Knowledge Graph (interactive)</title>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    body { margin: 0; font-family: sans-serif; }
    svg { width: 100vw; height: 90vh; background: #f3f7fb; }
    .node circle { stroke: #fff; stroke-width: 1.5px; }
    .node text { font-size: 12px; pointer-events: none; }
    .link { stroke: #999; stroke-opacity: 0.6; }
    .tooltip { position: absolute; background: white; border: 1px solid #ccc; padding: 6px; font-size: 12px; display: none; }
  </style>
</head>
<body>
  <h3 style="margin:8px 12px">Probe Knowledge Graph</h3>
  <div id="chart"></div>
  <div id="tooltip" class="tooltip"></div>
  <script>
    const data = __DATA_JSON__;
    const width = window.innerWidth;
    const height = window.innerHeight * 0.8;

    const svg = d3.select('#chart').append('svg')
      .attr('width', width)
      .attr('height', height);

    const link = svg.append('g')
        .attr('class', 'links')
      .selectAll('line')
      .data(data.links)
      .enter().append('line')
        .attr('class','link')
        .attr('stroke-width', 1);

    const node = svg.append('g')
        .attr('class', 'nodes')
      .selectAll('g')
      .data(data.nodes)
      .enter().append('g')
        .attr('class','node')
        .call(d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended));

    node.append('circle')
        .attr('r', d => Math.max(6, (d.degree || 0) * 2 + 6))
        .attr('fill', d => d.color || '#888')

    node.append('text')
        .attr('x', 8)
        .attr('y', 3)
        .text(d => d.label || d.id);

    const tooltip = d3.select('#tooltip');

    node.on('mouseover', (event, d) => {
      tooltip.style('display', 'block');
      tooltip.html('<b>' + (d.label || d.id) + '</b><br/>' + (d.type ? d.type : ''))
             .style('left', (event.pageX + 8) + 'px')
             .style('top', (event.pageY + 8) + 'px');
    }).on('mouseout', () => tooltip.style('display', 'none'));

    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(80).strength(0.5))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .on('tick', ticked);

    function ticked() {
      link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

      node
          .attr('transform', d => `translate(${d.x},${d.y})`);
    }

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

    // compute degrees for sizing
    const degreeMap = {};
    data.links.forEach(l => { degreeMap[l.source] = (degreeMap[l.source] || 0) + 1; degreeMap[l.target] = (degreeMap[l.target] || 0) + 1; });
    data.nodes.forEach(n => n.degree = degreeMap[n.id] || 0);
  </script>
</body>
</html>"""

        d3_html = template.replace('__DATA_JSON__', json.dumps(data))
        with open(output_path, 'w', encoding='utf-8') as fh:
            fh.write(d3_html)

        # store a simple flag that this is a d3 export
        self._last_fig = None
        return output_path

    def export_to_gephi(self, output_path: str = "graph.gexf") -> str:
        if not nx:
            raise RuntimeError("networkx is required to export to GEXF")
        nx.write_gexf(self.G, output_path)
        return output_path

    def export_dot(self, output_path: str = "graph.dot") -> str:
        if not nx:
            # fallback: write a minimal DOT
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write('digraph G {\n')
                for n in (self.G["nodes"].keys() if not nx else self.G.nodes()):
                    fh.write(f'"{n}";\n')
                for a, b, _ in self.G["edges"]:
                    fh.write(f'"{a}" -> "{b}";\n')
                fh.write('}\n')
            return output_path
        try:
            import pydot
            nx.drawing.nx_pydot.write_dot(self.G, output_path)
        except Exception:
            # fallback: write a minimal DOT
            with open(output_path, 'w', encoding='utf-8') as fh:
                fh.write('digraph G {\n')
                for n in self.G.nodes():
                    fh.write(f'"{n}";\n')
                for a, b in self.G.edges():
                    fh.write(f'"{a}" -> "{b}";\n')
                fh.write('}\n')
        return output_path

    def export_image(self, output_path: str = "graph.png") -> str:
        """Export the latest interactive figure as a static image (PNG/SVG).

        Requires `kaleido` (pip install kaleido) or a plotly image engine.
        If no figure exists yet, `plot_interactive()` is invoked to create one.
        """
        # If we were not able to import plotly at module load, we don't strictly need it
        # here as long as a _last_fig object with write_image() exists (tests may mock it).
        if not hasattr(self, '_last_fig') or self._last_fig is None:
            # create a transient HTML/fig
            self._last_fig = None
            # Attempt to build a figure into _last_fig by calling plot_interactive to set it
            # Use a temp path so we don't overwrite user files
            tmp = "./.tmp_graph.html"
            self.plot_interactive(tmp)
            try:
                import os
                os.remove(tmp)
            except Exception:
                pass

        if not hasattr(self, '_last_fig') or self._last_fig is None:
            raise RuntimeError("No figure available to export")

        # Check for kaleido availability
        try:
            import kaleido  # noqa: F401
        except Exception:
            raise RuntimeError("To export images you must install 'kaleido' (pip install kaleido)")

        # Write the image
        self._last_fig.write_image(output_path)
        return output_path

    def get_stats(self):
        if nx:
            return {'nodes': self.G.number_of_nodes(), 'edges': self.G.number_of_edges(), 'density': nx.density(self.G), 'components': nx.number_weakly_connected_components(self.G)}
        else:
            n_nodes = len(self.G["nodes"])
            n_edges = len(self.G["edges"])
            density = (n_edges / (n_nodes * (n_nodes - 1))) if n_nodes > 1 else 0
            components = 1 if n_nodes > 0 else 0
            return {'nodes': n_nodes, 'edges': n_edges, 'density': density, 'components': components}
