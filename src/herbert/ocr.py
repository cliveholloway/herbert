import os
import base64
import re
from pathlib import Path
import anthropic
import json
import time


# Array of model families to process
# Available models: "sonnet", "haiku", "opus"
# After manual testing, I removed Haiku
MODEL_FAMILIES = ["sonnet", "opus"]

def get_latest_model_ids() -> dict:
    """
    Fetch the latest model IDs from Anthropic's Models API.
    Returns a dictionary mapping model families to their latest model IDs.
    """
    print("🔍 DEBUG: Starting model ID retrieval...")
    client = anthropic.Anthropic()
    
    try:
        print("🔍 DEBUG: Making API call to client.models.list()...")
        start_time = time.time()
        models_response = client.models.list()
        api_time = time.time() - start_time
        print(f"🔍 DEBUG: API call completed in {api_time:.2f}s")
        
        available_models = [model.id for model in models_response.data]
        print(f"🔍 DEBUG: Found {len(available_models)} total models from API")
        print(f"🔍 DEBUG: Available models: {available_models}")
        
        # Find the latest model for each family
        model_ids = {}
        
        # Look for the latest models in order of preference
        for family in MODEL_FAMILIES:
            print(f"🔍 DEBUG: Searching for {family.capitalize()} models...")
            for model_id in available_models:
                if family in model_id.lower() and family not in model_ids:
                    model_ids[family] = model_id
                    print(f"🔍 DEBUG: Found {family.capitalize()} model: {model_id}")
                    break
            else:
                print(f"🔍 DEBUG: No {family.capitalize()} model found")
        
        print("🔡 Retrieved latest model IDs from API:")
        for family, model_id in model_ids.items():
            print(f"  {family}: {model_id}")
        
        print(f"🔍 DEBUG: Successfully mapped {len(model_ids)} model families")
        return model_ids
        
    except Exception as e:
        print(f"🔍 DEBUG: Exception during API call: {type(e).__name__}: {str(e)}")
        print("⚠️ Failed to fetch latest models from API: {e}")
        print("📄 Falling back to hardcoded model IDs...")
        
        # Fallback to hardcoded values if API call fails
        fallback_models = {
            "sonnet": "claude-sonnet-4-20250514",
            "haiku":  "claude-3-5-haiku-20241022",
            "opus":   "claude-opus-4-1-20250805",
        }
        print(f"🔍 DEBUG: Using fallback models: {fallback_models}")
        return fallback_models

