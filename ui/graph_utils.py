import tempfile
import os

"""
Utilities for enhancing PyVis graph HTML with custom JavaScript
"""


def get_base_html_from_network(net):
    """
    Generate HTML string from PyVis network without saving to disk.

    Args:
        net: PyVis Network instance

    Returns:
        str: Complete HTML document as string
    """
    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        temp_path = f.name

    try:
        net.save_graph(temp_path)
        with open(temp_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return html_content


def inject_custom_js(html_content, js_code):
    """
    Inject custom JavaScript into HTML before </body> tag.

    Args:
        html_content: Original HTML string
        js_code: JavaScript code to inject (without <script> tags)

    Returns:
        str: Modified HTML with injected JS
    """
    js_wrapped = f"\n<script type='text/javascript'>\n{js_code}\n</script>\n"

    # Find </body> tag (case-insensitive)
    insertion_point = html_content.lower().rfind("</body>")

    if insertion_point != -1:
        return (
            html_content[:insertion_point] + js_wrapped + html_content[insertion_point:]
        )
    else:
        # Fallback: append at end
        return html_content + js_wrapped
    
def get_delete_node_js():
    """
    Returns JavaScript code that enables right-click to delete nodes.
    Deletion is visual only (client-side).
    """
    return """
    // Wait for network to be ready
    (function() {
        function initDeleteFeature() {
            try {
                // PyVis exposes the network as a global variable
                var network = window.network;
                if (!network) {
                    console.warn('Network not found, retrying...');
                    setTimeout(initDeleteFeature, 100);
                    return;
                }
                
                console.log('Delete feature initialized');
                
                // Track deleted nodes for potential undo feature
                window.deletedNodes = window.deletedNodes || [];
                
                // Right-click handler
                network.on('oncontext', function(params) {
                    // Prevent browser context menu
                    if (params.event && params.event.srcEvent) {
                        params.event.srcEvent.preventDefault();
                    }
                    
                    // Get node at click position
                    var nodeId = network.getNodeAt(params.pointer.DOM);
                    
                    if (nodeId !== undefined && nodeId !== null) {
                        console.log('Deleting node:', nodeId);
                        
                        // Get references to data stores
                        var nodesDS = network.body.data.nodes;
                        var edgesDS = network.body.data.edges;
                        
                        // Store node data before deletion (for potential undo)
                        var nodeData = nodesDS.get(nodeId);
                        var connectedEdges = network.getConnectedEdges(nodeId);
                        var edgeData = edgesDS.get(connectedEdges);
                        
                        window.deletedNodes.push({
                            node: nodeData,
                            edges: edgeData
                        });
                        
                        // Remove node (this automatically removes connected edges in Vis.js)
                        nodesDS.remove({id: nodeId});
                        
                        // Explicitly remove edges to be safe
                        if (connectedEdges && connectedEdges.length > 0) {
                            edgesDS.remove(connectedEdges);
                        }
                        
                        console.log('Node deleted successfully');
                    }
                });
                
                // Add visual hint
                addHint('Right-click a node to remove it from view');
                
            } catch(e) {
                console.error('Error initializing delete feature:', e);
            }
        }
        
        function addHint(text) {
            var hint = document.createElement('div');
            hint.id = 'graph-hint';
            hint.style.cssText = `
                position: absolute;
                right: 12px;
                bottom: 12px;
                padding: 8px 12px;
                background: rgba(0, 0, 0, 0.75);
                color: #fff;
                font: 12px/1.4 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                border-radius: 6px;
                z-index: 9999;
                pointer-events: none;
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            `;
            hint.textContent = text;
            document.body.appendChild(hint);
        }
        
        // Start initialization when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initDeleteFeature);
        } else {
            initDeleteFeature();
        }
    })();
    """