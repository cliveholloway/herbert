import os
import json
import shutil
import subprocess
import tempfile
import re
import pdfplumber
import argparse
import zipfile
from zipfile import ZipFile
from lxml import etree
from lxml.etree import QName

# Attempt to import python-docx; if not available, comments fallback may be limited.
try:
    from docx import Document
    from docx.oxml.ns import qn as wqn  # noqa: F401
except Exception:
    Document = None

# Define the namespace mapping for WordprocessingML
NAMESPACE = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'v': 'urn:schemas-microsoft-com:vml',
    'w10': 'urn:schemas-microsoft-com:office:word',
    'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic': 'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
}

OUTPUT_DIR = "output"


def convert_to_pdf(source_file: str) -> str:
    """
    Convert source ODT/DOCX into PDF using LibreOffice headless mode,
    write to OUTPUT_DIR, and return the PDF path.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", temp_dir, source_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion failed: {result.stderr}")

        base = os.path.splitext(os.path.basename(source_file))[0]
        out_src = os.path.join(temp_dir, f"{base}.pdf")
        if not os.path.exists(out_src):
            raise Exception(f"Expected PDF not found at {out_src}")
        out_dst = os.path.join(OUTPUT_DIR, f"{base}.pdf")
        shutil.copy2(out_src, out_dst)
        return out_dst


def ensure_docx_for_comments(source_file: str) -> str:
    """Ensure we have a DOCX version of the doc for comment extraction."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ext = os.path.splitext(source_file)[1].lower()
    if ext == ".docx":
        return source_file

    with tempfile.TemporaryDirectory() as temp_dir:
        cmd = ["libreoffice", "--headless", "--convert-to", "docx", "--outdir", temp_dir, source_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"LibreOffice conversion to DOCX failed: {result.stderr}")

        base = os.path.splitext(os.path.basename(source_file))[0]
        out_src = os.path.join(temp_dir, f"{base}.docx")
        if not os.path.exists(out_src):
            raise Exception(f"Expected DOCX not found at {out_src}")
        out_dst = os.path.join(OUTPUT_DIR, f"{base}.docx")
        shutil.copy2(out_src, out_dst)
        return out_dst


def extract_comments_simple(docx_file: str) -> dict:
    """
    Extract comments and their anchor ranges (based on commentRangeStart/End).
    Return structure:
    {
      "comments": {comment_id: comment_text},
      "comment_data": {
          comment_id: {
             "anchor": "...",
             "before_words": "...",
             "after_words": "...",
          }, ...
      }
    }
    """
    comments = {}
    comment_data = {}

    try:
        if Document is None:
            raise RuntimeError("python-docx not installed")

        doc = Document(docx_file)
        # Read comments from the comments part (if present)
        if hasattr(doc.part, "_comments_part") and doc.part._comments_part is not None:
            for c in doc.part._comments_part.comments:
                cid = str(c._element.get(f"{{{NAMESPACE['w']}}}id"))
                comments[cid] = c.text

        # Read the main document XML to get comment range positions
        with ZipFile(docx_file) as z:
            xml = z.read("word/document.xml")

        root = etree.fromstring(xml)
        body = root.find(".//w:body", namespaces=NAMESPACE)

        for el in body:
            if QName(el).localname != "p":
                continue

            paragraph_words = []
            comment_start_positions = {}
            comment_end_positions = {}
            word_index = 0

            for child in el:
                tag = QName(child).localname
                if tag == "commentRangeStart":
                    comment_id = child.attrib.get(f"{{{NAMESPACE['w']}}}id")
                    comment_start_positions[comment_id] = word_index
                elif tag == "commentRangeEnd":
                    comment_id = child.attrib.get(f"{{{NAMESPACE['w']}}}id")
                    comment_end_positions[comment_id] = word_index
                elif tag == "r":
                    # text runs inside this paragraph
                    for t in child.findall(".//w:t", namespaces=NAMESPACE):
                        if t.text:
                            # Use the SAME tokenization as the matcher: sequences of non-space (\S+)
                            words = re.findall(r"\S+", t.text)
                            paragraph_words.extend(words)
                            word_index += len(words)

            for comment_id, start_idx in comment_start_positions.items():
                if comment_id not in comment_end_positions:
                    continue
                end_idx = comment_end_positions[comment_id]

                anchor_words = paragraph_words[start_idx:end_idx]
                if not anchor_words:
                    continue

                before_words = paragraph_words[max(0, start_idx - 2):start_idx]
                after_words = paragraph_words[end_idx:end_idx + 2]

                comment_data[comment_id] = {
                    "anchor": " ".join(anchor_words).strip(),
                    "before_words": " ".join(before_words).strip(),
                    "after_words": " ".join(after_words).strip(),
                }

    except Exception as e:
        print(f"Warning: Could not extract comments: {e}")
        import traceback; traceback.print_exc()

    return {"comments": comments, "comment_data": comment_data}


