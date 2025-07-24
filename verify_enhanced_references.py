#!/usr/bin/env python3
"""
Verification script for enhanced file references.

This script checks that files with "enhanced" in their name are properly
referenced throughout the codebase.
"""

import os
import re
import json
from typing import Dict, List, Set, Tuple

def print_section(title: str):
    """Print a section title"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def find_enhanced_files(root_dir: str) -> List[str]:
    """Find all files with 'enhanced' in their name"""
    enhanced_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if 'enhanced' in filename.lower():
                file_path = os.path.join(dirpath, filename)
                # Convert to relative path
                rel_path = os.path.relpath(file_path, root_dir)
                enhanced_files.append(rel_path)
    
    return enhanced_files

def find_references(root_dir: str, target_files: List[str]) -> Dict[str, List[str]]:
    """Find references to target files in the codebase"""
    references = {file: [] for file in target_files}
    
    # Create patterns to search for
    patterns = {}
    for file in target_files:
        # Get filename without extension
        filename = os.path.basename(file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Create patterns for different ways the file might be referenced
        patterns[file] = [
            re.compile(re.escape(file), re.IGNORECASE),  # Full path
            re.compile(re.escape(filename), re.IGNORECASE),  # Just filename
            re.compile(r'["\']' + re.escape(name_without_ext) + r'["\']', re.IGNORECASE),  # Name in quotes
            re.compile(r'import\s+' + re.escape(name_without_ext), re.IGNORECASE),  # Import statement
            re.compile(r'from\s+' + re.escape(name_without_ext), re.IGNORECASE),  # From import
            re.compile(r'require\(["\']' + re.escape(name_without_ext) + r'["\']', re.IGNORECASE),  # JS require
        ]
    
    # Search all files
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            # Skip binary files and node_modules
            if ('node_modules' in dirpath or
                filename.endswith(('.pyc', '.jpg', '.png', '.gif', '.ico', '.woff', '.ttf'))):
                continue
                
            file_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(file_path, root_dir)
            
            # Skip the target files themselves
            if rel_path in target_files:
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check for references
                    for target_file, file_patterns in patterns.items():
                        for pattern in file_patterns:
                            if pattern.search(content):
                                references[target_file].append(rel_path)
                                break  # Found a reference, no need to check other patterns
            except UnicodeDecodeError:
                # Skip binary files
                continue
    
    return references

def check_import_consistency(root_dir: str, references: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Check if imports are consistent across the codebase"""
    inconsistencies = {}
    
    for target_file, ref_files in references.items():
        # Skip if no references
        if not ref_files:
            continue
            
        # Get filename without extension
        filename = os.path.basename(target_file)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Check each reference file
        for ref_file in ref_files:
            file_path = os.path.join(root_dir, ref_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Look for different import patterns
                    import_patterns = [
                        (r'import\s+{\s*[^}]*' + re.escape(name_without_ext) + r'[^}]*}\s+from', 'destructured import'),
                        (r'import\s+' + re.escape(name_without_ext) + r'\s+from', 'default import'),
                        (r'from\s+["\'].*' + re.escape(name_without_ext) + r'["\']', 'python import'),
                        (r'require\(["\'].*' + re.escape(name_without_ext) + r'["\']', 'require'),
                    ]
                    
                    found_imports = []
                    for pattern, import_type in import_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            found_imports.append(import_type)
                    
                    # If multiple import styles found, flag as inconsistency
                    if len(found_imports) > 1:
                        if target_file not in inconsistencies:
                            inconsistencies[target_file] = []
                        inconsistencies[target_file].append((ref_file, found_imports))
            except UnicodeDecodeError:
                # Skip binary files
                continue
    
    return inconsistencies

def main():
    """Main function"""
    print_section("ENHANCED FILE REFERENCE VERIFICATION")
    
    # Get the root directory (current working directory)
    root_dir = os.getcwd()
    print(f"Checking references in: {root_dir}")
    
    # Find enhanced files
    enhanced_files = find_enhanced_files(root_dir)
    print(f"\nFound {len(enhanced_files)} files with 'enhanced' in their name:")
    for file in enhanced_files:
        print(f"  - {file}")
    
    # Find references
    references = find_references(root_dir, enhanced_files)
    
    # Check each enhanced file
    for file, refs in references.items():
        print(f"\nReferences to {file}:")
        if refs:
            print(f"  Found {len(refs)} references:")
            for ref in refs:
                print(f"  - {ref}")
        else:
            print("  WARNING: No references found!")
    
    # Check import consistency
    inconsistencies = check_import_consistency(root_dir, references)
    
    if inconsistencies:
        print("\nImport inconsistencies found:")
        for file, issues in inconsistencies.items():
            print(f"\n  Issues with {file}:")
            for ref_file, import_types in issues:
                print(f"  - {ref_file}: {', '.join(import_types)}")
    else:
        print("\nNo import inconsistencies found.")
    
    print_section("VERIFICATION COMPLETE")

if __name__ == "__main__":
    main()