def load_prompt(prompt_file: Path) -> str:
    """Load base transcription prompt."""
    print(f"🔍 DEBUG: Loading prompt from {prompt_file}")
    
    if not prompt_file.exists():
        print(f"🔍 DEBUG: ERROR - Prompt file does not exist: {prompt_file}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        
        print(f"🔍 DEBUG: Loaded prompt - {len(content)} characters, {len(content.split())} words")
        print(f"🔍 DEBUG: Prompt preview: '{content[:100]}{'...' if len(content) > 100 else ''}'")
        return content
        
    except Exception as e:
        print(f"🔍 DEBUG: ERROR reading prompt file: {type(e).__name__}: {str(e)}")
        raise


def load_hints(hints_dir: Path) -> list:
    """
    Load OCR hint examples from hints.txt in the given directory.

    Format of hints.txt:
        img1 => "Pightle",
        img2 => Fernie's
    
    Note: .png extension is automatically appended to identifiers.
    """
    print(f"🔍 DEBUG: Loading hints from directory: {hints_dir}")
    hints_file = hints_dir / "hints.txt"
    
    if not hints_file.exists():
        print(f"🔍 DEBUG: No hints file found at {hints_file}")
        return []

    print(f"🔍 DEBUG: Found hints file: {hints_file}")
    hints = []
    processed_count = 0
    skipped_count = 0
    
    try:
        with open(hints_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        print(f"🔍 DEBUG: Read {len(lines)} lines from hints file")
        
        for line_num, line in enumerate(lines, 1):
            original_line = line
            line = line.strip().rstrip(",")  # strip whitespace and trailing commas
            print(f"🔍 DEBUG: Line {line_num}: '{original_line.strip()}' -> '{line}'")
            
            if not line or line.startswith("#"):
                print(f"🔍 DEBUG: Skipping line {line_num} (empty or comment)")
                skipped_count += 1
                continue
                
            parts = re.split(r"\s*=>\s*", line, maxsplit=1)
            if len(parts) != 2:
                print(f"🔍 DEBUG: Skipping line {line_num} (invalid format, got {len(parts)} parts)")
                skipped_count += 1
                continue
                
            img_identifier, correct_text = parts
            # Append .png to the identifier to get the actual filename
            img_name = f"{img_identifier}.png"
            img_path = hints_dir / img_name
            print(f"🔍 DEBUG: Processing hint: '{img_identifier}' -> '{img_name}' -> '{correct_text}' (path: {img_path})")
            
            if not img_path.exists():
                print(f"🔍 DEBUG: Skipping line {line_num} - image not found: {img_path}")
                skipped_count += 1
                continue
                
            try:
                with open(img_path, "rb") as imgf:
                    img_data = imgf.read()
                
                img_size = len(img_data)
                b64 = base64.b64encode(img_data).decode("utf-8")
                b64_size = len(b64.encode("utf-8"))
                
                print(f"🔍 DEBUG: Encoded hint image {img_name} (from identifier '{img_identifier}'): {img_size} bytes -> {b64_size} bytes (base64)")
                
                # Add each hint as a complete example with clear pairing
                hints.append({"type": "text", "text": f"Example {processed_count + 1}:"})
                hints.append(
                    {"type": "image",
                     "source": {"type": "base64", "media_type": "image/png", "data": b64}}
                )
                hints.append({"type": "text", "text": f"Transcription: {correct_text.strip()}"})
                processed_count += 1
                
            except Exception as e:
                print(f"🔍 DEBUG: ERROR processing image {img_path} (from identifier '{img_identifier}'): {type(e).__name__}: {str(e)}")
                skipped_count += 1
                continue
    
    except Exception as e:
        print(f"🔍 DEBUG: ERROR reading hints file: {type(e).__name__}: {str(e)}")
        return []
    
    print(f"🔍 DEBUG: Hints summary - processed: {processed_count}, skipped: {skipped_count}, total hint objects: {len(hints)}")
    return hints


def build_messages(prompt_text: str, image: Path, hints: list):
    """Build Anthropic message payload from prompt, hints, and a single image."""
    print(f"🔍 DEBUG: Building messages for image: {image}")
    print(f"🔍 DEBUG: Using {len(hints)} hint objects, prompt length: {len(prompt_text)} chars")
    
    content = []

    # Add hints if available
    if hints:
        hint_examples = len(hints) // 3  # Each hint is 3 objects: text, image, text
        print(f"🔍 DEBUG: Adding {hint_examples} hint examples to content")
        content.append({"type": "text", "text": "Examples of correct transcription:"})
        content.extend(hints)
        content.append({"type": "text", "text": "Now transcribe the following page faithfully:"})

    # Add the main prompt
    if prompt_text.strip():  # Only add if non-empty
        content.append({"type": "text", "text": prompt_text})

    # Encode and add the main image
    try:
        with open(image, "rb") as f:
            img_data = f.read()
        
        img_size = len(img_data)
        b64 = base64.b64encode(img_data).decode("utf-8")
        b64_size = len(b64.encode("utf-8"))
        
        print(f"🔍 DEBUG: Encoded main image: {img_size} bytes -> {b64_size} bytes (base64)")
        
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": b64},
        })
        
    except Exception as e:
        print(f"🔍 DEBUG: ERROR reading/encoding image {image}: {type(e).__name__}: {str(e)}")
        raise

    total_content_items = len(content)
    print(f"🔍 DEBUG: Built message with {total_content_items} content items")
    
    # Validate that we have non-empty content
    if not content:
        raise ValueError("No content items generated for message")
    
    # Check for empty text content (which causes the API error)
    for i, item in enumerate(content):
        if item["type"] == "text" and not item["text"].strip():
            print(f"🔍 DEBUG: WARNING - Empty text content at index {i}")
    
    return content

