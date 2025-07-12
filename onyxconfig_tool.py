#!/usr/bin/env python3
"""
Onyx Handwriting Optimization Tool

A CLI tool to enable/disable handwriting optimizations for apps in Onyx Boox e-readers
by modifying the MMKV onyx_config database.

Usage:
    python onyxconfig_tool.py enable --app com.xodo.pdf.reader --draw-view MyDrawView --database ./onyx_config
    python onyxconfig_tool.py disable --app com.xodo.pdf.reader --database ./onyx_config  
    python onyxconfig_tool.py list --database ./onyx_config
    python onyxconfig_tool.py show --app com.xodo.pdf.reader --database ./onyx_config
"""

import argparse
import json
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import MMKV - ensure we're in the right directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import mmkv
except ImportError:
    print("Error: MMKV Python module not found. Please build it first:")
    print("cd /path/to/MMKV/Python && python setup.py build_ext --inplace")
    sys.exit(1)


# Known DrawViewKeys for popular apps
KNOWN_APPS = {
    "com.xodo.pdf.reader": {
        "name": "Xodo PDF Reader",
        "drawViewKey": "com.pdftron.pdf.PDFViewCtrl",
        "commonActivities": [
            "com.xodo.presentation.activity.TabletReaderActivity",
            "com.xodo.presentation.activity.ReaderActivity"
        ]
    },
    "com.steadfastinnovation.android.projectpapyrus": {
        "name": "Squid",
        "drawViewKey": "com.steadfastinnovation.android.projectpapyrus.ui.widget.PageViewContainer",
        "commonActivities": [
            "com.steadfastinnovation.android.projectpapyrus.ui.MainActivity"
        ]
    },
    "md.obsidian": {
        "name": "Obsidian (Excalidraw/Ink)",
        "drawViewKey": "com.getcapacitor.CapacitorWebView",
        "commonActivities": [
            "md.obsidian.MainActivity"
        ]
    },
    "com.penly.penly": {
        "name": "Penly",
        "drawViewKey": "com.penly.penly.editor.views.EditorView",
        "commonActivities": [
            "com.penly.penly.editor.EditorActivity"
        ]
    },
    "jp.ne.ibis.ibispaintx": {
        "name": "Ibis Paint X",
        "drawViewKey": "jp.ne.ibis.ibispaintx.app.glwtk.IbisPaintView",
        "commonActivities": [
            "jp.ne.ibis.ibispaintx.app.MainActivity"
        ]
    },
    "com.medibang.android.paint.tablet": {
        "name": "MediBang Paint",
        "drawViewKey": "com.medibang.android.paint.tablet.ui.widget.CanvasView",
        "commonActivities": [
            "com.medibang.android.paint.tablet.MainActivity"
        ]
    },
    "org.joplin.react": {
        "name": "Joplin (Drawing plugin)",
        "drawViewKey": "com.reactnativecommunity.webview.RNCWebView",
        "commonActivities": [
            "org.joplin.react.MainActivity"
        ]
    },
    "com.easyinnovation.notebook.gfree": {
        "name": "DrawNote",
        "drawViewKey": "com.dragonnest.app.view.DrawingContainerView",
        "commonActivities": [
            "com.easyinnovation.notebook.gfree.MainActivity"
        ]
    },
    "com.microsoft.office.onenote": {
        "name": "Microsoft OneNote",
        "drawViewKey": "com.microsoft.office.onenote.drawing.CanvasView",
        "commonActivities": [
            "com.microsoft.office.onenote.ui.main.MainActivity"
        ]
    }
}


