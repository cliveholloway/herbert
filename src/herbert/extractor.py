import os
import json
from lxml import etree
from lxml.etree import QName
from docx import Document
from zipfile import ZipFile

NAMESPACE = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}


def extract_docx(input_docx: str, build_dir: str = "journal_processing/build") -> None:
    """
    Extract pages, plain text, and comments from a DOCX into HTML, TXT, and JSON.

    Args:
        input_docx: Path to the input .docx file
        build_dir:  Base directory for outputs (pages/, txt/, data.json)
    """
    html_dir = os.path.join(build_dir, "pages")
    txt_dir = os.path.join(build_dir, "txt")
    json_path = os.path.join(build_dir, "data.json")

    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)

    # --- Extract comments ---
    comments = {}
    doc = Document(input_docx)
    if hasattr(doc.part, "_comments_part") and doc.part._comments_part is not None:
        for c in doc.part._comments_part.comments:
            cid = str(c._element.get(f"{{{NAMESPACE['w']}}}id"))
            comments[cid] = c.text

    # --- Parse document XML ---
    with ZipFile(input_docx) as docx:
        xml = docx.read("word/document.xml")

    root = etree.fromstring(xml)
    body = root.find(".//w:body", namespaces=NAMESPACE)

    line_number = 1
    page_number = 0
    current_page, pages = [], []

    for el in body:
        tag = QName(el).localname

        # Handle page breaks
        if el.find(".//w:br[@w:type='page']", namespaces=NAMESPACE) is not None:
            if current_page:
                pages.append((page_number, current_page))
                current_page = []
                page_number += 1
            continue

        output_line, plain_line = "", ""
        page_comments, comment_buffer = [], []
        in_comment, comment_id = False, None

        if tag == "p":
            for child in el:
                ctag = QName(child).localname

                if ctag == "commentRangeStart":
                    comment_id = child.attrib.get(f"{{{NAMESPACE['w']}}}id")
                    in_comment, comment_buffer = True, []
                    continue

                if ctag == "commentRangeEnd":
                    in_comment = False
                    anchor = "".join(comment_buffer)
                    output_line += (
                        f'<a class="comment-link" data-comment-id="c{comment_id}">{anchor}</a>'
                    )
                    page_comments.append(
                        {"id": f"c{comment_id}", "text": comments.get(comment_id, "")}
                    )
                    comment_id, comment_buffer = None, []
                    continue

                if ctag == "r":
                    text_fragments = []
                    for t in child.findall(".//w:t", namespaces=NAMESPACE):
                        txt = t.text or ""
                        plain_line += txt
                        text_fragments.append(txt)
                    joined = "".join(text_fragments)
                    if in_comment:
                        comment_buffer.append(joined)
                    else:
                        output_line += joined

        html_line = f"<p data-line='{line_number}'>{output_line}</p>"
        current_page.append((html_line, plain_line, page_comments))
        line_number += 1

    if current_page:
        pages.append((page_number, current_page))

    # --- Write outputs ---
    metadata = []
    for page_num, lines in pages:
        if page_num == 0:  # skip first cover page
            continue

        html_path = os.path.join(html_dir, f"page_{page_num}.html")
        txt_path = os.path.join(txt_dir, f"page_{page_num}.txt")

        comments_data = [c for _, _, cs in lines for c in cs]
        metadata.append({"page": page_num + 1, "comments": comments_data})

        with open(html_path, "w", encoding="utf-8") as f:
            for html, _, _ in lines:
                f.write(html + "\n")

        with open(txt_path, "w", encoding="utf-8") as f:
            for _, plain, _ in lines:
                f.write(plain + "\n")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