# -------------------- Matching & Injection Helpers --------------------

_TOKEN_RE = re.compile(r"\S+")


def _normalize_token(s: str) -> str:
    # Normalize case and typographic quotes/dashes ONLY.
    # Do NOT strip punctuation so tokens remain exactly "\S+" (Perl-style).
    x = s.lower()
    x = (x.replace("’", "'").replace("‘", "'")
           .replace("“", '"').replace("”", '"')
           .replace("–", "-").replace("—", "-"))
    return x


def _tokenize_with_spans(text: str):
    r"""Tokenize as sequences of non-space characters (\S+), preserving punctuation tokens."""
    toks = []
    for m in _TOKEN_RE.finditer(text):
        raw = m.group(0)
        toks.append({
            "text": raw,
            "norm": _normalize_token(raw),
            "start": m.start(),
            "end": m.end(),
        })
    return toks


def _build_anchor_regex(anchor_words):
    # allow whitespace or hyphen+newline breaks between words
    joiner = r"(?:\s+|-\s*\n\s*)"
    parts = [re.escape(w) for w in anchor_words if w]
    if not parts:
        return None
    return re.compile(joiner.join(parts), flags=re.DOTALL)


def _match_and_plan_replacements(page_text, anchors_dict, comments, used_comments):
    r"""
    Context-based matcher (single-line anchors only):
    - Tokens are \S+; punctuation preserved.
    - Compare using edge-trimmed forms so punctuation hugging words (quotes/commas) doesn't block matches.
    - If both before/after exist, require both; if one side exists, require that one; if neither, anchor-only.
    - Accept possessive/plural on the last anchor token (crew/crew's/crew’s/crews). Keep ’s/'s outside the link.
    """
    tokens = _tokenize_with_spans(page_text)
    if not tokens:
        return page_text, [], used_comments

    # Normalized and edge-trimmed tokens
    norm_seq = [t["norm"] for t in tokens]
    PUNCT_EDGES = ".,;:!?)]}”’'\"([{“‘…"
    def edge(s: str) -> str:
        return s.strip(PUNCT_EDGES)
    comp_seq = [edge(x) for x in norm_seq]
    # Trim leading/trailing hyphens/dashes at token edges (after normalizing “–/—” → '-')
    comp_seq = [re.sub(r'^-+|-+$', '', t) for t in comp_seq]
    # Strip a trailing bare apostrophe not followed by s (handles Berk’-/Berk’)
    comp_seq = [re.sub(r"(?<!s)['’]$", "", t) for t in comp_seq]
    # Non-punctuation token indexes (comparison basis)
    nonp = [i for i, c in enumerate(comp_seq) if c]

    replacements = []
    page_comments = []

    # helper: in-order subsequence match inside a window, allowing leading hyphen on tokens
    def _in_order(hay: list[str], needles: list[str]) -> bool:
        if not needles:
            return True
        i = 0
        for tok in hay:
            if not tok:
                continue
            t = tok.lstrip('-')
            if t == needles[i]:
                i += 1
                if i == len(needles):
                    return True
        return False

    for cid, info in anchors_dict.items():
        if cid in used_comments:
            continue
        anchor = (info.get("anchor") or "").strip()
        if not anchor:
            continue

        aw = [w for w in anchor.split() if w]
        bw = [w for w in (info.get("before_words") or "").split() if w]
        fw = [w for w in (info.get("after_words") or "").split() if w]

        # Normalize/edge-trim for comparison
        def _norm_edge(w: str) -> str:
            return edge(_normalize_token(w))
        def _edge_after(w: str) -> str:
            nrm = _normalize_token(w)
            # Preserve possessive token so we can allow absorption by the anchor
            if nrm in ("'s", "’s"):
                return "'s"
            e = edge(nrm)
            # Drop standalone dash tokens (after normalization “–/—” -> '-')
            return "" if e == "-" else e

        aw_comp = [_norm_edge(w) for w in aw if _norm_edge(w)]
        bw_comp = [_norm_edge(w) for w in bw if _norm_edge(w)]
        fw_comp = [_edge_after(w) for w in fw]
        fw_comp = [t for t in fw_comp if t]
        # Keep raw-normalized anchor tokens (for punctuation-only anchors like '?' or '(?)')
        aw_norm_list = [_normalize_token(w) for w in aw]
        n = len(aw_comp)
        punct_only_anchor = (len(aw_norm_list) > 0 and n == 0)
        if n == 0 and not punct_only_anchor:
            print(f"[debug] skip c{cid}: empty anchor")
            continue

        def anchor_span_len(start_nonp: int) -> int:
            """Return the length (in nonp tokens) of the anchor match starting at start_nonp.
            Supports either normal n-token match or concatenated multi-token anchor
            collapsed into a single PDF token (e.g., ['fenia','ns'] -> 'fenians').
            Returns 0 if no match."""
            # Case A: normal n-token match
            if start_nonp + n <= len(nonp):
                ok = True
                for j in range(n):
                    idx = nonp[start_nonp + j]
                    t = comp_seq[idx]
                    a = aw_comp[j]
                    if t == a:
                        continue
                    if j == n - 1 and t in (a + "s", a + "'s", a + "’s"):
                        continue
                    if j == n - 1 and t.startswith(a + "-"):
                        continue
                    ok = False
                    break
                if ok:
                    return n
            # Case B: concatenated anchor tokens equal a single PDF token
            cat = "".join(aw_comp)
            if cat:
                idx = nonp[start_nonp] if start_nonp < len(nonp) else None
                if idx is not None and comp_seq[idx] == cat:
                    return 1
            return 0

        def before_ok(start_nonp: int) -> bool:
            if not bw_comp:
                return True
            if start_nonp < len(bw_comp):
                return False
            actual = [comp_seq[nonp[start_nonp - len(bw_comp) + k]] for k in range(len(bw_comp))]
            return actual == bw_comp

        def after_ok(start_nonp: int, span_len: int = None) -> bool:
            if span_len is None:
                span_len = n
            if not fw_comp:
                return True
            if span_len == 0:
                return False
            end_nonp = start_nonp + span_len
            last_t = comp_seq[nonp[start_nonp + span_len - 1]]
            base = aw_comp[-1]
            fw_req = list(fw_comp)
            # 1) absorb possessive if the last anchor token already includes it
            if fw_req and fw_req[0] in ("'s", "’s") and last_t in (base + "'s", base + "’s", base + "s"):
                fw_req = fw_req[1:]
            # 2) handle hyphen-glued next word inside the last token (e.g., and-used)
            if fw_req:
                expect = fw_req[0]
                if last_t.startswith(base + "-" + expect):
                    fw_req = fw_req[1:]
                # 2b) handle concatenation without hyphen (e.g., journa + l -> journal)
                elif last_t == base + expect:
                    fw_req = fw_req[1:]
            if end_nonp + len(fw_req) > len(nonp):
                return False
            actual = [comp_seq[nonp[end_nonp + k]] for k in range(len(fw_req))]
            return actual == fw_req

        def before_last_ok(start_nonp: int) -> bool:
            """Relaxed: only require the LAST before word to match immediately before."""
            if not bw_comp:
                return True
            if start_nonp < 1:
                return False
            return comp_seq[nonp[start_nonp - 1]] == bw_comp[-1]

        def after_first_ok(start_nonp: int) -> bool:
            """Relaxed: only require the FIRST after word to match (supports glued hyphen/possessive)."""
            if not fw_comp:
                return True
            if n == 0:
                return False
            end_nonp = start_nonp + n
            expect = fw_comp[0]
            base = aw_comp[-1]
            last_t = comp_seq[nonp[start_nonp + n - 1]]
            # absorbed possessive by anchor's last token
            if expect in ("'s", "’s") and last_t in (base + "'s", base + "’s", base + "s"):
                return True
            # next token matches (allow leading hyphen on it)
            if end_nonp < len(nonp):
                nxt = comp_seq[nonp[end_nonp]]
                if nxt == expect or (nxt.startswith("-") and nxt.lstrip("-") == expect):
                    return True
            # hyphen-glued directly to last anchor token (e.g., and-used)
            if last_t.startswith(base + "-" + expect):
                return True
            return False

        found_span = None
        candidates = []
        # Pass 1: strict both-sides (or the one side provided) — skip for punctuation-only anchors
        if not punct_only_anchor:
            for s_nonp in range(0, max(0, len(nonp) - 1)):
                L = anchor_span_len(s_nonp)
                if L == 0:
                    continue
                candidates.append(s_nonp)
                if not before_ok(s_nonp):
                    continue
                if not after_ok(s_nonp, L):
                    continue
                # Map back to original token span
                start_tok = nonp[s_nonp]
                end_tok   = nonp[s_nonp + L - 1]
                found_span = (tokens[start_tok]["start"], tokens[end_tok]["end"])
                break

        # Punctuation-only anchor handling (e.g., '?', '(?)')
        if not found_span and punct_only_anchor:
            mlen = len(aw_norm_list)
            for i_full in range(0, max(0, len(tokens) - mlen + 1)):
                ok_anchor = True
                for j in range(mlen):
                    if _normalize_token(tokens[i_full + j]["text"]) != aw_norm_list[j]:
                        ok_anchor = False
                        break
                if not ok_anchor:
                    continue
                # Check immediate before/after using nearest non-empty comp tokens
                def prev_nonp(idx, k):
                    res = []
                    p = idx - 1
                    while p >= 0 and len(res) < k:
                        if comp_seq[p]:
                            res.append(comp_seq[p])
                        p -= 1
                    return list(reversed(res))
                def next_nonp(idx, k):
                    res = []
                    p = idx + 1
                    while p < len(tokens) and len(res) < k:
                        if comp_seq[p]:
                            res.append(comp_seq[p])
                        p += 1
                    return res
                if (not bw_comp or prev_nonp(i_full, len(bw_comp)) == bw_comp) and (not fw_comp or next_nonp(i_full + mlen - 1, len(fw_comp)) == fw_comp):
                    s = tokens[i_full]["start"]
                    e = tokens[i_full + mlen - 1]["end"]
                    found_span = (s, e)
                    break

        if not found_span:
            # No match on this page; we'll only report unmatched comments at end-of-run.
            continue

        s, e = found_span
        # If the last anchor token is hyphen-glued to the next word (e.g., and-used),
        # trim the link to end before the hyphen.
        end_tok_ix = None
        end_span = s, e
        for ix in range(len(tokens)-1, -1, -1):
            if tokens[ix]["end"] == e:
                end_tok_ix = ix
                break
        if end_tok_ix is not None and n > 0:
            raw_last = tokens[end_tok_ix]["text"]
            norm_last = tokens[end_tok_ix]["norm"]
            base_last = aw_comp[-1]
            if norm_last.startswith(base_last + "-"):
                for ch in ("-", "–", "—"):
                    p = raw_last.find(ch)
                    if p != -1:
                        e = tokens[end_tok_ix]["start"] + p
                        break

        raw_anchor_text = page_text[s:e]
        # keep possessive outside link
        if raw_anchor_text.endswith("’s") or raw_anchor_text.endswith("'s"):
            e -= 2
            raw_anchor_text = page_text[s:e]

        link_html = f'<a class="comment-link" data-comment-id="c{cid}">{raw_anchor_text}</a>'
        replacements.append((s, e, link_html))
        page_comments.append({"id": f"c{cid}", "text": comments.get(cid, ""), "anchor": anchor})
        used_comments.add(cid)

    # Apply replacements from end → start
    if replacements:
        replacements.sort(key=lambda x: x[0], reverse=True)
        buf = page_text
        for s, e, rep in replacements:
            buf = buf[:s] + rep + buf[e:]
        page_text = buf

    return page_text, page_comments, used_comments

