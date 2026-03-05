#!/usr/bin/env python3
"""
Log viewer for Q&A Cleaner application
"""
import os
import sys
from datetime import datetime

def view_logs(follow=False):
    """View application logs"""
    log_file = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
    
    if not os.path.exists(log_file):
        print(f"❌ Log file not found: {log_file}")
        print("   Run the application first to generate logs.")
        return
    
    print("=" * 80)
    print(f"📋 Q&A Cleaner Application Logs")
    print(f"📁 Log file: {log_file}")
    print(f"📊 File size: {os.path.getsize(log_file) / 1024:.2f} KB")
    print("=" * 80)
    print()
    
    if follow:
        # Follow mode (like tail -f)
        print("🔄 Following log file (Ctrl+C to stop)...\n")
        try:
            import subprocess
            subprocess.run(['tail', '-f', log_file])
        except KeyboardInterrupt:
            print("\n\n👋 Stopped following logs")
    else:
        # Show last 100 lines
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                num_lines = len(lines)
                display_lines = lines[-100:] if num_lines > 100 else lines
                
                if num_lines > 100:
                    print(f"... showing last 100 of {num_lines} lines ...\n")
                
                for line in display_lines:
                    print(line.rstrip())
        except Exception as e:
            print(f"❌ Error reading log file: {e}")

if __name__ == '__main__':
    follow_mode = '-f' in sys.argv or '--follow' in sys.argv
    
    if '--help' in sys.argv or '-h' in sys.argv:
        print("Usage: python view_logs.py [options]")
        print()
        print("Options:")
        print("  -f, --follow    Follow log file in real-time (like tail -f)")
        print("  -h, --help      Show this help message")
        print()
        print("Examples:")
        print("  python view_logs.py           # View last 100 log lines")
        print("  python view_logs.py -f        # Follow logs in real-time")
    else:
        view_logs(follow=follow_mode)
