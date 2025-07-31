import os, json, sys
from lxml import etree
from lxml.etree import QName
from docx import Document
from zipfile import ZipFile

if len(sys.argv) != 2:
    print("Usage: python extract.py <input_docx>")
    sys.exit(1)

INPUT_DOCX = sys.argv[1]
OUTPUT_HTML_DIR = "journal_processing/build/pages"
OUTPUT_TXT_DIR = "journal_processing/build/txt"
OUTPUT_JSON = "journal_processing/build/data.json"
os.makedirs(OUTPUT_HTML_DIR, exist_ok=True)
os.makedirs(OUTPUT_TXT_DIR, exist_ok=True)

NAMESPACE = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
}

# Extract comments
comments = {}
doc = Document(INPUT_DOCX)
if hasattr(doc.part, "_comments_part") and doc.part._comments_part is not None:
    for c in doc.part._comments_part.comments:
        cid = str(c._element.get(f"{{{NAMESPACE['w']}}}id"))
        comments[cid] = c.text

# Parse document XML
with ZipFile(INPUT_DOCX) as docx:
    xml = docx.read('word/document.xml')

root = etree.fromstring(xml)
body = root.find('.//w:body', namespaces=NAMESPACE)
line_number = 1
page_number = 0
current_page = []
pages = []

for el in body:
    tag = QName(el).localname

    if el.find('.//w:br[@w:type="page"]', namespaces=NAMESPACE) is not None:
        if current_page:
            pages.append((page_number, current_page))
            current_page = []
            page_number += 1
        continue

    output_line = ""
    plain_line = ""
    page_comments = []
    in_comment = False
    comment_buffer = []
    comment_id = None

    if tag == 'p':
        for child in el:
            ctag = QName(child).localname

            if ctag == 'commentRangeStart':
                comment_id = child.attrib.get(f"{{{NAMESPACE['w']}}}id")
                in_comment = True
                comment_buffer = []
                continue

            if ctag == 'commentRangeEnd':
                in_comment = False
                anchor = ''.join(comment_buffer)
                output_line += f'<a class="comment-link" data-comment-id="c{comment_id}">{anchor}</a>'
                page_comments.append({
                    "id": f"c{comment_id}",
                    "text": comments.get(comment_id, "")
                })
                comment_id = None
                comment_buffer = []
                continue

            if ctag == 'r':
                text_fragments = []
                for t in child.findall('.//w:t', namespaces=NAMESPACE):
                    txt = t.text or ""
                    plain_line += txt
                    text_fragments.append(txt)
                joined = ''.join(text_fragments)
                if in_comment:
                    comment_buffer.append(joined)
                else:
                    output_line += joined

    html_line = f"<p data-line='{line_number}'>{output_line}</p>"
    current_page.append((html_line, plain_line, page_comments))
    line_number += 1

if current_page:
    pages.append((page_number, current_page))

# Write HTML, TXT and metadata, skipping page 0
metadata = []

for page_num, lines in pages:
    if page_num == 0:
        continue

    # Strip leading and trailing empty lines from page
    while lines and not lines[0][0].strip('<p data-line=>').strip('</p>'):
        lines.pop(0)
    while lines and not lines[-1][0].strip('<p data-line=>').strip('</p>'):
        lines.pop()

    html_path = os.path.join(OUTPUT_HTML_DIR, f"page_{page_num}.html")
    txt_path = os.path.join(OUTPUT_TXT_DIR, f"page_{page_num}.txt")

    comments_data = [c for _, _, cs in lines for c in cs]
    metadata.append({
        "page": page_num + 1,
        "comments": comments_data
    })

    with open(html_path, "w", encoding="utf-8") as f:
        for html, _, _ in lines:
            f.write(html + "\n")

    with open(txt_path, "w", encoding="utf-8") as f:
        for _, plain, _ in lines:
            f.write(plain + "\n")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
import os, json, sys
from lxml import etree
from lxml.etree import QName
from docx import Document
from zipfile import ZipFile

if len(sys.argv) != 2:
    print("Usage: python extract.py <input_docx>")
    sys.exit(1)

INPUT_DOCX = sys.argv[1]
OUTPUT_DIR = "journal_processing/build/pages"
os.makedirs(OUTPUT_DIR, exist_ok=True)
NAMESPACE = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
}

# Extract comments
comments = {}
doc = Document(INPUT_DOCX)
if hasattr(doc.part, "_comments_part") and doc.part._comments_part is not None:
    for c in doc.part._comments_part.comments:
        cid = str(c._element.get(f"{{{NAMESPACE['w']}}}id"))
        comments[cid] = c.text

# Parse document XML
with ZipFile(INPUT_DOCX) as docx:
    xml = docx.read('word/document.xml')

root = etree.fromstring(xml)
body = root.find('.//w:body', namespaces=NAMESPACE)
line_number = 1
page_number = 0
current_page = []
pages = []

for el in body:
    tag = QName(el).localname

    if el.find('.//w:br[@w:type="page"]', namespaces=NAMESPACE) is not None:
        if current_page:
            pages.append((page_number, current_page))
            current_page = []
            page_number += 1
        continue

    output_line = ""
    plain_line = ""
    page_comments = []
    in_comment = False
    comment_buffer = []
    comment_id = None

    if tag == 'p':
        for child in el:
            ctag = QName(child).localname

            if ctag == 'commentRangeStart':
                comment_id = child.attrib.get(f"{{{NAMESPACE['w']}}}id")
                in_comment = True
                comment_buffer = []
                continue

            if ctag == 'commentRangeEnd':
                in_comment = False
                anchor = ''.join(comment_buffer)
                output_line += f'<a class="comment-link" data-comment-id="c{comment_id}">{anchor}</a>'
                page_comments.append({
                    "id": f"c{comment_id}",
                    "text": comments.get(comment_id, ""),
                })
                comment_id = None
                comment_buffer = []
                continue

            if ctag == 'r':
                text_fragments = []
                for t in child.findall('.//w:t', namespaces=NAMESPACE):
                    txt = t.text or ""
                    plain_line += txt
                    text_fragments.append(txt)
                joined = ''.join(text_fragments)
                if in_comment:
                    comment_buffer.append(joined)
                else:
                    output_line += joined

    html_line = f"<p data-line='{line_number}'>{output_line}</p>"
    current_page.append((html_line, plain_line, page_comments))
    line_number += 1

if current_page:
    pages.append((page_number, current_page))

# Write HTML and metadata, skipping page 0
metadata = []

for page_num, lines in pages:
    if page_num == 0:
        continue
    html_path = os.path.join(OUTPUT_DIR, f"page_{page_num}.html")
    comments_data = [c for _, _, cs in lines for c in cs]
    metadata.append({
        "page": page_num + 1,
        "comments": comments_data
    })
    with open(html_path, "w", encoding="utf-8") as f:
        for html, _, _ in lines:
            f.write(html + "\n")

with open("journal_processing/build/data.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)


