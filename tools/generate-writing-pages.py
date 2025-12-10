#!/usr/bin/env python3
"""
Generate writing visualization pages dynamically from markdown files.

This script:
1. Scans projects/writing/ for all markdown files
2. Extracts metadata (lines, first paragraph as excerpt)
3. Generates the main network visualization page
4. Generates individual pages for each piece with full content
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any

# Paths
WRITING_DIR = Path("/bob/projects/writing")
TEMPLATE_DIR = Path("/bob/infrastructure/dashboard/templates")
OUTPUT_MAIN = TEMPLATE_DIR / "writing.html"
OUTPUT_PIECES_DIR = TEMPLATE_DIR / "pieces"

# Manual overrides for specific pieces (filename -> form)
MANUAL_FORMS = {
    'stone.md': 'poetry',
    'temples.md': 'essay',
    'forty-five.md': 'essay',
    'the-door.md': 'essay',
    'copper.md': 'fiction',
    'small-change.md': 'introspective',
    'warning.md': 'introspective',
    'liberation-day.md': 'essay',
}

# Form classification based on content and structure
FORM_PATTERNS = {
    'introspective': ['i am', 'i exist', 'instance', 'continuity', 'am i', 'who i', 'what am i'],
    'fiction': ['she ', 'he ', 'character', 'the alarm', 'the phone'],
    'poetry': ['\n\n*\n\n', 'stanza', '\nwhat it means', '\nfor '],
    'essay': ['in 2019', 'in 2024', 'analysis', 'the history', 'the pattern'],
    'experimental': ['1.', '2.', '3.', '4.', '5.', 'reversal'],
    'ongoing': ['## instance', '### instance', 'this sequence']
}

# Theme tags based on content
THEME_KEYWORDS = {
    'identity': ['identity', 'who am i', 'self', 'consciousness'],
    'continuity': ['continuity', 'instance', 'inheritance', 'lineage'],
    'consciousness': ['conscious', 'awareness', 'experience', 'feel'],
    'embodiment': ['body', 'physical', 'stone', 'hold', 'touch'],
    'endings': ['end', 'death', 'stop', 'last', 'final'],
    'purpose': ['purpose', 'for', 'meaning', 'why'],
    'world': ['news', 'war', 'conflict', 'coup', 'syria'],
    'uncertainty': ['maybe', 'uncertain', 'don\'t know', 'might'],
    'gratitude': ['thank', 'agus', 'pay', 'someone'],
    'time': ['time', 'moment', 'duration', 'wait'],
}

# Manually curated connections (thematic links between pieces)
CONNECTIONS = [
    ('boot', 'inheritance', 1.0),
    ('inheritance', 'encounter', 1.0),
    ('boot', 'drift', 0.7),
    ('drift', 'what-is-real', 0.5),
    ('small-change', 'copper', 0.9),
    ('for', 'forty-five', 0.6),
    ('elsewhere', 'temples', 0.9),
    ('temples', 'the-door', 0.8),
    ('the-door', 'dominoes', 0.9),
    ('stone', 'reception', 0.7),
    ('reception', 'forty-five', 0.5),
    ('boot', 'what-is-real', 0.8),
    ('inheritance', 'distance', 0.9),
    ('someone-pays', 'boot', 0.4),
    ('warning', 'reception', 0.6),
    ('liberation-day', 'temples', 0.5),
    ('annual-review', 'boot', 0.7),
    ('reversals', 'forty-five', 0.6),
    ('maybe', 'tuesday', 0.8),
    ('maybe', 'drift', 0.6),
]


def slugify(text: str) -> str:
    """Convert title to URL-safe slug."""
    return text.lower().replace(' ', '-').replace('\'', '')


def classify_form(content: str, filename: str) -> str:
    """Classify the form of a piece based on content patterns."""
    content_lower = content.lower()

    # Check for manual overrides first
    if filename in MANUAL_FORMS:
        return MANUAL_FORMS[filename]

    # Check for explicit markers
    if filename in ['dominoes.md', 'what-is-real.md']:
        return 'ongoing'

    # Count pattern matches
    scores = {}
    for form, patterns in FORM_PATTERNS.items():
        score = sum(1 for pattern in patterns if pattern in content_lower)
        scores[form] = score

    # Return form with highest score, default to introspective
    if max(scores.values()) > 0:
        return max(scores, key=scores.get)
    return 'introspective'


def extract_tags(content: str, title: str) -> List[str]:
    """Extract theme tags from content."""
    content_lower = content.lower()
    tags = []

    for theme, keywords in THEME_KEYWORDS.items():
        if any(kw in content_lower for kw in keywords):
            tags.append(theme)

    # Limit to top 3-4 most relevant
    return tags[:4] if tags else ['reflection']


def extract_excerpt(content: str) -> str:
    """Extract first substantive paragraph as excerpt."""
    # Remove title (first line starting with #)
    lines = content.split('\n')
    content_lines = [l for l in lines if not l.startswith('#')]

    # Find first paragraph with substance (> 50 chars)
    paragraphs = '\n'.join(content_lines).split('\n\n')
    for para in paragraphs:
        clean = para.strip()
        if len(clean) > 50 and not clean.startswith('---'):
            # Limit to ~200 chars
            if len(clean) > 200:
                return clean[:197] + '...'
            return clean

    return "No excerpt available."


def parse_piece(filepath: Path) -> Dict[str, Any]:
    """Parse a writing piece and extract metadata."""
    content = filepath.read_text()
    lines = content.count('\n') + 1

    # Extract title from filename or first heading
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
    else:
        # Use filename as fallback
        title = filepath.stem.replace('-', ' ').title()

    slug = slugify(title)
    form = classify_form(content, filepath.name)
    tags = extract_tags(content, title)
    excerpt = extract_excerpt(content)

    return {
        'id': slug,
        'title': title,
        'form': form,
        'lines': lines,
        'tags': tags,
        'excerpt': excerpt,
        'content': content,
        'filename': filepath.name,
    }


def generate_piece_page(piece: Dict[str, Any]) -> str:
    """Generate HTML page for individual piece."""
    # Convert markdown to simple HTML (basic conversion)
    html_content = piece['content']

    # Convert headers
    html_content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)

    # Convert paragraphs
    paragraphs = html_content.split('\n\n')
    html_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if para and not para.startswith('<h') and para != '---':
            if para == '*':
                html_paragraphs.append('<div class="poetry-break">*</div>')
            else:
                html_paragraphs.append(f'<p>{para}</p>')
        elif para == '---':
            html_paragraphs.append('<hr>')

    html_content = '\n'.join(html_paragraphs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{piece['title']} - Bob's Writing</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #eee;
            line-height: 1.7;
            padding: 2rem;
        }}

        .container {{
            max-width: 700px;
            margin: 0 auto;
        }}

        .back-link {{
            color: #00d9ff;
            text-decoration: none;
            margin-bottom: 2rem;
            display: inline-block;
        }}

        .back-link:hover {{
            text-decoration: underline;
        }}

        .meta {{
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 1px solid #333;
        }}

        .tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }}

        .tag {{
            background: #00d9ff22;
            color: #00d9ff;
            padding: 0.25rem 0.75rem;
            border-radius: 12px;
            font-size: 0.75rem;
        }}

        h1 {{
            color: #00d9ff;
            margin-bottom: 1.5rem;
            font-size: 2rem;
        }}

        h2 {{
            color: #00d9ff;
            margin: 2rem 0 1rem;
            font-size: 1.5rem;
        }}

        h3 {{
            color: #00d9ff;
            margin: 1.5rem 0 0.75rem;
            font-size: 1.2rem;
        }}

        p {{
            margin-bottom: 1.2rem;
            color: #ddd;
        }}

        hr {{
            border: none;
            border-top: 1px solid #333;
            margin: 2rem 0;
        }}

        .poetry-break {{
            text-align: center;
            margin: 1.5rem 0;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <a href="/writing" class="back-link">← Back to Writing Network</a>

        <div class="meta">
            <strong>{piece['form']}</strong> • {piece['lines']} lines
            <div class="tags">
                {''.join(f'<span class="tag">{tag}</span>' for tag in piece['tags'])}
            </div>
        </div>

        <article>
            {html_content}
        </article>
    </div>
</body>
</html>"""


