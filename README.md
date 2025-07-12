# Onyx Handwriting Optimization Tool

A Python CLI tool to easily enable/disable handwriting optimizations for apps on Onyx Boox e-readers by modifying the MMKV `onyx_config` database.

## Why This Tool?

Before this tool, enabling handwriting optimizations required:
1. Using the Mac-only Swift `mmkv-cli` tool
2. Manually extracting JSON configurations  
3. Figuring out obscure DrawViewKey values for each app
4. Escaping JSON properly when writing back to the database
5. Managing .crc checksums correctly

This tool simplifies the process dramatically, especially for popular apps with known configurations.

## Setup

0. **Clone the MMKV repository from here:** https://github.com/Tencent/MMKV
1. 
Now create a virtualenv to work in in the MMKV directory and activate it: `python3 -m venv venv && source venv/bin/activate`

2. **Build the MMKV Python bindings** (if not already done):
   ```bash
   cd /path/to/MMKV/Python
   python setup.py build_ext --inplace
   ```

3. **The tool is ready to use**:
   ```bash
   python onyx_handwriting_tool.py --help
   ```

## Quick Start

### For Popular Apps (Easiest)

The tool includes pre-configured settings for popular apps mentioned in the MobileRead forums:

```bash
# See all known apps
python onyx_handwriting_tool.py known

# Enable handwriting for Xodo PDF reader (one command!)
python onyx_handwriting_tool.py quick --app com.xodo.pdf.reader --database ./onyx_config

# Enable for Obsidian
python onyx_handwriting_tool.py quick --app md.obsidian --database ./onyx_config

### Managing Optimizations

```bash
# List all currently optimized apps
python onyx_handwriting_tool.py list --database ./onyx_config

# Show configuration for specific app
python onyx_handwriting_tool.py show --app com.xodo.pdf.reader --database ./onyx_config

# Disable handwriting optimization
python onyx_handwriting_tool.py disable --app com.xodo.pdf.reader --database ./onyx_config
```

## Known Apps Database

The tool includes DrawViewKeys for these popular apps:

| App | Package Name | DrawViewKey |
|-----|--------------|-------------|
| Xodo PDF Reader | `com.xodo.pdf.reader` | `com.pdftron.pdf.PDFViewCtrl` |
| Obsidian (Excalidraw/Ink) | `md.obsidian` | `com.getcapacitor.CapacitorWebView` |
| Squid | `com.steadfastinnovation.android.projectpapyrus` | `com.steadfastinnovation.android.projectpapyrus.ui.widget.PageViewContainer` |
| Ibis Paint X | `jp.ne.ibis.ibispaintx` | `jp.ne.ibis.ibispaintx.app.glwtk.IbisPaintView` |
| MediBang Paint | `com.medibang.android.paint.tablet` | `com.medibang.android.paint.tablet.ui.widget.CanvasView` |
| Joplin (Drawing plugin) | `org.joplin.react` | `com.reactnativecommunity.webview.RNCWebView` |
| Penly | `com.penly.penly` | `com.penly.penly.editor.views.EditorView` |
| DrawNote | `com.easyinnovation.notebook.gfree` | `com.dragonnest.app.view.DrawingContainerView` |

*Source: [MobileRead Forums Community Research](https://gist.github.com/calliecameron/b3c62c601d255630468bd493380e3b7e#gistcomment-5673800)*

### Note on "Not Found In Database" Error
Please note: you may have the script tell you an app that you know you have installed is not found in the database. This is most likely because you have never opened the "Optimization" menu for the app and made a change before. You have to do this once in order for the app to show up in the database. It doesn't matter what change you make; anything will work.

## Advanced Usage

### Custom Apps (When DrawViewKey is Known)

```bash
# Enable handwriting for a custom app
python onyx_handwriting_tool.py enable \
  --app com.myapp.package \
  --draw-view com.myapp.CustomDrawView \
  --activity com.myapp.MainActivity \
  --database ./onyx_config
```

### Discovering DrawViewKeys for Unknown Apps

The tool includes powerful discovery features to help find DrawViewKeys for new apps:

#### 1. Get Discovery Suggestions
```bash
# General discovery guide
python onyx_handwriting_tool.py discover

# App-specific suggestions
python onyx_handwriting_tool.py discover --app com.myapp.package
```

This analyzes patterns from known apps and suggests likely DrawViewKey candidates based on the app's package name.

#### 2. Test Potential DrawViewKeys
```bash
# Test a potential DrawViewKey
python onyx_handwriting_tool.py test \
  --app com.myapp.package \
  --draw-view com.myapp.ui.CanvasView \
  --activity com.myapp.MainActivity \
  --database ./onyx_config \
  --name "My Drawing App"
```

The test command:
- ✅ **Safely applies** the configuration with automatic backup
- 🧪 **Provides clear testing steps** for validation
- 📝 **Gives feedback instructions** for success/failure
- 🔄 **Easy restoration** if the DrawViewKey doesn't work

#### 3. Manual Discovery Methods
1. **Android debugging tools**: `adb shell dumpsys activity top` while the app is running
2. **APK analysis**: Decompile and search for View classes used for drawing  
3. **View hierarchy inspection**: Use developer tools to inspect active views
4. **Pattern analysis**: Common suffixes like `*DrawView`, `*CanvasView`, `*PaintView`
5. **Community research**: Check MobileRead forums for community discoveries

## Safety Features

- **Automatic backups**: Creates `.backup` files before any changes
- **Validation**: Checks that database and .crc files exist  
- **Error handling**: Won't corrupt database if something goes wrong
- **Read-only operations**: `list`, `show`, `known` commands don't modify anything

## How It Works

The tool modifies the MMKV `onyx_config` database by:

1. Reading the app's existing configuration
2. Adding an `activityConfigMap` entry with handwriting optimization settings
3. Setting the app-specific `drawViewKey` for pen/stylus recognition
4. Enabling note-taking features with proper stroke styling
5. Configuring display and refresh settings for optimal e-ink performance

## Getting Database Files

To use this tool, you need the `onyx_config` and `onyx_config.crc` files from your Onyx device:

1. **Root access required**: These files are in `/data/data/com.onyx.android.sdk/mmkv/`
2. **Copy to computer**: Use `adb pull` or file manager to copy both files
3. **Backup originals**: Always keep backups before making changes
4. **Copy back**: Transfer modified files back to device (matching permissions)

## Contributing

Found a DrawViewKey for a new app? Please contribute to the known apps database by:

1. Testing the app thoroughly with the new DrawViewKey
2. Submitting the package name, app name, DrawViewKey, and common activity names
3. Sharing results in the MobileRead forums or as a pull request

## Credits

- Built on the MMKV database research from the MobileRead Forums community
- DrawViewKey database compiled from [calliecameron's gist](https://gist.github.com/calliecameron/b3c62c601d255630468bd493380e3b7e#gistcomment-5673800)
- Uses Tencent's MMKV library Python bindings
