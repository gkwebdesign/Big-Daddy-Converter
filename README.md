# Image Converter - PNG/JPG ↔ WebP

A simple Windows tool to convert images between PNG/JPG and WebP formats. Supports both folder-based batch conversion and drag-and-drop GUI.

## Features

- ✅ Convert PNG/JPG → WebP
- ✅ Convert WebP → PNG
- ✅ Batch processing (entire folders)
- ✅ Drag-and-drop GUI
- ✅ Adjustable quality settings
- ✅ Recursive folder processing
- ✅ Standalone .exe (no Python required)

## Installation

### Option 1: Use Pre-built .exe (Easiest)

1. Download `image_converter.exe` from the [Releases](https://github.com/yourusername/image-converter/releases) page
2. Run the .exe - no installation needed!

### Option 2: Run from Source

1. Install Python 3.8 or higher
2. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/image-converter.git
   cd image-converter
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the script:
   ```bash
   python image_converter.py
   ```

## Usage

### GUI Mode (Default)

Simply run the script without arguments:

```bash
python image_converter.py
```

**Features:**
- Drag and drop images or folders onto the window
- Click "Select Files" to choose individual images
- Click "Select Folder" to convert all images in a folder
- Adjust quality slider (1-100)
- Set custom output folder (optional)

### Command Line Mode

#### Convert a Folder

```bash
python image_converter.py --folder ./images
```

This will:
- Convert all PNG/JPG images in `./images` to WebP
- Convert all WebP images to PNG
- Save converted images to `./images/converted/`

#### Custom Output Directory

```bash
python image_converter.py --folder ./images --output ./output
```

#### Adjust Quality

```bash
python image_converter.py --folder ./images --quality 85
```

Quality range: 1-100 (higher = better quality, larger file size)
- 90-100: High quality (recommended)
- 80-89: Good quality, smaller files
- 70-79: Moderate quality
- Below 70: Lower quality, very small files

#### Recursive Processing

```bash
python image_converter.py --folder ./images --recursive
```

Processes all subdirectories as well.

## Building the .exe

To create a standalone executable:

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Run the build script:
   ```bash
   python build_exe.py
   ```

   Or manually:
   ```bash
   pyinstaller --onefile --windowed --name "Image Converter" --icon=NONE image_converter.py
   ```

3. The .exe will be in the `dist/` folder

## Supported Formats

- **Input:** PNG, JPG, JPEG, WebP
- **Output:** 
  - PNG/JPG → WebP
  - WebP → PNG

## Examples

### Example 1: Convert folder to WebP
```bash
python image_converter.py --folder C:\Users\YourName\Pictures
```

### Example 2: Convert with custom quality
```bash
python image_converter.py --folder ./photos --quality 95
```

### Example 3: GUI with drag-and-drop
1. Run `python image_converter.py`
2. Drag images from Windows Explorer onto the window
3. Images are converted automatically!

## Troubleshooting

### "No module named 'PIL'"
Install dependencies:
```bash
pip install -r requirements.txt
```

### "No module named 'tkinterdnd2'"
Install the missing package:
```bash
pip install tkinterdnd2
```

### Images not converting
- Check that the file format is supported (PNG, JPG, JPEG, WebP)
- Ensure you have write permissions in the output directory
- Check the log/console for error messages

## License

MIT License - feel free to use and modify!

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.

