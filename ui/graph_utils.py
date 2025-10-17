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