class OnyxMMKVHandler:
    """Handler for Onyx MMKV database operations."""
    
    def __init__(self, database_path: str):
        """
        Initialize MMKV handler.
        
        Args:
            database_path: Path to the onyx_config file
        """
        self.database_path = Path(database_path)
        self.database_dir = self.database_path.parent
        self.database_name = self.database_path.stem
        self.crc_path = self.database_path.with_suffix('.crc')
        
        # Validate files exist
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database file not found: {self.database_path}")
        if not self.crc_path.exists():
            raise FileNotFoundError(f"CRC file not found: {self.crc_path}")
            
        # Initialize MMKV
        mmkv.MMKV.initializeMMKV(str(self.database_dir))
        self.db = mmkv.MMKV(self.database_name, mmkv.MMKVMode.SingleProcess)
        
    def backup_database(self) -> Tuple[Path, Path]:
        """Create backup copies of database and CRC files."""
        backup_db = self.database_path.with_suffix('.backup')
        backup_crc = self.crc_path.with_suffix('.crc.backup')
        
        shutil.copy2(self.database_path, backup_db)
        shutil.copy2(self.crc_path, backup_crc)
        
        return backup_db, backup_crc
        
    def get_app_config(self, package_name: str) -> Optional[Dict]:
        """Get configuration for a specific app."""
        key = f"eac_app_{package_name}"
        try:
            config_str = self.db.getString(key)
            return json.loads(config_str)
        except Exception:
            return None
            
    def set_app_config(self, package_name: str, config: Dict) -> bool:
        """Set configuration for a specific app."""
        key = f"eac_app_{package_name}"
        try:
            config_str = json.dumps(config, separators=(',', ':'))
            self.db.set(key, config_str)
            return True
        except Exception as e:
            print(f"Error setting config: {e}")
            return False
            
    def list_all_apps(self) -> List[str]:
        """List all apps in the database."""
        keys = self.db.keys()
        apps = []
        for key in keys:
            if key.startswith('eac_app_'):
                package_name = key[8:]  # Remove 'eac_app_' prefix
                apps.append(package_name)
        return sorted(apps)
        
    def list_optimized_apps(self) -> List[Tuple[str, List[str]]]:
        """List apps that have handwriting optimization enabled."""
        optimized = []
        for app in self.list_all_apps():
            config = self.get_app_config(app)
            if config and config.get('activityConfigMap'):
                activities_with_drawing = []
                for activity_name, activity_config in config['activityConfigMap'].items():
                    note_config = activity_config.get('noteConfig', {})
                    if note_config.get('enable') and note_config.get('drawViewKey'):
                        activities_with_drawing.append({
                            'activity': activity_name,
                            'drawViewKey': note_config['drawViewKey']
                        })
                if activities_with_drawing:
                    optimized.append((app, activities_with_drawing))
        return optimized


class HandwritingOptimizer:
    """Logic for enabling/disabling handwriting optimizations."""
    
    @staticmethod
    def create_activity_config(draw_view_key: str, activity_name: str) -> Dict:
        """Create a handwriting-optimized activity configuration."""
        return {
            "clsName": activity_name,
            "disableScrollAnim": False,
            "displayConfig": {
                "bwMode": 0,
                "cfaColorBrightness": 0,
                "cfaColorSaturation": 0,
                "cfaColorSaturationMin": 60,
                "contrast": 30,
                "ditherThreshold": 128,
                "enable": True,
                "enhance": True,
                "monoLevel": 10
            },
            "enable": True,
            "noteConfig": {
                "compatibleVersionCode": 0,
                "drawViewKey": draw_view_key,
                "enable": True,
                "globalStrokeStyle": {
                    "enable": True,
                    "strokeColor": -16777216,  # Black
                    "strokeExtraArgs": [],
                    "strokeParams": [],
                    "strokeStyle": 0,  # Pen style
                    "strokeWidth": 3
                },
                "repaintLatency": 500,
                "styleMap": {},
                "supportNoteConfig": True
            },
            "paintConfig": {
                "antiAlisingType": 0,
                "ditherBitmap": False,
                "enable": True,
                "fillBrightness": 0,
                "fillContrast": 0,
                "fillEAC": False,
                "iconBrightness": 0,
                "iconContrast": 0,
                "iconEAC": False,
                "iconThreshold": 0,
                "imgEAC": True,
                "imgGamma": 60,
                "quantBits": 3,
                "textBold": False,
                "textEACType": 0
            },
            "refreshConfig": {
                "animationDuration": 50,
                "antiFlicker": 10,
                "enable": True,
                "gcInterval": 20,
                "supportRegal": False,
                "turbo": 2,
                "updateMode": 2,
                "useGCForNewSurface": False
            }
        }
    
    @staticmethod 
    def enable_handwriting(handler: OnyxMMKVHandler, package_name: str, 
                          draw_view_key: str, activity_name: str) -> bool:
        """Enable handwriting optimization for an app."""
        config = handler.get_app_config(package_name)
        if not config:
            print(f"Error: App {package_name} not found in database")
            return False
            
        # Create or update activity config map
        if 'activityConfigMap' not in config:
            config['activityConfigMap'] = {}
            
        # Add the handwriting-optimized activity
        activity_config = HandwritingOptimizer.create_activity_config(draw_view_key, activity_name)
        config['activityConfigMap'][activity_name] = activity_config
        
        return handler.set_app_config(package_name, config)
    
    @staticmethod
    def disable_handwriting(handler: OnyxMMKVHandler, package_name: str, 
                           activity_name: Optional[str] = None) -> bool:
        """Disable handwriting optimization for an app or specific activity."""
        config = handler.get_app_config(package_name)
        if not config:
            print(f"Error: App {package_name} not found in database")
            return False
            
        activity_map = config.get('activityConfigMap', {})
        if not activity_map:
            print(f"No optimizations found for {package_name}")
            return True
            
        if activity_name:
            # Remove specific activity
            if activity_name in activity_map:
                del activity_map[activity_name]
                print(f"Removed optimization for activity: {activity_name}")
            else:
                print(f"Activity {activity_name} not found")
                return False
        else:
            # Remove all activities with handwriting optimization
            to_remove = []
            for act_name, act_config in activity_map.items():
                note_config = act_config.get('noteConfig', {})
                if note_config.get('enable') and note_config.get('drawViewKey'):
                    to_remove.append(act_name)
            
            for act_name in to_remove:
                del activity_map[act_name]
                print(f"Removed optimization for activity: {act_name}")
        
        return handler.set_app_config(package_name, config)