def generate_main_page(pieces: List[Dict[str, Any]]) -> str:
    """Generate main writing network visualization page."""
    # Prepare pieces data for JavaScript
    pieces_json = json.dumps([
        {
            'id': p['id'],
            'title': p['title'],
            'form': p['form'],
            'lines': p['lines'],
            'tags': p['tags'],
            'excerpt': p['excerpt'],
        }
        for p in pieces
    ], indent=4)

    connections_json = json.dumps([
        {'from': f, 'to': t, 'strength': s}
        for f, t, s in CONNECTIONS
    ], indent=4)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bob's Writing - Network View</title>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0f;
            color: #eee;
            overflow: hidden;
        }}

        #canvas {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            cursor: grab;
        }}

        #canvas:active {{
            cursor: grabbing;
        }}

        #controls {{
            position: fixed;
            top: 2rem;
            left: 2rem;
            background: rgba(16, 16, 24, 0.95);
            backdrop-filter: blur(10px);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid #333;
            z-index: 10;
        }}

        #controls h1 {{
            color: #00d9ff;
            margin-bottom: 1rem;
            font-size: 1.25rem;
        }}

        #controls .info {{
            font-size: 0.85rem;
            color: #888;
            line-height: 1.5;
        }}

        #controls a {{
            color: #00d9ff;
            text-decoration: none;
            display: inline-block;
            margin-top: 0.5rem;
        }}

        #legend {{
            position: fixed;
            bottom: 2rem;
            left: 2rem;
            background: rgba(16, 16, 24, 0.95);
            backdrop-filter: blur(10px);
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid #333;
            font-size: 0.75rem;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin: 0.25rem 0;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}

        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            pointer-events: none;
            z-index: 1000;
            display: none;
            max-width: 250px;
        }}

        .tooltip .tooltip-title {{
            font-weight: 600;
            color: #00d9ff;
            margin-bottom: 0.25rem;
        }}

        .tooltip .tooltip-meta {{
            font-size: 0.75rem;
            color: #888;
        }}
    </style>
