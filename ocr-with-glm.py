import gradio as gr
from PIL import Image
import base64
import requests
import json
import io
import os

OLLAMA_BASE = "http://localhost:11434"


def get_models():
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags")
        return [m["name"] for m in r.json().get("models", [])]
    except Exception as e:
        return [f"error: {e}"]


def image_to_b64(pil_image):
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    buf = io.BytesIO()
    pil_image.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def ocr_image(pil_image, model, html_mode=False):
    b64 = image_to_b64(pil_image)

    if html_mode:
        prompt = (
            "Extract all text from this image. "
            "Return valid HTML only — use <b> for bold, <i> for italic, "
            "<table><tr><td> for tables, <br> for line breaks. "
            "Preserve font sizes with <span style='font-size:Xpx'>. "
            "No markdown, no explanations, no code blocks — raw HTML only."
        )
    else:
        prompt = (
            "Extract all text and Text numbers from this image. "
            "Return only the raw text, nothing else."
        )

    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": prompt,
            "images": [b64]
        }],
        "stream": True,
        "options": {
            "temperature": 0.0,
            "num_predict": 2048
        }
    }

    resp = requests.post(f"{OLLAMA_BASE}/api/chat", json=payload, stream=True)
    result = ""
    for line in resp.iter_lines():
        if line:
            try:
                chunk = json.loads(line.decode("utf-8"))
                result += chunk.get("message", {}).get("content", "")
                if chunk.get("done") is True:
                    break
            except:
                continue

    clean = result.strip()
    # Strip accidental markdown code fences if model wraps in ```html
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[-1]
        if clean.endswith("```"):
            clean = clean[:-3].strip()

    return clean if clean else "[no text extracted]"