def extract_docx(source_file: str) -> None:
    base = os.path.splitext(os.path.basename(source_file))[0]
    html_dir = os.path.join(OUTPUT_DIR, "html")
    txt_dir = os.path.join(OUTPUT_DIR, "txt")
    json_path = os.path.join(OUTPUT_DIR, f"{base}.comments.json")
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)

    print("Step 1: Converting to PDF...")
    pdf_path = convert_to_pdf(source_file)

    print("Step 2: Extracting comments...")
    docx_for_comments = ensure_docx_for_comments(source_file)
    comment_data = extract_comments_simple(docx_for_comments)
    comments = comment_data["comments"]
    comment_anchors = comment_data["comment_data"]
    print(f"Found {len(comments)} total comments, {len(comment_anchors)} with context")

    # Debug: list comments that have NO extracted context (e.g., deleted/misaligned ranges)
    missing_ids = sorted(set(comments.keys()) - set(comment_anchors.keys()), key=lambda x: int(x) if str(x).isdigit() else str(x))
    if missing_ids:
        print(f"[debug] {len(missing_ids)} comment(s) with no context:")
        for mid in missing_ids:
            txt = (comments.get(mid) or "").strip().replace("\n", " ")
            if len(txt) > 120:
                txt = txt[:117] + "..."
            print(f"  - id=c{mid}: {txt}")

    print("Step 3: Extracting text from PDF pages...")
    page_texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_texts.append(text)

    print(f"Extracted {len(page_texts)} pages from PDF")

    print("Step 4: Processing pages...")
    metadata = []
    used_comments = set()

    for page_num in range(len(page_texts)):
        # Skip cover page if page_num==0 is not part of the journal text
        if page_num == 0:
            continue

        html_path = os.path.join(html_dir, f"page{page_num:03d}.html")
        txt_path = os.path.join(txt_dir, f"page{page_num:03d}.txt")

        page_text = page_texts[page_num]
        lines = page_text.split('\n')
        # Drop trailing standalone page number / blank lines
        while lines and (lines[-1].strip().isdigit() or not lines[-1].strip()):
            lines.pop()
        clean_text = '\n'.join(lines)

        # Insert comment links using context (single pass per page; no cross-line anchors)
        linked_text, page_comments, used_comments = _match_and_plan_replacements(
            clean_text, comment_anchors, comments, used_comments
        )

        metadata.append({
            "page": page_num,
            "comments": [{"id": c["id"], "text": c["text"]} for c in page_comments]
        })

        # Wrap each extracted line in <p data-line='N'> ... </p>
        html_lines = []
        for line_num, line in enumerate(linked_text.split('\n'), 1):
            html_lines.append(f"<p data-line='{line_num}'>{line}</p>")
        html_content = '\n'.join(html_lines)

        # Remove stray trailing numeric paragraph if any
        html_content = re.sub(r"<p data-line='\d+'>\d+</p>\s*$", "", html_content)

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(clean_text)

    # End-of-run summary for comments that had context but never anchored anywhere
    remaining = sorted(set(comment_anchors.keys()) - set(used_comments), key=lambda x: int(x) if str(x).isdigit() else str(x))
    if remaining:
        print(f"[debug] {len(remaining)} comment(s) with context not anchored:")
        for cid in remaining:
            ctx = comment_anchors.get(cid, {})
            anchor = ctx.get("anchor", "").strip()
            bw = ctx.get("before_words", "").strip()
            fw = ctx.get("after_words", "").strip()
            print(f"  - id=c{cid}: anchor='{anchor}' before='{bw}' after='{fw}'")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"PDF saved as: {pdf_path}")
    print(f"\u2713 Extracted {len(page_texts) - 1} pages to {OUTPUT_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract PDF text and inject comment anchors from ODT/DOCX")
    parser.add_argument("source", help="Path to source ODT/DOCX file")
    args = parser.parse_args()

    extract_docx(args.source)

