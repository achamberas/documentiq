import json
import re
import uuid
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

class MarkdownToRicosConverter:
    """
    Converts Markdown text to RICOS (Rich Content Object Storage) format.
    RICOS is a structured format for storing rich content with blocks and entities.
    """
    
    def __init__(self):
        self.block_counter = 0
    
    def generate_id(self):
        """Generate a unique key for RICOS blocks and entities."""
        return str(uuid.uuid4())
    
    def convert(self, markdown_text):
        """
        Convert markdown text to RICOS format.
        
        Args:
            markdown_text (str): The markdown text to convert
            
        Returns:
            dict: A RICOS document
        """
        # Convert markdown to HTML
        html = markdown.markdown(markdown_text, extensions=['tables', 'fenced_code'])
        
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize RICOS document structure
        ricos_doc = {
            "VERSION": "1",
            "blocks": [],
            "entityMap": {}
        }
        
        # Process elements
        for element in soup.find_all(True):
            if element.parent == soup:  # Top-level elements only
                block = self._process_element(element)
                if block:
                    ricos_doc["blocks"].append(block)
        
        return ricos_doc
    
    def _process_element(self, element):
        """Process an HTML element and convert it to a RICOS block."""
        tag_name = element.name
        
        # Handle different element types
        if tag_name == 'p':
            return self._create_paragraph_block(element)
        if tag_name == 'a':
            return self._create_hyperlink_block(element)
        elif tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            return self._create_header_block(element, int(tag_name[1]))
        elif tag_name == 'pre' and element.find('code'):
            return self._create_code_block(element)
        elif tag_name == 'ul':
            return self._create_list_block(element, 'unordered')
        elif tag_name == 'ol':
            return self._create_list_block(element, 'ordered')
        elif tag_name == 'blockquote':
            return self._create_blockquote_block(element)
        elif tag_name == 'table':
            return self._create_table_block(element)
        elif tag_name == 'hr':
            return self._create_divider_block()
        
        return None
    
    def _create_paragraph_block(self, element):
        """Create a paragraph block from a <p> element."""
        text = element.get_text()
        id = self.generate_id()
        self.block_counter += 1
        
        return {
            "type": "PARAGRAPH",
            "id": id,
            "text": text,
            "inlineStyleRanges": self._extract_inline_styles(element),
            "nodes": [],
            "paragraphData": {}
        }
    
    def _create_hyperlink_block(self, element, level):
        """Create a hyperlink from an <a> element."""
        text = element.get_text()
        url = element.get('href')
        id = self.generate_id()
        self.block_counter += 1
        
        return {
            "type": "TEXT",
            "id":id,
            "inlineStyleRanges": self._extract_inline_styles(element),
            "nodes": [],
            "textData": {
                "text": text,
                "decorations": [
                    {
                        "type": "LINK",
                        "linkData": {
                            "link": {
                                "url": url,
                                "target": "BLANK",
                                "rel": {
                                    "noreferrer": True
                                }
                            }
                        }
                    },
                    {
                        "type": "UNDERLINE"
                    }
                ]
            }
        }
    
    def _create_header_block(self, element, level):
        """Create a header block from a <h1> to <h6> element."""
        text = element.get_text()
        id = self.generate_id()
        self.block_counter += 1
        
        return {
            "type": "HEADING",
            "id":id,
            "text": text,
            "inlineStyleRanges": self._extract_inline_styles(element),
            "nodes": [],
            "headingData": {
                "level": level
            }
    }
    
    def _create_code_block(self, element):
        """Create a code block from a <pre><code> element."""
        code_element = element.find('code')
        text = code_element.get_text() if code_element else element.get_text()
        language = code_element.get('class', [''])[0] if code_element.get('class') else ''
        
        if language.startswith('language-'):
            language = language[9:]
        
        id = self.generate_id()
        self.block_counter += 1

        return {
            "type": "CODE_BLOCK",
            "id":id,
            "inlineStyleRanges": [],
            "nodes": [
                {
                    "type": "TEXT",
                    "id": "",
                    "nodes": [],
                    "textData": {
                        "text": text,
                        "decorations": []
                    }
                }                
            ],
            "codeBlockData": {
                "language": language
            }
        }
    
    def _create_blockquote_block(self, element):
        """Create a blockquote block from a <blockquote> element."""
        text = element.get_text()
        id = self.generate_id()
        self.block_counter += 1
        
        return {
            "type": "BLOCKQUOTE",
            "id":id,
            "inlineStyleRanges": [],
            "nodes": [
                {
                    "type": "TEXT",
                    "id": "",
                    "nodes": [],
                    "textData": {
                        "text": text,
                        "decorations": []
                    }
                }                
            ],
            "blockquoteData": {}
        }
    
    def _create_divider_block(self):
        """Create a divider block from a <hr> element."""
        id = self.generate_id()
        self.block_counter += 1
        
        return {
            "type": "DIVIDER",
            "id":id,
            "nodes": [],
            "inlineStyleRanges": [],
            "dividerData": {
                "containerData": {
                    "width": {},
                    "alignment": "CENTER",
                    "spoiler": {},
                    "height": {},
                    "textWrap": False
                },
                "lineStyle": "SINGLE",
                "width": "LARGE",
                "alignment": "CENTER"
            }
        }

    # TODO: fix the following two functions based on the `sample ricos document.json` file
    def _create_list_block(self, element, list_type):
        """Create a list block from a <ul> or <ol> element."""
        items = element.find_all('li', recursive=False)
        id = self.generate_id()
        self.block_counter += 1
        
        list_items = []
        for item in items:
            list_items.append({
                "text": item.get_text(),
                "inlineStyleRanges": self._extract_inline_styles(item),
                "nodes": []
            })
        
        return {
            "id":id,
            "type": "LIST",
            "text": "",
            "inlineStyleRanges": [],
            "nodes": [],
            "data": {
                "listType": list_type,
                "items": list_items
            }
        }
    
    def _create_table_block(self, element):
        """Create a table block from a <table> element."""
        id = self.generate_id()
        self.block_counter += 1
        
        rows = []
        header_row = None
        
        # Extract table header
        thead = element.find('thead')
        if thead:
            th_elements = thead.find_all('th')
            header_row = [th.get_text() for th in th_elements]
        
        # Extract table body
        tbody = element.find('tbody') or element
        tr_elements = tbody.find_all('tr')
        
        for tr in tr_elements:
            row = []
            for td in tr.find_all(['td', 'th']):
                row.append(td.get_text())
            rows.append(row)
        
        return {
            "id":id,
            "type": "TABLE",
            "text": "",
            "inlineStyleRanges": [],
            "nodes": [],
            "data": {
                "headerRow": header_row,
                "rows": rows
            }
        }
        
    def _extract_inline_styles(self, element):
        """Extract inline styles from an element."""
        styles = []
        
        # This is a simplified approach. In a real implementation, you would
        # need to find the exact character offsets for each style.
        # For now, we'll just return an empty list.
        
        return styles

