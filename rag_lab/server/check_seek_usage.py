"""Check all seek() usage in the codebase"""

import os
import re

def check_seek_usage():
    """Find all seek() calls that might cause NoneType errors"""
    
    print("Checking for potential seek() issues...")
    
    # Pattern to find seek calls and their return value usage
    patterns = [
        (r'(\w+)\s*=\s*.*\.seek\(', "Assigning seek() return value"),
        (r'await\s+(\w+)\.seek\(([^)]+)\)', "Async seek calls"),
        (r'\.seek\(([^)]+)\)', "All seek calls")
    ]
    
    services_dir = "modules/services"
    
    for root, dirs, files in os.walk(services_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for pattern_str, description in patterns:
                    pattern = re.compile(pattern_str)
                    
                    for i, line in enumerate(lines):
                        match = pattern.search(line)
                        if match:
                            print(f"\n{description}:")
                            print(f"  File: {file_path}")
                            print(f"  Line {i+1}: {line.strip()}")
                            
                            # Check context
                            if i > 0:
                                print(f"  Line {i}: {lines[i-1].strip()}")
                            if i < len(lines) - 1:
                                print(f"  Line {i+2}: {lines[i+1].strip()}")

if __name__ == "__main__":
    check_seek_usage()