def run_ocr(source_dir: str, label: str = "", max_tokens: int = 2000):
    """
    Run OCR on images in a source directory using Anthropic API.

    Args:
        source_dir: Path to directory containing images & prompt.txt
        label: Optional string appended to output filenames (e.g. "test1")
        max_tokens: Max tokens for model output
    """
    print(f"🔍 DEBUG: Starting OCR run - source_dir: '{source_dir}', label: '{label}', max_tokens: {max_tokens}")

    # Dynamically fetch latest model IDs (with fallback if API call fails)
    print("🔍 DEBUG: Fetching model IDs...")
    model_ids = get_latest_model_ids()
    print(f"🔍 DEBUG: Got model IDs: {model_ids}")

    source = Path(source_dir)
    print(f"🔍 DEBUG: Source path resolved to: {source.absolute()}")
    
    if not source.exists():
        print(f"🔍 DEBUG: ERROR - Source directory does not exist: {source}")
        raise FileNotFoundError(f"Source directory not found: {source}")
    
    if not source.is_dir():
        print(f"🔍 DEBUG: ERROR - Source path is not a directory: {source}")
        raise NotADirectoryError(f"Source path is not a directory: {source}")

    # Both prompt file and hints directory are now relative to repo root
    repo_root = Path(__file__).resolve().parents[2]
    prompt_file = repo_root / "data" / "ocr_prompt.txt"
    print(f"🔍 DEBUG: Looking for prompt file at: {prompt_file} (repo root: {repo_root})")
    
    if not prompt_file.exists():
        print(f"🔍 DEBUG: ERROR - Prompt file not found: {prompt_file}")
        raise FileNotFoundError(f"ocr_prompt.txt not found at {prompt_file}")

    hints_dir = repo_root / "data" / "ocr_hints"
    print(f"🔍 DEBUG: Checking for hints directory at: {hints_dir}")
    
    if hints_dir.exists():
        print(f"🔍 DEBUG: Hints directory found, loading hints...")
        hints = load_hints(hints_dir)
    else:
        print(f"🔍 DEBUG: No hints directory found at {hints_dir}")
        hints = []

    print(f"🔍 DEBUG: Loading prompt from centralized location...")
    prompt_text = load_prompt(prompt_file)

    print(f"🔍 DEBUG: Scanning for PNG images in {source}")
    all_files = list(source.iterdir())
    print(f"🔍 DEBUG: Found {len(all_files)} total files/directories")
    
    images = sorted([p for p in all_files if p.suffix.lower() == ".png"])
    print(f"🔍 DEBUG: Found {len(images)} PNG images: {[img.name for img in images]}")
    
    if not images:
        print(f"🔍 DEBUG: ERROR - No PNG images found")
        raise FileNotFoundError(f"No .png images found in {source}")

    # Output directory relative to repo root
    output_dir = repo_root / "output" / "ocr_pages"
    print(f"🔍 DEBUG: Output directory: {output_dir.absolute()}")
    
    print(f"🔍 DEBUG: Creating output directory (if needed)...")
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"🔍 DEBUG: Output directory ready")

    print(f"🔍 DEBUG: Initializing Anthropic client...")
    client = anthropic.Anthropic()
    print(f"🔍 DEBUG: Client initialized")

    total_requests = len(images) * len([f for f in MODEL_FAMILIES if f in model_ids])
    current_request = 0
    
    print(f"🔍 DEBUG: Will process {len(images)} images x {len(model_ids)} models = {total_requests} total requests")

    for img_idx, img in enumerate(images, 1):
        print(f"\n🔍 DEBUG: ===== Processing image {img_idx}/{len(images)}: {img.name} =====")
        
        for family in MODEL_FAMILIES:
            current_request += 1
            print(f"\n🔍 DEBUG: ----- Request {current_request}/{total_requests}: {img.name} with {family} -----")
            
            if family not in model_ids:
                print(f"🔍 DEBUG: Skipping {family}: no model ID found")
                print(f"⚠️ Skipping {family}: no model ID found")
                continue
                
            model = model_ids[family]
            print(f"🔍 DEBUG: Using model: {model}")

            # Build request content using the proper function
            print(f"🔍 DEBUG: Building request content...")
            try:
                content = build_messages(prompt_text, img, hints)
                print(f"🔍 DEBUG: Content built with {len(content)} items")
            except Exception as e:
                print(f"🔍 DEBUG: ERROR building content: {type(e).__name__}: {str(e)}")
                continue

            # Estimate total request size
            print(f"🔍 DEBUG: Estimating request size...")
            try:
                payload = {
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": content}],
                }
                request_json = json.dumps(payload)
                request_size = len(request_json.encode("utf-8"))
                print(f"🔍 DEBUG: Request JSON size: {request_size} bytes ({request_size/1024/1024:.2f} MB)")
                
            except Exception as e:
                print(f"🔍 DEBUG: ERROR estimating request size: {type(e).__name__}: {str(e)}")
                request_size = 0

            print(f"\n--- Processing {img.name} with {family} ---")
            print(f"  Request size:   {request_size/1024/1024:.2f} MB (JSON payload)")
            print(f"  Prompt length:  {len(prompt_text.split())} words")
            print(f"  Hints used:     {len(hints)//3} examples")  # Now 3 items per example
            if request_size > 9*1024*1024:
                print("  ⚠️ WARNING: request is close to 10 MB API limit!")
                print(f"🔍 DEBUG: Request size warning - {request_size} bytes vs 10MB limit")

            # Send request
            print(f"🔍 DEBUG: Sending API request...")
            try:
                start_time = time.time()
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": content}],
                )
                api_time = time.time() - start_time
                print(f"🔍 DEBUG: API request completed in {api_time:.2f}s")
                
                # Debug response structure
                print(f"🔍 DEBUG: Response type: {type(response)}")
                print(f"🔍 DEBUG: Response content blocks: {len(response.content)}")
                for i, block in enumerate(response.content):
                    print(f"🔍 DEBUG: Block {i}: type={block.type}, length={len(getattr(block, 'text', ''))}")
                
                text_blocks = [block for block in response.content if block.type == "text"]
                text_raw = "".join(block.text for block in text_blocks)
                
                print(f"🔍 DEBUG: Extracted text length: {len(text_raw)} characters")
                print(f"🔍 DEBUG: Text preview: '{text_raw[:100]}{'...' if len(text_raw) > 100 else ''}'")
                
                # Clean the text by stripping whitespace
                final_text = text_raw.strip()
                print(f"🔍 DEBUG: Final text length after stripping: {len(final_text)} characters")
                
                # Analyze blank line patterns for debugging
                lines = final_text.split('\n')
                blank_line_count = sum(1 for line in lines if line.strip() == '')
                consecutive_blanks = []
                current_blank_streak = 0
                for line in lines:
                    if line.strip() == '':
                        current_blank_streak += 1
                    else:
                        if current_blank_streak > 0:
                            consecutive_blanks.append(current_blank_streak)
                            current_blank_streak = 0
                if current_blank_streak > 0:  # Handle trailing blanks
                    consecutive_blanks.append(current_blank_streak)
                
                print(f"🔍 DEBUG: Text analysis - Total lines: {len(lines)}, Blank lines: {blank_line_count}")
                if consecutive_blanks:
                    print(f"🔍 DEBUG: Consecutive blank line patterns: {consecutive_blanks}")
                else:
                    print(f"🔍 DEBUG: No consecutive blank lines found")
                
                # Ensure text ends with newline (Unix convention)
                if final_text and not final_text.endswith('\n'):
                    final_text += '\n'
                    print(f"🔍 DEBUG: Added trailing newline")
                elif final_text.endswith('\n'):
                    print(f"🔍 DEBUG: Text already ends with newline")
                else:
                    print(f"🔍 DEBUG: Empty text, no newline needed")
                
            except Exception as e:
                print(f"🔍 DEBUG: ERROR during API request: {type(e).__name__}: {str(e)}")
                print(f"❌ API request failed for {img.name} ({family}): {str(e)}")
                continue

            # Save output
            try:
                suffix = f"_{label}" if label else ""
                raw_file = output_dir / f"{img.stem}_{family}{suffix}.txt"
                print(f"🔍 DEBUG: Saving output to: {raw_file}")
                
                with open(raw_file, "w", encoding="utf-8") as f:
                    f.write(final_text)
                
                saved_size = raw_file.stat().st_size
                print(f"🔍 DEBUG: Saved {saved_size} bytes to {raw_file}")
                print(f"✅ OCR complete: {img.name} ({family}) -> {raw_file}")
                
            except Exception as e:
                print(f"🔍 DEBUG: ERROR saving output: {type(e).__name__}: {str(e)}")
                print(f"❌ Failed to save output for {img.name} ({family}): {str(e)}")
                continue

    print(f"\n🔍 DEBUG: ===== OCR run completed =====")
    print(f"🔍 DEBUG: Processed {len(images)} images with {len([f for f in MODEL_FAMILIES if f in model_ids])} models")