def build_viewer_html(segments, html_mode=False):
    segments_js = json.dumps([
        {"img": s["img_b64"], "text": s["text"], "label": s["label"]}
        for s in segments
    ])
    html_mode_js = "true" if html_mode else "false"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #0d0d0d;
    overflow: hidden;
    height: 100vh;
    display: flex;
    flex-direction: column;
    font-family: 'JetBrains Mono', monospace;
  }}

  #ocr-viewer {{
    display: flex;
    flex: 1;
    overflow: hidden;
    position: relative;
  }}

  /* ── LEFT: image strip ── */
  #img-pane {{
    width: 280px;
    min-width: 80px;
    max-width: 80%;
    overflow-y: scroll;
    overflow-x: hidden;
    background: #111;
    flex-shrink: 0;
    scrollbar-width: thin;
    scrollbar-color: #333 #111;
  }}
  #img-pane::-webkit-scrollbar {{ width: 4px; }}
  #img-pane::-webkit-scrollbar-thumb {{ background: #333; border-radius: 2px; }}

  .img-slot {{
    position: relative;
    padding: 8px;
    border-bottom: 1px solid #1a1a1a;
    cursor: pointer;
    transition: background 0.2s;
  }}
  .img-slot:hover {{ background: #1a1a1a; }}
  .img-slot.active {{ background: #1a1a1a; }}
  .img-slot.active::before {{
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: #e8c547;
  }}
  .img-slot img {{
    width: 100%;
    border-radius: 4px;
    display: block;
    opacity: 0.35;
    transition: opacity 0.3s;
  }}
  .img-slot.active img {{ opacity: 1; box-shadow: 0 0 0 1px #e8c547; }}
  .img-slot:hover img {{ opacity: 0.7; }}
  .img-label {{
    font-size: 9px;
    color: #444;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 4px 0 2px;
    font-family: 'Syne', sans-serif;
    transition: color 0.2s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .img-slot.active .img-label {{ color: #e8c547; }}

  /* ── DRAG DIVIDER ── */
  #divider {{
    width: 6px;
    background: #1a1a1a;
    cursor: col-resize;
    flex-shrink: 0;
    position: relative;
    transition: background 0.15s;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  #divider:hover, #divider.dragging {{ background: #e8c54733; }}
  #divider::after {{
    content: '';
    width: 2px;
    height: 40px;
    background: #333;
    border-radius: 1px;
    transition: background 0.15s;
  }}
  #divider:hover::after, #divider.dragging::after {{ background: #e8c547; }}

  /* ── RIGHT: text pane ── */
  #text-pane {{
    flex: 1;
    overflow-y: scroll;
    overflow-x: hidden;
    background: #0d0d0d;
    scrollbar-width: thin;
    scrollbar-color: #2a2a2a #0d0d0d;
    min-width: 100px;
  }}
  #text-pane::-webkit-scrollbar {{ width: 4px; }}
  #text-pane::-webkit-scrollbar-thumb {{ background: #2a2a2a; border-radius: 2px; }}

  .text-segment {{
    padding: 16px 20px;
    border-bottom: 1px solid #161616;
    min-height: 60px;
    transition: background 0.2s;
  }}
  .text-segment.active {{
    background: #131310;
    border-left: 2px solid #e8c54733;
  }}
  .text-segment-content {{
    color: #c8c8c8;
    font-size: 13px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
    outline: none;
    min-height: 20px;
  }}
  /* HTML mode styles inside segments */
  .text-segment-content.html-mode {{
    white-space: normal;
    font-family: Georgia, serif;
  }}
  .text-segment-content.html-mode table {{
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    font-size: 12px;
  }}
  .text-segment-content.html-mode td,
  .text-segment-content.html-mode th {{
    border: 1px solid #2a2a2a;
    padding: 4px 8px;
    text-align: left;
  }}
  .text-segment-content:focus {{ color: #e8e8e8; }}
  .seg-num {{
    font-size: 9px;
    color: #2a2a2a;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-bottom: 6px;
    font-family: 'Syne', sans-serif;
    transition: color 0.2s;
  }}
  .text-segment.active .seg-num {{ color: #e8c54766; }}

  /* ── TOOLBAR ── */
  #toolbar {{
    background: #0d0d0d;
    border-bottom: 1px solid #1a1a1a;
    padding: 6px 12px;
    display: flex;
    gap: 8px;
    align-items: center;
  }}
  .tbtn {{
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    color: #777;
    font-size: 10px;
    font-family: 'Syne', sans-serif;
    letter-spacing: 1px;
    padding: 3px 10px;
    border-radius: 3px;
    cursor: pointer;
    text-transform: uppercase;
    transition: all 0.15s;
  }}
  .tbtn:hover {{ color: #e8c547; border-color: #e8c54744; background: #222; }}
  .tbtn.active {{ color: #e8c547; border-color: #e8c547; background: #1a1a0a; }}
  #mode-label {{
    font-size: 10px;
    color: #333;
    font-family: 'Syne', sans-serif;
    letter-spacing: 1px;
    margin-left: auto;
  }}

  /* ── LIGHTBOX ── */
  #lightbox {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.93);
    z-index: 9999;
    align-items: center;
    justify-content: center;
    cursor: zoom-out;
  }}
  #lightbox.open {{ display: flex; }}
  #lightbox img {{
    max-width: 92vw;
    max-height: 92vh;
    border-radius: 6px;
    box-shadow: 0 0 80px rgba(232,197,71,0.12);
    object-fit: contain;
    cursor: default;
  }}
  #lb-close {{
    position: absolute;
    top: 18px; right: 24px;
    color: #555;
    font-size: 26px;
    cursor: pointer;
    line-height: 1;
    transition: color 0.15s;
  }}
  #lb-close:hover {{ color: #e8c547; }}
</style>
</head>
<body>

<div id="toolbar">
  <button class="tbtn" id="copy-btn" onclick="copyAll()">Copy All</button>
  <button class="tbtn" id="mode-btn" onclick="toggleMode()">HTML Mode</button>
  <span id="mode-label">PLAIN TEXT</span>
</div>

<div id="ocr-viewer">
  <div id="img-pane"></div>
  <div id="divider"></div>
  <div id="text-pane"></div>
</div>

<div id="lightbox">
  <span id="lb-close">✕</span>
  <img id="lb-img" src="" alt="" onclick="event.stopPropagation()">
</div>

<script>
(function() {{
  const segments  = {segments_js};
  const imgPane   = document.getElementById('img-pane');
  const textPane  = document.getElementById('text-pane');
  const divider   = document.getElementById('divider');
  const lightbox  = document.getElementById('lightbox');
  const lbImg     = document.getElementById('lb-img');
  const modeBtn   = document.getElementById('mode-btn');
  const modeLabel = document.getElementById('mode-label');

  let activeIdx  = 0;
  let syncing    = false;
  let htmlMode   = {html_mode_js};

  // ── Build DOM ──
  segments.forEach((seg, i) => {{
    // Image slot
    const slot = document.createElement('div');
    slot.className = 'img-slot' + (i === 0 ? ' active' : '');
    slot.dataset.idx = i;
    const lbl = document.createElement('div');
    lbl.className = 'img-label';
    lbl.textContent = 'img ' + (i+1) + ' — ' + seg.label;
    const im = document.createElement('img');
    im.src = 'data:image/jpeg;base64,' + seg.img;
    im.alt = 'Image ' + (i+1);
    im.loading = 'lazy';
    im.addEventListener('dblclick', e => {{ e.stopPropagation(); openLightbox(seg.img); }});
    slot.appendChild(lbl);
    slot.appendChild(im);
    slot.addEventListener('click', () => scrollToSegment(i, 'text'));
    imgPane.appendChild(slot);

    // Text segment
    const tseg = document.createElement('div');
    tseg.className = 'text-segment' + (i === 0 ? ' active' : '');
    tseg.dataset.idx = i;
    const snum = document.createElement('div');
    snum.className = 'seg-num';
    snum.textContent = 'Image ' + (i+1);
    const content = document.createElement('div');
    content.className = 'text-segment-content' + (htmlMode ? ' html-mode' : '');
    content.contentEditable = 'true';
    content.spellcheck = false;
    content.dataset.raw = seg.text;
    renderContent(content, seg.text);
    tseg.appendChild(snum);
    tseg.appendChild(content);
    textPane.appendChild(tseg);
  }});

  function renderContent(el, text) {{
    if (htmlMode) {{
      el.innerHTML = text;
    }} else {{
      el.textContent = text;
    }}
  }}

  // ── HTML / Plain toggle ──
  window.toggleMode = function() {{
    htmlMode = !htmlMode;
    modeBtn.classList.toggle('active', htmlMode);
    modeLabel.textContent = htmlMode ? 'HTML MODE' : 'PLAIN TEXT';
    document.querySelectorAll('.text-segment-content').forEach(el => {{
      el.classList.toggle('html-mode', htmlMode);
      renderContent(el, el.dataset.raw);
    }});
  }};

  if (htmlMode) {{
    modeBtn.classList.add('active');
    modeLabel.textContent = 'HTML MODE';
  }}

  // ── Scroll sync ──
  function setActive(idx) {{
    if (idx === activeIdx) return;
    activeIdx = idx;
    document.querySelectorAll('.img-slot').forEach(el => el.classList.toggle('active', +el.dataset.idx === idx));
    document.querySelectorAll('.text-segment').forEach(el => el.classList.toggle('active', +el.dataset.idx === idx));
  }}

  function scrollToSegment(idx, source) {{
    setActive(idx);
    if (source !== 'text') {{
      const tseg = textPane.querySelectorAll('.text-segment')[idx];
      if (tseg) {{ syncing = true; textPane.scrollTo({{ top: tseg.offsetTop - 20, behavior: 'smooth' }}); setTimeout(() => syncing = false, 600); }}
    }}
    if (source !== 'img') {{
      const islot = imgPane.querySelectorAll('.img-slot')[idx];
      if (islot) {{ syncing = true; imgPane.scrollTo({{ top: islot.offsetTop - 20, behavior: 'smooth' }}); setTimeout(() => syncing = false, 600); }}
    }}
  }}

  textPane.addEventListener('scroll', () => {{
    if (syncing) return;
    const segs = textPane.querySelectorAll('.text-segment');
    let closest = 0, closestDist = Infinity;
    segs.forEach((el, i) => {{
      const dist = Math.abs(el.getBoundingClientRect().top - textPane.getBoundingClientRect().top);
      if (dist < closestDist) {{ closestDist = dist; closest = i; }}
    }});
    if (closest !== activeIdx) {{
      setActive(closest);
      const islot = imgPane.querySelectorAll('.img-slot')[closest];
      if (islot) {{ syncing = true; imgPane.scrollTo({{ top: islot.offsetTop - 20, behavior: 'smooth' }}); setTimeout(() => syncing = false, 600); }}
    }}
  }});

  // ── Drag divider ──
  let dragging = false, startX = 0, startW = 0;

  divider.addEventListener('mousedown', e => {{
    dragging = true;
    startX = e.clientX;
    startW = imgPane.offsetWidth;
    divider.classList.add('dragging');
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
  }});

  document.addEventListener('mousemove', e => {{
    if (!dragging) return;
    const newW = Math.max(80, Math.min(startW + e.clientX - startX, window.innerWidth * 0.8));
    imgPane.style.width = newW + 'px';
  }});

  document.addEventListener('mouseup', () => {{
    if (!dragging) return;
    dragging = false;
    divider.classList.remove('dragging');
    document.body.style.userSelect = '';
    document.body.style.cursor = '';
  }});

  // ── Lightbox ──
  function openLightbox(b64) {{
    lbImg.src = 'data:image/jpeg;base64,' + b64;
    lightbox.classList.add('open');
  }}
  lightbox.addEventListener('click', () => lightbox.classList.remove('open'));
  document.getElementById('lb-close').addEventListener('click', () => lightbox.classList.remove('open'));

  // ── Copy all ──
  window.copyAll = function() {{
    const parts = [];
    document.querySelectorAll('.text-segment-content').forEach(el => parts.push(el.innerText.trim()));
    navigator.clipboard.writeText(parts.join('\\n\\n')).then(() => {{
      const btn = document.getElementById('copy-btn');
      btn.textContent = 'Copied!';
      setTimeout(() => btn.textContent = 'Copy All', 1500);
    }});
  }};

  if (segments.length > 0) setActive(0);
}})();
</script>
</body>
</html>"""

    escaped = html.replace('&', '&amp;').replace('"', '&quot;')
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:640px;border:none;background:#0d0d0d;" frameborder="0"></iframe>'


# ── State ──
_segments = []
_html_mode = False


def process_images(files, model, reset_first, html_mode):
    global _segments, _html_mode
    _html_mode = html_mode

    if reset_first:
        _segments = []

    if not files:
        yield build_viewer_html(_segments, _html_mode) if _segments else "<p style='color:#444;padding:20px;font-family:monospace'>No images processed yet.</p>", "No images uploaded."
        return

    for i, file_path in enumerate(files):
        label = os.path.basename(file_path)
        yield build_viewer_html(_segments, _html_mode) if _segments else "<p style='color:#444;padding:20px;font-family:monospace'>Processing...</p>", f"Processing {i+1}/{len(files)}: {label}"

        try:
            img = Image.open(file_path)
            b64 = image_to_b64(img)
            extracted = ocr_image(img, model, html_mode)
            _segments.append({"img_b64": b64, "text": extracted, "label": label})
            yield build_viewer_html(_segments, _html_mode), f"Done {i+1}/{len(files)}: {label}"
        except Exception as e:
            _segments.append({"img_b64": "", "text": f"[Error: {e}]", "label": label})
            yield build_viewer_html(_segments, _html_mode), f"Error on {label}: {e}"

    yield build_viewer_html(_segments, _html_mode), f"All {len(files)} done. Total: {len(_segments)} segments."


def clear_all():
    global _segments
    _segments = []
    return "<p style='color:#333;padding:20px;font-family:monospace;text-align:center'>Cleared.</p>", "Cleared."


def refresh_models():
    models = get_models()
    return gr.Dropdown(choices=models, value=models[0] if models else "")


initial_models = get_models()
default_model = initial_models[0] if initial_models else ""

with gr.Blocks(title="OCR Text Extractor", css="""
    body { background: #0a0a0a !important; }
    .gradio-container { background: #0a0a0a !important; max-width: 1300px !important; }
    label { color: #555 !important; font-family: monospace !important; font-size: 11px !important; }
    button.primary { background: #e8c547 !important; color: #000 !important; border: none !important; font-family: monospace !important; font-weight: 600 !important; }
    button.secondary { background: #1a1a1a !important; color: #777 !important; border: 1px solid #2a2a2a !important; font-family: monospace !important; }
""") as app:

    gr.HTML("""
    <div style="padding:16px 0 8px;font-family:'Syne',sans-serif;">
      <div style="font-size:10px;letter-spacing:3px;color:#333;text-transform:uppercase;margin-bottom:3px;">Ollama Vision</div>
      <div style="font-size:22px;color:#e8c547;font-weight:700;letter-spacing:-0.5px;">OCR Text Extractor</div>
      <div style="font-size:11px;color:#2a2a2a;margin-top:3px;font-family:monospace;">scroll text → image follows &nbsp;·&nbsp; drag divider &nbsp;·&nbsp; double-click image → zoom</div>
    </div>
    """)

    with gr.Row():
        model_dd    = gr.Dropdown(choices=initial_models, value=default_model, label="Model", interactive=True, scale=3)
        refresh_btn = gr.Button("Refresh", scale=1, variant="secondary")
        html_check  = gr.Checkbox(label="HTML formatting mode", value=False, scale=2)
        reset_check = gr.Checkbox(label="Clear on new batch", value=True, scale=2)

    refresh_btn.click(fn=refresh_models, outputs=model_dd)

    file_input = gr.File(label="Upload Images", file_count="multiple", file_types=["image"], type="filepath")

    with gr.Row():
        run_btn   = gr.Button("▶  Extract", variant="primary", scale=3)
        clear_btn = gr.Button("Clear All", variant="secondary", scale=1)

    status_box = gr.Textbox(label="Status", lines=1, interactive=False)

    viewer = gr.HTML(value="<p style='color:#2a2a2a;padding:40px;font-family:monospace;text-align:center'>Upload images and click Extract</p>")

    run_btn.click(fn=process_images, inputs=[file_input, model_dd, reset_check, html_check], outputs=[viewer, status_box])
    clear_btn.click(fn=clear_all, outputs=[viewer, status_box])

app.launch(share=False)
