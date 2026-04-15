# OCR with GLM-OCR

A Gradio-based Optical Character Recognition (OCR) application that uses Ollama's vision models to extract text from images. Supports both plain text and HTML-formatted output with an interactive dual-pane viewer.

## Features

- **Vision Model Integration**: Uses Ollama's vision-capable models (GLM-4-Vision, LLaVA, etc.) for OCR
- **Dual-Pane Interface**: Side-by-side image and extracted text viewer with scroll synchronization
- **HTML Mode**: Option to extract text with HTML formatting (bold, italics, tables, line breaks)
- **Batch Processing**: Process multiple images at once with progress tracking
- **Interactive Viewer**: 
  - Drag to resize the image/text panels
  - Double-click images to open lightbox zoom
  - Edit extracted text directly in the viewer
  - Copy all text to clipboard
- **Dark Theme**: Professional dark UI with syntax-highlighted colors

## Requirements

```
Python 3.8+
gradio>=4.0.0
Pillow>=10.0.0
requests>=2.28.0
```

### Ollama Requirements

- [Ollama](https://ollama.ai/) installed and running
- A vision-capable model pulled (e.g., `ollama pull glm4v` or `ollama pull llava`)

## Installation

1. **Clone or download this project**

2. **Install Python dependencies**:
   ```bash
   pip install gradio Pillow requests
   ```

3. **Install Ollama** (if not already installed):
   - Download from: https://ollama.ai/
   - Or via terminal: `curl -fsSL https://ollama.dev/install.sh | sh`

4. **Pull a vision model**:
   ```bash
   ollama pull glm4v
   # or
   ollama pull llava
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
   - Select a vision model from the dropdown
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
│  (User Input)  │     │  (Processing)│    │ (Vision Model)│
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
   - Prompt is sent with the image to the selected vision model
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
- `ocr_image()`: Sends image to Ollama API and extracts text
- `build_viewer_html()`: Creates the interactive HTML viewer
- `process_images()`: Main processing pipeline with progress yields

## Project Details

### What It Does

- **Text Extraction**: Extracts all visible text from images using AI-powered vision models
- **Phone Number Detection**: Specifically looks for and extracts phone numbers
- **HTML Formatting**: Optionally preserves formatting like bold, italics, tables
- **Visual Comparison**: Shows side-by-side view of original image and extracted text
- **Batch Processing**: Handles multiple images in sequence with status updates

### Use Cases

- Digitizing printed documents
- Extracting text from screenshots
- Processing receipt images
- Converting scanned documents to text
- Extracting contact information from business cards
- Processing invoice images

### Configuration

The application connects to Ollama at `http://localhost:11434` (default). To change:

```python
# Modify this line in ocr-with-glm-ocr.py
OLLAMA_BASE = "http://localhost:11434"  # Change to your Ollama URL
```

### Model Recommendations

- `glm4v` - General purpose, good accuracy
- `llava` - Fast, lightweight option
- `llama3.2-vision` - Meta's vision model

## License

This project is provided as-is for educational and practical use.