# OCR with GLM-OCR

A Gradio-based Optical Character Recognition (OCR) application that uses the `glm-ocr:latest` model via Ollama to extract text from images. Features an interactive dual-pane viewer with scroll synchronization, HTML formatting support, and batch processing capabilities.

## Requirements

```
Python 3.8+
gradio>=4.0.0
Pillow>=10.0.0
requests>=2.28.0
```

### Ollama Requirements

- [Ollama](https://ollama.ai/) installed and running
- **Only tested with**: `glm-ocr:latest` model

## Installation

1. **Clone or download this project**

2. **Install Python dependencies**:
   ```bash
   pip install gradio Pillow requests
   ```

3. **Install Ollama** (if not already installed):
   - Download from: https://ollama.ai/
   - Or via terminal: `curl -fsSL https://ollama.dev/install.sh | sh`

4. **Pull the required OCR model**:
   ```bash
   ollama pull glm-ocr:latest
   ```

5. **Start Ollama server** (if not running):
   ```bash
   ollama serve
   ```

## Usage

1. **Run the OCR application**:
   ```bash
   python ocr-with-glm-ocr.py
   ```

2. Open your browser to the URL shown (typically `http://127.0.0.1:7860`)

3. **Using the interface**:
   - Select `glm-ocr:latest` from the model dropdown
   - Optionally enable "HTML formatting mode" for structured output
   - Optionally enable "Clear on new batch" to reset results between runs
   - Upload one or more images using the file picker
   - Click "▶ Extract" to process the images
   - View results in the dual-pane viewer

4. **Viewer controls**:
   - Scroll either panel to sync the other
   - Drag the divider between panels to resize
   - Double-click an image to open lightbox zoom
   - Click "Copy All" to copy all extracted text
   - Edit text directly in the text segments
   - Toggle between Plain Text and HTML mode

## How It Works

### Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────┐
│   Gradio UI    │────▶│   Python    │────▶│   Ollama     │
│  (User Input)  │     │  (Processing)│    │ glm-ocr      │
└─────────────────┘     └─────────────┘     └──────────────┘
                              │
                              ▼
                        ┌─────────────┐
                        │  HTML Viewer│
                        │ (Dual Pane) │
                        └─────────────┘
```

### Processing Flow

1. **Image Input**: User uploads images via Gradio file input
2. **Base64 Encoding**: Images are converted to base64 for API transmission
3. **Ollama API Call**: 
   - Prompt is sent with the image to the `glm-ocr:latest` model
   - Model processes the image and returns extracted text
   - Streaming response is accumulated
4. **Result Display**: 
   - Extracted text is paired with the original image
   - HTML viewer is rendered with dual-pane synchronized display
5. **User Interaction**: 
   - Scroll sync between panels
   - Edit capability for post-processing
   - Export via copy functionality

### Key Functions

- `get_models()`: Fetches available Ollama models
- `image_to_b64()`: Converts PIL images to base64
- `ocr_image()`: Sends image to Ollama API and extracts text using `glm-ocr:latest`
- `build_viewer_html()`: Creates the interactive HTML viewer
- `process_images()`: Main processing pipeline with progress yields

## What It Does

- **Text Extraction**: Extracts all visible text from images using `glm-ocr:latest` via Ollama
- **Text Number Detection**: Specifically extracts Text numbers from images
- **HTML Formatting**: Optionally preserves formatting like bold, italics, tables with HTML output
- **Visual Comparison**: Shows side-by-side view of original image and extracted text
- **Batch Processing**: Handles multiple images in sequence with status updates

### Use Cases

- Digitizing printed documents
- Extracting text from screenshots
- Processing receipt images
- Converting scanned documents to text
- Extracting contact information from business cards
- Processing invoice images
- Reading text from photos

## Screenshots

> **Note**: The images below are placeholders. Replace them with actual screenshots of the application.
> Place your screenshot images in the `screenshots/` directory.

### Main Interface
![Main Interface](screenshots/interface.png)

### OCR Viewer
![OCR Viewer](screenshots/viewer.png)

## Configuration

The application connects to Ollama at `http://localhost:11434` (default). To change:

```python
# Modify this line in ocr-with-glm-ocr.py
OLLAMA_BASE = "http://localhost:11434"  # Change to your Ollama URL
```

## Notes

- **Only tested with `glm-ocr:latest`** - Other models may work but are not guaranteed
- The model must be pulled before running the application
- Ensure Ollama is running before starting the Gradio app

## License

This project is provided as-is for educational and practical use.
