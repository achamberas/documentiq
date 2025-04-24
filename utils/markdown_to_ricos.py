import mistune
import uuid
import json

def generate_id():
    return uuid.uuid4().hex[:10]

markdown = mistune.create_markdown(renderer='ast')

def convert_markdown_to_ricos(md_text):
    ast = markdown(md_text)
    ricos_nodes = []

    for item in ast:
        t = item['type']
        if t == 'heading':
            ricos_nodes.append({
                "type": "HEADING",
                "id": generate_id(),
                "nodes": build_text_nodes(item.get('children', [])),
                "headingData": {
                    "level": item.get('attrs', {}).get('level', 1) + 1,
                    "textStyle": {"textAlignment": "AUTO"}
                }
            })
            ricos_nodes.append(empty_para())

        elif t == 'paragraph':
            ricos_nodes.append({
                "type": "PARAGRAPH",
                "id": generate_id(),
                "nodes": build_text_nodes(item.get('children', [])),
                "paragraphData": {}
            })

        elif t == 'thematic_break':
            ricos_nodes.append(empty_para())
            ricos_nodes.append(divider_node())

    ricos_nodes.append(empty_para())
    ricos_nodes.append(empty_para())

    return {"richContent": {"nodes": ricos_nodes, "documentStyle": {}}}

def build_text_nodes(children, decorations=None):
    if decorations is None:
        decorations = []
    nodes = []
    for child in children:
        t = child['type']
        if t == 'text':
            nodes.append({
                "type": "TEXT",
                "id": "",
                "nodes": [],
                "textData": {
                    "text": child.get('raw', ''),
                    "decorations": decorations.copy()
                }
            })
        elif t == 'strong':
            nodes.extend(build_text_nodes(child.get('children', []), decorations + [{"type": "BOLD"}]))
        elif t == 'emphasis':
            nodes.extend(build_text_nodes(child.get('children', []), decorations + [{"type": "ITALIC"}]))
        elif t == 'link':
            url = child.get('attrs', {}).get('url', '').replace("https://", "").replace("http://", "")
            link_decorations = decorations + [
                {"type": "LINK", "linkData": {"link": {"url": url, "target": "BLANK", "rel": {"noreferrer": True}}}},
                {"type": "UNDERLINE"}
            ]
            nodes.extend(build_text_nodes(child.get('children', []), link_decorations))
    return nodes

def empty_para():
    return {"type": "PARAGRAPH", "id": generate_id(), "nodes": [], "paragraphData": {}}

def divider_node():
    return {
        "type": "DIVIDER",
        "id": generate_id(),
        "nodes": [],
        "dividerData": {
            "containerData": {
                "width": {}, "alignment": "CENTER", "spoiler": {}, "height": {}, "textWrap": False
            },
            "lineStyle": "SINGLE",
            "width": "LARGE",
            "alignment": "CENTER"
        }
    }
