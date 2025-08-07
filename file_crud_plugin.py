"""
Enhanced File Operations Plugin with full CRUD capabilities
"""

import os
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class EnhancedFileOperationsPlugin:
    """Enhanced file operations with full CRUD support"""
    
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        
    def execute(self, task: Any, context: Dict[str, Any]) -> Any:
        """Execute file operations based on task metadata"""
        operation = task.metadata.get('operation', 'create')
        
        operations_map = {
            'create': self.create_file,
            'read': self.read_file,
            'update': self.update_file,
            'delete': self.delete_file,
            'list': self.list_files,
            'search': self.search_files,
            'copy': self.copy_file,
            'move': self.move_file,
            'rename': self.rename_file,
            'mkdir': self.create_directory,
            'rmdir': self.remove_directory,
            'exists': self.check_exists,
            'info': self.get_file_info,
            'append': self.append_to_file,
            'backup': self.backup_file
        }
        
        if operation in operations_map:
            return operations_map[operation](task, context)
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    def create_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new file"""
        filename = self._get_filename(task)
        filepath = self.workspace / filename
        
        # Get content from various sources
        content = (
            task.metadata.get('file_content') or 
            task.results.get('final_output') or
            task.results.get('revise') or
            task.results.get('create_implementation') or
            task.results.get('write_code') or
            json.dumps(task.results, indent=2)
        )
        
        try:
            # Create parent directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
            if isinstance(content, dict) or isinstance(content, list):
                filepath.write_text(json.dumps(content, indent=2))
            else:
                filepath.write_text(str(content))
                
            return {
                "status": "success",
                "operation": "create",
                "filepath": str(filepath),
                "size": filepath.stat().st_size
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def read_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Read file contents"""
        filename = task.metadata.get('filename')
        if not filename:
            return {"status": "error", "message": "No filename specified"}
            
        filepath = self.workspace / filename
        
        try:
            if not filepath.exists():
                return {"status": "error", "message": f"File not found: {filename}"}
                
            content = filepath.read_text()
            
            # Try to parse as JSON if possible
            try:
                content = json.loads(content)
            except:
                pass
                
            return {
                "status": "success",
                "operation": "read",
                "filepath": str(filepath),
                "content": content,
                "size": filepath.stat().st_size
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def update_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing file"""
        filename = task.metadata.get('filename')
        if not filename:
            return {"status": "error", "message": "No filename specified"}
            
        filepath = self.workspace / filename
        
        if not filepath.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        try:
            # Backup original
            backup_path = filepath.with_suffix(filepath.suffix + '.bak')
            shutil.copy2(filepath, backup_path)
            
            # Get new content
            new_content = (
                task.metadata.get('new_content') or 
                task.metadata.get('file_content') or
                task.results.get('final_output', '')
            )
            
            # Update based on update mode
            update_mode = task.metadata.get('update_mode', 'replace')
            
            if update_mode == 'append':
                current = filepath.read_text()
                filepath.write_text(current + '\n' + str(new_content))
            elif update_mode == 'prepend':
                current = filepath.read_text()
                filepath.write_text(str(new_content) + '\n' + current)
            else:  # replace
                filepath.write_text(str(new_content))
            
            return {
                "status": "success",
                "operation": "update",
                "filepath": str(filepath),
                "backup": str(backup_path),
                "mode": update_mode
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file"""
        filename = task.metadata.get('filename')
        if not filename:
            return {"status": "error", "message": "No filename specified"}
            
        filepath = self.workspace / filename
        
        try:
            if filepath.exists():
                # Create backup before deletion
                if task.metadata.get('create_backup', True):
                    backup_dir = self.workspace / '.deleted'
                    backup_dir.mkdir(exist_ok=True)
                    backup_path = backup_dir / f"{filename}.deleted"
                    shutil.copy2(filepath, backup_path)
                
                filepath.unlink()
                return {
                    "status": "success",
                    "operation": "delete",
                    "filepath": str(filepath)
                }
            else:
                return {"status": "error", "message": f"File not found: {filename}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def list_files(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """List files in workspace"""
        pattern = task.metadata.get('pattern', '*')
        recursive = task.metadata.get('recursive', False)
        
        try:
            if recursive:
                files = list(self.workspace.rglob(pattern))
            else:
                files = list(self.workspace.glob(pattern))
            
            file_list = []
            for f in files:
                if f.is_file():
                    file_list.append({
                        "name": f.name,
                        "path": str(f.relative_to(self.workspace)),
                        "size": f.stat().st_size,
                        "modified": f.stat().st_mtime
                    })
            
            return {
                "status": "success",
                "operation": "list",
                "count": len(file_list),
                "files": file_list
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def search_files(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Search for text in files"""
        search_text = task.metadata.get('search_text', '')
        pattern = task.metadata.get('pattern', '*.txt')
        
        if not search_text:
            return {"status": "error", "message": "No search text specified"}
        
        try:
            matches = []
            for filepath in self.workspace.rglob(pattern):
                if filepath.is_file():
                    try:
                        content = filepath.read_text()
                        if search_text.lower() in content.lower():
                            # Find line numbers
                            lines = content.split('\n')
                            matching_lines = []
                            for i, line in enumerate(lines, 1):
                                if search_text.lower() in line.lower():
                                    matching_lines.append({
                                        "line_number": i,
                                        "content": line.strip()
                                    })
                            
                            matches.append({
                                "file": str(filepath.relative_to(self.workspace)),
                                "matches": matching_lines
                            })
                    except:
                        pass  # Skip binary files
            
            return {
                "status": "success",
                "operation": "search",
                "search_text": search_text,
                "files_found": len(matches),
                "matches": matches
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def copy_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Copy a file"""
        source = task.metadata.get('source')
        destination = task.metadata.get('destination')
        
        if not source or not destination:
            return {"status": "error", "message": "Source and destination required"}
        
        try:
            src_path = self.workspace / source
            dst_path = self.workspace / destination
            
            if not src_path.exists():
                return {"status": "error", "message": f"Source not found: {source}"}
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
            
            return {
                "status": "success",
                "operation": "copy",
                "source": str(src_path),
                "destination": str(dst_path)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def move_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Move a file"""
        source = task.metadata.get('source')
        destination = task.metadata.get('destination')
        
        if not source or not destination:
            return {"status": "error", "message": "Source and destination required"}
        
        try:
            src_path = self.workspace / source
            dst_path = self.workspace / destination
            
            if not src_path.exists():
                return {"status": "error", "message": f"Source not found: {source}"}
            
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src_path), str(dst_path))
            
            return {
                "status": "success",
                "operation": "move",
                "source": str(src_path),
                "destination": str(dst_path)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def rename_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a file"""
        old_name = task.metadata.get('old_name')
        new_name = task.metadata.get('new_name')
        
        if not old_name or not new_name:
            return {"status": "error", "message": "Old and new names required"}
        
        try:
            old_path = self.workspace / old_name
            new_path = self.workspace / new_name
            
            if not old_path.exists():
                return {"status": "error", "message": f"File not found: {old_name}"}
            
            old_path.rename(new_path)
            
            return {
                "status": "success",
                "operation": "rename",
                "old_name": old_name,
                "new_name": new_name
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def create_directory(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a directory"""
        dirname = task.metadata.get('dirname')
        if not dirname:
            return {"status": "error", "message": "Directory name required"}
        
        try:
            dirpath = self.workspace / dirname
            dirpath.mkdir(parents=True, exist_ok=True)
            
            return {
                "status": "success",
                "operation": "mkdir",
                "directory": str(dirpath)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def remove_directory(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Remove a directory"""
        dirname = task.metadata.get('dirname')
        if not dirname:
            return {"status": "error", "message": "Directory name required"}
        
        try:
            dirpath = self.workspace / dirname
            
            if not dirpath.exists():
                return {"status": "error", "message": f"Directory not found: {dirname}"}
            
            if dirpath.is_dir():
                shutil.rmtree(dirpath)
                return {
                    "status": "success",
                    "operation": "rmdir",
                    "directory": str(dirpath)
                }
            else:
                return {"status": "error", "message": f"Not a directory: {dirname}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def check_exists(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check if file or directory exists"""
        path = task.metadata.get('path')
        if not path:
            return {"status": "error", "message": "Path required"}
        
        filepath = self.workspace / path
        
        return {
            "status": "success",
            "operation": "exists",
            "path": path,
            "exists": filepath.exists(),
            "is_file": filepath.is_file() if filepath.exists() else False,
            "is_directory": filepath.is_dir() if filepath.exists() else False
        }
    
    def get_file_info(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed file information"""
        filename = task.metadata.get('filename')
        if not filename:
            return {"status": "error", "message": "Filename required"}
        
        filepath = self.workspace / filename
        
        if not filepath.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        try:
            stat = filepath.stat()
            return {
                "status": "success",
                "operation": "info",
                "filename": filename,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "created": stat.st_ctime,
                "is_file": filepath.is_file(),
                "is_directory": filepath.is_dir(),
                "extension": filepath.suffix
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def append_to_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Append content to file"""
        filename = task.metadata.get('filename')
        content = task.metadata.get('content', '')
        
        if not filename:
            return {"status": "error", "message": "Filename required"}
        
        filepath = self.workspace / filename
        
        try:
            # Create if doesn't exist
            if not filepath.exists():
                filepath.touch()
            
            with open(filepath, 'a') as f:
                f.write(str(content) + '\n')
            
            return {
                "status": "success",
                "operation": "append",
                "filepath": str(filepath),
                "size": filepath.stat().st_size
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def backup_file(self, task: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup of file"""
        filename = task.metadata.get('filename')
        if not filename:
            return {"status": "error", "message": "Filename required"}
        
        filepath = self.workspace / filename
        
        if not filepath.exists():
            return {"status": "error", "message": f"File not found: {filename}"}
        
        try:
            backup_dir = self.workspace / '.backups'
            backup_dir.mkdir(exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{filepath.stem}_{timestamp}{filepath.suffix}"
            backup_path = backup_dir / backup_name
            
            shutil.copy2(filepath, backup_path)
            
            return {
                "status": "success",
                "operation": "backup",
                "original": str(filepath),
                "backup": str(backup_path)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_filename(self, task: Any) -> str:
        """Get filename from task metadata or generate one"""
        if task.metadata.get('filename'):
            return task.metadata['filename']
        
        template = task.metadata.get('filename_template', '{task_id}.txt')
        filename = template.replace('{task_id}', task.id)
        
        # Add appropriate extension based on task type
        if task.type.value == 'code' and not filename.endswith(('.py', '.js', '.java')):
            lang = task.metadata.get('language', 'python')
            extensions = {
                'python': '.py',
                'javascript': '.js',
                'java': '.java',
                'cpp': '.cpp',
                'go': '.go',
                'rust': '.rs'
            }
            filename = filename.rsplit('.', 1)[0] + extensions.get(lang, '.txt')
        
        return filename
    
    def get_name(self) -> str:
        return "enhanced_file_operations"