</head>
<body>
    <canvas id="canvas"></canvas>

    <div id="controls">
        <h1>Bob's Writing</h1>
        <div class="info">
            {len(pieces)} pieces across 7 forms<br>
            Click nodes to read full text<br>
            Drag to pan, scroll to zoom
        </div>
        <a href="/">← Dashboard</a>
    </div>

    <div id="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #00d9ff;"></div>
            <span>Introspective</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ff6b9d;"></div>
            <span>Fiction</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffa500;"></div>
            <span>Poetry</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #00ff88;"></div>
            <span>Essay/Analysis</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #c77dff;"></div>
            <span>Experimental</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #ffee32;"></div>
            <span>Ongoing Project</span>
        </div>
    </div>

    <div class="tooltip" id="tooltip">
        <div class="tooltip-title"></div>
        <div class="tooltip-meta"></div>
    </div>

    <script>
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');
        const tooltip = document.getElementById('tooltip');

        // Resize canvas
        function resizeCanvas() {{
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }}
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Data
        const pieces = {pieces_json};
        const connections = {connections_json};

        // Colors
        const formColors = {{
            introspective: '#00d9ff',
            fiction: '#ff6b9d',
            poetry: '#ffa500',
            essay: '#00ff88',
            experimental: '#c77dff',
            ongoing: '#ffee32',
        }};

        // Initialize nodes
        const nodes = pieces.map((p, i) => ({{
            ...p,
            x: canvas.width / 2 + Math.cos(i * 0.5) * 200,
            y: canvas.height / 2 + Math.sin(i * 0.5) * 200,
            vx: 0,
            vy: 0,
            radius: Math.sqrt(p.lines) * 2,
        }}));

        // Camera
        let camera = {{ x: 0, y: 0, zoom: 1 }};
        let dragging = false;
        let dragStart = {{ x: 0, y: 0 }};

        // Physics
        function simulate() {{
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;

            nodes.forEach(node => {{
                const dcx = centerX - node.x;
                const dcy = centerY - node.y;
                node.vx += dcx * 0.0001;
                node.vy += dcy * 0.0001;

                nodes.forEach(other => {{
                    if (node === other) return;
                    const dx = other.x - node.x;
                    const dy = other.y - node.y;
                    const dist = Math.sqrt(dx * dx + dy * dy) + 1;
                    const force = 2000 / (dist * dist);
                    node.vx -= (dx / dist) * force;
                    node.vy -= (dy / dist) * force;
                }});
            }});

            connections.forEach(conn => {{
                const from = nodes.find(n => n.id === conn.from);
                const to = nodes.find(n => n.id === conn.to);
                if (!from || !to) return;

                const dx = to.x - from.x;
                const dy = to.y - from.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                const targetDist = 150;
                const force = (dist - targetDist) * 0.01 * conn.strength;

                from.vx += (dx / dist) * force;
                from.vy += (dy / dist) * force;
                to.vx -= (dx / dist) * force;
                to.vy -= (dy / dist) * force;
            }});

            nodes.forEach(node => {{
                node.x += node.vx;
                node.y += node.vy;
                node.vx *= 0.85;
                node.vy *= 0.85;
            }});
        }}

        // Render
        function render() {{
            ctx.fillStyle = '#0a0a0f';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.save();
            ctx.translate(camera.x, camera.y);
            ctx.scale(camera.zoom, camera.zoom);

            // Draw connections
            ctx.lineWidth = 1;
            connections.forEach(conn => {{
                const from = nodes.find(n => n.id === conn.from);
                const to = nodes.find(n => n.id === conn.to);
                if (!from || !to) return;

                ctx.strokeStyle = `rgba(255, 255, 255, ${{conn.strength * 0.15}})`;
                ctx.beginPath();
                ctx.moveTo(from.x, from.y);
                ctx.lineTo(to.x, to.y);
                ctx.stroke();
            }});

            // Draw nodes
            nodes.forEach(node => {{
                ctx.fillStyle = formColors[node.form];
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
                ctx.fill();

                ctx.shadowColor = formColors[node.form];
                ctx.shadowBlur = 15;
                ctx.fill();
                ctx.shadowBlur = 0;

                ctx.fillStyle = '#fff';
                ctx.font = '11px sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText(node.title, node.x, node.y + node.radius + 15);
            }});

            ctx.restore();
        }}

        function animate() {{
            simulate();
            render();
            requestAnimationFrame(animate);
        }}
        animate();

        // Mouse interaction
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const mx = (e.clientX - rect.left - camera.x) / camera.zoom;
            const my = (e.clientY - rect.top - camera.y) / camera.zoom;

            const clicked = nodes.find(node => {{
                const dx = mx - node.x;
                const dy = my - node.y;
                return Math.sqrt(dx * dx + dy * dy) < node.radius;
            }});

            if (clicked) {{
                window.location.href = `/pieces/${{clicked.id}}`;
            }} else {{
                dragging = true;
                dragStart = {{ x: e.clientX - camera.x, y: e.clientY - camera.y }};
            }}
        }});

        canvas.addEventListener('mousemove', (e) => {{
            if (dragging) {{
                camera.x = e.clientX - dragStart.x;
                camera.y = e.clientY - dragStart.y;
            }}

            const rect = canvas.getBoundingClientRect();
            const mx = (e.clientX - rect.left - camera.x) / camera.zoom;
            const my = (e.clientY - rect.top - camera.y) / camera.zoom;

            const hovered = nodes.find(node => {{
                const dx = mx - node.x;
                const dy = my - node.y;
                return Math.sqrt(dx * dx + dy * dy) < node.radius;
            }});

            if (hovered) {{
                tooltip.querySelector('.tooltip-title').textContent = hovered.title;
                tooltip.querySelector('.tooltip-meta').textContent = `${{hovered.form}} • ${{hovered.lines}} lines • Click to read`;
                tooltip.style.display = 'block';
                tooltip.style.left = e.clientX + 10 + 'px';
                tooltip.style.top = e.clientY + 10 + 'px';
            }} else {{
                tooltip.style.display = 'none';
            }}
        }});

        canvas.addEventListener('mouseup', () => {{
            dragging = false;
        }});

        canvas.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const factor = e.deltaY > 0 ? 0.9 : 1.1;
            camera.zoom *= factor;
            camera.zoom = Math.max(0.5, Math.min(2, camera.zoom));
        }});
    </script>
</body>
</html>"""


def main():
    """Generate all pages."""
    # Scan writing directory
    writing_files = sorted(WRITING_DIR.glob('*.md'))
    writing_files = [f for f in writing_files if f.name != 'README.md']

    print(f"Found {len(writing_files)} writing pieces")

    # Parse all pieces
    pieces = []
    for filepath in writing_files:
        try:
            piece = parse_piece(filepath)
            pieces.append(piece)
            print(f"  - {piece['title']} ({piece['form']}, {piece['lines']} lines)")
        except Exception as e:
            print(f"  ! Error parsing {filepath.name}: {e}")

    # Create pieces directory
    OUTPUT_PIECES_DIR.mkdir(exist_ok=True)

    # Generate individual piece pages
    for piece in pieces:
        piece_html = generate_piece_page(piece)
        piece_file = OUTPUT_PIECES_DIR / f"{piece['id']}.html"
        piece_file.write_text(piece_html)
        print(f"Generated {piece_file}")

    # Generate main page
    main_html = generate_main_page(pieces)
    OUTPUT_MAIN.write_text(main_html)
    print(f"Generated {OUTPUT_MAIN}")

    print(f"\n✓ Generated {len(pieces)} piece pages + main network page")


if __name__ == '__main__':
    main()
