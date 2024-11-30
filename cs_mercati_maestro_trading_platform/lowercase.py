#!/usr/bin/env python3

import os
import sys
import shutil
import datetime
import json
from pathlib import Path
from typing import Dict, Set, Tuple
import logging

class SafeRenamer:
    def __init__(self, start_path: str = '.'):
        self.start_path = Path(start_path).resolve()
        self.timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = self.start_path.parent / f'rename_backup_{self.timestamp}'
        
        # Create backup directory first
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        self.log_file = self.backup_dir / 'rename_log.txt'
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        
        # Store original and new paths for comparison
        self.original_paths: Set[Path] = set()
        self.new_paths: Set[Path] = set()
        
    def create_backup(self) -> bool:
        """Create a backup of the entire directory structure."""
        try:
            logging.info(f"Creating backup in: {self.backup_dir}")
            shutil.copytree(self.start_path, self.backup_dir / self.start_path.name)
            return True
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False
            
    def scan_directory(self) -> Dict[Path, Path]:
        """Scan directory and return mapping of original paths to lowercase paths."""
        changes = {}
        for path in sorted(self.start_path.rglob('*'), key=lambda x: len(x.parents), reverse=True):
            self.original_paths.add(path)
            lower_path = path.parent / path.name.lower()
            if path != lower_path:
                changes[path] = lower_path
        return changes
        
    def verify_changes(self) -> Tuple[bool, str]:
        """Compare current state with backup to verify integrity."""
        current_files = set(p for p in self.start_path.rglob('*'))
        
        # Check for missing files
        missing = self.original_paths - current_files
        unexpected = current_files - self.new_paths
        
        verification_report = []
        if missing:
            verification_report.append("Missing files after conversion:")
            verification_report.extend(f"  - {f}" for f in missing)
            
        if unexpected:
            verification_report.append("Unexpected files after conversion:")
            verification_report.extend(f"  - {f}" for f in unexpected)
            
        return not (missing or unexpected), "\n".join(verification_report)

    def generate_report(self) -> str:
        """Generate a detailed report of all changes."""
        report = [
            "=== Rename Operation Report ===",
            f"Timestamp: {self.timestamp}",
            f"Starting directory: {self.start_path}",
            f"Backup location: {self.backup_dir}",
            f"Log file: {self.log_file}",
            "\nDetailed changes:",
        ]
        
        # Add all logged changes from the log file
        with open(self.log_file) as f:
            log_contents = f.read()
        report.append(log_contents)
        
        return "\n".join(report)

    def rename_files(self, changes: Dict[Path, Path]) -> bool:
        """Perform the actual renaming operation."""
        success = True
        for original, new in changes.items():
            try:
                if new.exists() and original.resolve() != new.resolve():
                    logging.warning(f"Skipping {original} -> {new}: Target already exists")
                    success = False
                    continue
                    
                original.rename(new)
                self.new_paths.add(new)
                logging.info(f"Renamed: {original} -> {new}")
                
            except Exception as e:
                logging.error(f"Error renaming {original} to {new}: {e}")
                success = False
                
        return success

    def run(self):
        """Execute the complete rename operation with safety checks."""
        logging.info("Starting safe rename operation...")
        
        # Create backup
        if not self.create_backup():
            logging.error("Backup failed. Aborting.")
            return False
            
        # Scan for changes
        changes = self.scan_directory()
        if not changes:
            logging.info("No changes needed. All files are already lowercase.")
            return True
            
        # Show preview
        logging.info("\nProposed changes:")
        for old, new in changes.items():
            logging.info(f"{old} -> {new}")
            
        # Confirm
        response = input("\nProceed with these changes? (yes/no): ")
        if response.lower() != 'yes':
            logging.info("Operation cancelled by user.")
            return False
            
        # Perform renames
        success = self.rename_files(changes)
        
        # Verify
        verified, report = self.verify_changes()
        if verified:
            logging.info("All changes verified successfully!")
        else:
            logging.error("Verification failed!\n" + report)
            logging.info(f"Original files backed up at: {self.backup_dir}")
            
        # Generate final report
        with open(self.backup_dir / 'final_report.txt', 'w') as f:
            f.write(self.generate_report())
            
        logging.info(f"\nOperation complete. Check {self.backup_dir / 'final_report.txt'} for full details.")
        return success and verified

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Safely rename files and directories to lowercase with backup")
    parser.add_argument("path", nargs="?", default=".", help="Starting directory (default: current directory)")
    
    args = parser.parse_args()
    
    renamer = SafeRenamer(args.path)
    renamer.run()