def main():
    parser = argparse.ArgumentParser(
        description="Onyx Handwriting Optimization Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick enable handwriting for known apps (easiest method)
  python onyxconfig_tool.py quick --app com.xodo.pdf.reader --database ./onyx_config
  python onyxconfig_tool.py quick --app md.obsidian --database ./onyx_config

  # List all known apps with pre-configured settings
  python onyxconfig_tool.py known

  # Discover DrawViewKeys for unknown apps
  python onyxconfig_tool.py discover --app com.myapp.package
  
  # Test a potential DrawViewKey for an unknown app
  python onyxconfig_tool.py test --app com.myapp.package \\
    --draw-view com.myapp.DrawingView --activity com.myapp.MainActivity \\
    --database ./onyx_config --name "My App"

  # Manual enable for custom apps (when you know the DrawViewKey)
  python onyxconfig_tool.py enable --app com.xodo.pdf.reader \\
    --draw-view com.pdftron.pdf.PDFViewCtrl --activity com.xodo.presentation.activity.ReaderActivity \\
    --database ./onyx_config

  # Disable handwriting optimizations
  python onyxconfig_tool.py disable --app com.xodo.pdf.reader --database ./onyx_config

  # List all currently optimized apps
  python onyxconfig_tool.py list --database ./onyx_config

  # Show configuration for specific app
  python onyxconfig_tool.py show --app com.xodo.pdf.reader --database ./onyx_config
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Enable command
    enable_parser = subparsers.add_parser('enable', help='Enable handwriting optimization')
    enable_parser.add_argument('--app', required=True, help='App package name (e.g., com.xodo.pdf.reader)')
    enable_parser.add_argument('--draw-view', required=True, help='Draw view key for the app')
    enable_parser.add_argument('--activity', required=True, help='Activity class name')
    enable_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    enable_parser.add_argument('--backup', action='store_true', default=True, help='Create backup (default: True)')
    
    # Disable command
    disable_parser = subparsers.add_parser('disable', help='Disable handwriting optimization')
    disable_parser.add_argument('--app', required=True, help='App package name')
    disable_parser.add_argument('--activity', help='Specific activity to disable (optional)')
    disable_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    disable_parser.add_argument('--backup', action='store_true', default=True, help='Create backup (default: True)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List apps with handwriting optimization')
    list_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    list_parser.add_argument('--all', action='store_true', help='List all apps in database')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show configuration for specific app')
    show_parser.add_argument('--app', required=True, help='App package name')
    show_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    
    # Known apps command
    known_parser = subparsers.add_parser('known', help='List known apps with pre-configured DrawViewKeys')
    known_parser.add_argument('--app', help='Show details for specific known app')
    
    # Quick enable command for known apps
    quick_parser = subparsers.add_parser('quick', help='Quickly enable optimization for known apps')
    quick_parser.add_argument('--app', required=True, help='App package name (must be in known apps)')
    quick_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    quick_parser.add_argument('--activity', help='Specific activity (uses first common activity if not specified)')
    quick_parser.add_argument('--backup', action='store_true', default=True, help='Create backup (default: True)')
    
    # Test command for discovering DrawViewKeys
    test_parser = subparsers.add_parser('test', help='Test potential DrawViewKeys for unknown apps')
    test_parser.add_argument('--app', required=True, help='App package name')
    test_parser.add_argument('--draw-view', required=True, help='DrawViewKey to test')
    test_parser.add_argument('--activity', required=True, help='Activity class name to test')
    test_parser.add_argument('--database', required=True, help='Path to onyx_config file')
    test_parser.add_argument('--name', help='Friendly name for the app (for output)')
    test_parser.add_argument('--backup', action='store_true', default=True, help='Create backup (default: True)')
    
    # Discover command to suggest common DrawViewKey patterns
    discover_parser = subparsers.add_parser('discover', help='Get suggestions for discovering DrawViewKeys')
    discover_parser.add_argument('--app', help='App package name to analyze')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    try:
        # Handle commands that don't need database access
        if args.command == 'known':
            if args.app:
                if args.app in KNOWN_APPS:
                    app_info = KNOWN_APPS[args.app]
                    print(f"Known app: {app_info['name']}")
                    print(f"Package: {args.app}")
                    print(f"DrawViewKey: {app_info['drawViewKey']}")
                    print(f"Common Activities:")
                    for activity in app_info['commonActivities']:
                        print(f"  - {activity}")
                else:
                    print(f"App {args.app} not found in known apps database")
                    print("Use 'known' command without --app to see all known apps")
            else:
                print(f"Known apps with pre-configured DrawViewKeys ({len(KNOWN_APPS)}):")
                for package, info in KNOWN_APPS.items():
                    print(f"  {package}")
                    print(f"    Name: {info['name']}")
                    print(f"    DrawViewKey: {info['drawViewKey']}")
                    print()
            return
            
        elif args.command == 'discover':
            print("🔍 DrawViewKey Discovery Guide")
            print("=" * 50)
            
            # Analyze patterns from known apps
            print("\nCommon DrawViewKey patterns from known apps:")
            patterns = {}
            for package, info in KNOWN_APPS.items():
                draw_view = info['drawViewKey']
                if 'View' in draw_view:
                    pattern = draw_view.split('.')[-1]  # Get the class name
                    if pattern not in patterns:
                        patterns[pattern] = []
                    patterns[pattern].append(info['name'])
            
            for pattern, apps in patterns.items():
                print(f"  {pattern}: {', '.join(apps)}")
            
            print("\n🎯 Common View class suffixes to try:")
            common_suffixes = [
                "DrawView", "CanvasView", "PaintView", "DrawingView", 
                "PDFViewCtrl", "WebView", "RenderView", "EditorView",
                "NoteView", "SketchView", "InkView", "PenView"
            ]
            for suffix in common_suffixes:
                print(f"  *{suffix}")
            
            if args.app:
                print(f"\n📱 Suggestions for {args.app}:")
                package_parts = args.app.split('.')
                base_package = '.'.join(package_parts[:-1]) if len(package_parts) > 2 else args.app
                
                suggestions = []
                for suffix in common_suffixes:
                    suggestions.append(f"{base_package}.{suffix}")
                    suggestions.append(f"{args.app}.{suffix}")
                    if len(package_parts) >= 3:
                        suggestions.append(f"{package_parts[0]}.{package_parts[1]}.ui.{suffix}")
                        suggestions.append(f"{package_parts[0]}.{package_parts[1]}.view.{suffix}")
                
                for i, suggestion in enumerate(suggestions[:10], 1):
                    print(f"  {i:2}. {suggestion}")
                    
                print(f"\n🛠️  Test these with:")
                print(f"python onyx_handwriting_tool.py test --app {args.app} \\")
                print(f"  --draw-view <DrawViewKey> --activity <ActivityName> --database ./onyx_config")
            
            print("\n📚 Discovery methods:")
            print("1. Android debugging: adb shell dumpsys activity top")
            print("2. APK analysis: Search for *View classes in decompiled code")
            print("3. Inspect app's view hierarchy while drawing")
            print("4. Check similar apps' patterns")
            print("5. Community forums: MobileRead, Reddit r/Onyx_Boox")
            return
            
        # For all other commands, we need database access
        handler = OnyxMMKVHandler(args.database)
        
        if args.command == 'enable':
            if args.backup:
                backup_db, backup_crc = handler.backup_database()
                print(f"Created backups: {backup_db}, {backup_crc}")
                
            success = HandwritingOptimizer.enable_handwriting(
                handler, args.app, args.draw_view, args.activity
            )
            if success:
                print(f"✓ Enabled handwriting optimization for {args.app}")
                print(f"  Activity: {args.activity}")
                print(f"  Draw View: {args.draw_view}")
            else:
                print(f"✗ Failed to enable optimization for {args.app}")
                
        elif args.command == 'disable':
            if args.backup:
                backup_db, backup_crc = handler.backup_database()
                print(f"Created backups: {backup_db}, {backup_crc}")
                
            success = HandwritingOptimizer.disable_handwriting(
                handler, args.app, args.activity
            )
            if success:
                print(f"✓ Disabled handwriting optimization for {args.app}")
            else:
                print(f"✗ Failed to disable optimization for {args.app}")
                
        elif args.command == 'list':
            if args.all:
                apps = handler.list_all_apps()
                print(f"All apps in database ({len(apps)}):")
                for app in apps:
                    print(f"  {app}")
            else:
                optimized = handler.list_optimized_apps()
                print(f"Apps with handwriting optimization ({len(optimized)}):")
                for app, activities in optimized:
                    print(f"  {app}:")
                    for activity_info in activities:
                        print(f"    - {activity_info['activity']} (view: {activity_info['drawViewKey']})")
                        
        elif args.command == 'show':
            config = handler.get_app_config(args.app)
            if config:
                print(f"Configuration for {args.app}:")
                activity_map = config.get('activityConfigMap', {})
                if activity_map:
                    print("  Activity configurations:")
                    for activity_name, activity_config in activity_map.items():
                        note_config = activity_config.get('noteConfig', {})
                        if note_config.get('enable') and note_config.get('drawViewKey'):
                            print(f"    ✓ {activity_name} (handwriting enabled)")
                            print(f"      Draw View: {note_config.get('drawViewKey')}")
                        else:
                            print(f"    - {activity_name} (no handwriting)")
                else:
                    print("  No activity configurations")
            else:
                print(f"App {args.app} not found in database")
                    
        elif args.command == 'quick':
            if args.app not in KNOWN_APPS:
                print(f"Error: {args.app} is not in the known apps database")
                print("Use 'known' command to see available apps, or use 'enable' for custom configuration")
                sys.exit(1)
                
            app_info = KNOWN_APPS[args.app]
            activity = args.activity or app_info['commonActivities'][0]
            
            if args.backup:
                backup_db, backup_crc = handler.backup_database()
                print(f"Created backups: {backup_db}, {backup_crc}")
                
            success = HandwritingOptimizer.enable_handwriting(
                handler, args.app, app_info['drawViewKey'], activity
            )
            if success:
                print(f"✓ Enabled handwriting optimization for {app_info['name']}")
                print(f"  Package: {args.app}")
                print(f"  Activity: {activity}")
                print(f"  Draw View: {app_info['drawViewKey']}")
            else:
                print(f"✗ Failed to enable optimization for {args.app}")
                
        elif args.command == 'test':
            app_name = args.name or args.app
            print(f"🧪 Testing DrawViewKey for {app_name}")
            print(f"Package: {args.app}")
            print(f"DrawViewKey: {args.draw_view}")
            print(f"Activity: {args.activity}")
            print()
            
            # Check if app exists in database
            config = handler.get_app_config(args.app)
            if not config:
                print(f"❌ App {args.app} not found in database")
                print("Make sure the app is installed and has been launched at least once")
                return
                
            if args.backup:
                backup_db, backup_crc = handler.backup_database()
                print(f"📦 Created backups: {backup_db.name}, {backup_crc.name}")
                
            # Enable the test configuration
            success = HandwritingOptimizer.enable_handwriting(
                handler, args.app, args.draw_view, args.activity
            )
            
            if success:
                print(f"✅ Test configuration applied successfully!")
                print()
                print("🧪 Testing steps:")
                print("1. Copy the modified onyx_config and onyx_config.crc back to your device")
                print("2. Restart the target app")
                print("3. Try drawing/writing with your stylus in the app")
                print("4. Check if handwriting recognition works")
                print()
                print("✅ If handwriting works:")
                print(f"   This DrawViewKey is CORRECT for {app_name}!")
                print(f"   Consider sharing: {args.app} -> {args.draw_view}")
                print()
                print("❌ If handwriting doesn't work:")
                print("   Try a different DrawViewKey using 'discover' command")
                print(f"   Restore from backup: cp {backup_db.name} onyx_config")
                print()
                print("⚠️  Remember to test thoroughly before using permanently!")
                
            else:
                print(f"❌ Failed to apply test configuration")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
