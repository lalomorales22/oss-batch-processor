#!/usr/bin/env python3
"""
Universal Task Processor - Handles ANY task type with plugins
Supports web search, file operations, code execution, and more
"""

import json
import yaml
import time
import logging
import os
import re
import requests
import sqlite3
import threading
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
from abc import ABC, abstractmethod
import traceback

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, environment variables from .env file won't be loaded")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('universal_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TaskType(Enum):
    SEARCH = "search"
    PROCESS = "process"
    CREATE = "create"
    CHAIN = "chain"
    CODE = "code"
    CUSTOM = "custom"

class TaskStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class Task:
    id: str
    type: TaskType
    content: str
    config_name: str = None
    status: TaskStatus = TaskStatus.PENDING
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    created_at: str = ""
    updated_at: str = ""
    processing_time: float = 0
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()

# Plugin base class
class TaskPlugin(ABC):
    """Base class for task plugins"""
    
    @abstractmethod
    def execute(self, task: Task, context: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass

# Web Search Plugin
class WebSearchPlugin(TaskPlugin):
    def __init__(self, api_key: str = None, provider: str = "serper"):
        self.api_key = api_key or os.getenv('SERPER_API_KEY') or os.getenv('TAVILY_API_KEY')
        self.provider = provider
        
    def execute(self, task: Task, context: Dict[str, Any]) -> Any:
        """Execute web search"""
        query = task.metadata.get('search_query', task.content)
        
        if self.provider == "serper" and os.getenv('SERPER_API_KEY'):
            return self.search_serper(query)
        elif self.provider == "tavily" and os.getenv('TAVILY_API_KEY'):
            return self.search_tavily(query)
        else:
            logger.warning("No search API key found, returning mock results")
            return {"results": f"Mock search results for: {query}"}
    
    def search_serper(self, query: str) -> Dict:
        """Search using Serper API"""
        url = "https://google.serper.dev/search"
        headers = {
            'X-API-KEY': os.getenv('SERPER_API_KEY'),
            'Content-Type': 'application/json'
        }
        payload = {'q': query}
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Serper search error: {e}")
        return {}
    
    def search_tavily(self, query: str) -> Dict:
        """Search using Tavily API"""
        url = "https://api.tavily.com/search"
        payload = {
            'api_key': os.getenv('TAVILY_API_KEY'),
            'query': query,
            'search_depth': 'advanced'
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
        return {}
    
    def get_name(self) -> str:
        return "web_search"

# File Operations Plugin
class FileOperationsPlugin(TaskPlugin):
    def __init__(self, workspace_dir: str = "workspace"):
        self.workspace = Path(workspace_dir)
        self.workspace.mkdir(exist_ok=True)
        
    def execute(self, task: Task, context: Dict[str, Any]) -> Any:
        """Execute file operations"""
        # Get operation from step config first, then metadata
        step = context.get('step', {})
        operation = step.get('operation') or task.metadata.get('operation', 'create')
        
        # Get filename from template or metadata
        filename_template = step.get('filename_template', '')
        if filename_template:
            filename = filename_template.replace('{task_id}', task.id)
        else:
            filename = task.metadata.get('filename', f"{task.id}.txt")
        
        filepath = self.workspace / filename
        
        if operation == 'create':
            # Try to get content from various sources
            content = task.metadata.get('file_content', '')
            
            # If no explicit content, look for the last text result
            if not content and task.results:
                # Get the last non-plugin result (which would be LLM output)
                for key in reversed(list(task.results.keys())):
                    value = task.results[key]
                    if isinstance(value, str) and value.strip():
                        # Skip plugin results that look like status messages
                        if not value.startswith('Created file:') and not value.startswith('Error:'):
                            content = value
                            break
            
            if not content:
                content = task.results.get('final_output', '')
            
            # Write the content
            filepath.write_text(content, encoding='utf-8')
            return f"Created file: {filepath}"
        elif operation == 'edit':
            if filepath.exists():
                original = filepath.read_text()
                # Apply edits (simplified - in reality would be more complex)
                new_content = task.metadata.get('new_content', original)
                filepath.write_text(new_content, encoding='utf-8')
                return f"Edited file: {filepath}"
            else:
                return f"File not found for editing: {filepath}"
        elif operation == 'delete':
            if filepath.exists():
                filepath.unlink()
                return f"Deleted file: {filepath}"
        
        return f"File operation {operation} completed"
    
    def get_name(self) -> str:
        return "file_operations"

# Code Execution Plugin
class CodeExecutionPlugin(TaskPlugin):
    def __init__(self, allowed_languages: List[str] = None):
        self.allowed_languages = allowed_languages or ['python', 'javascript']
        
    def execute(self, task: Task, context: Dict[str, Any]) -> Any:
        """Execute code safely"""
        language = task.metadata.get('language', 'python')
        code = task.metadata.get('code', task.content)
        
        if language not in self.allowed_languages:
            return f"Language {language} not allowed"
        
        if language == 'python':
            return self.execute_python(code)
        elif language == 'javascript':
            return self.execute_javascript(code)
        
        return "Code execution completed"
    
    def execute_python(self, code: str) -> str:
        """Execute Python code in subprocess"""
        try:
            result = subprocess.run(
                ['python', '-c', code],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"Python execution error: {e}"
    
    def execute_javascript(self, code: str) -> str:
        """Execute JavaScript code"""
        try:
            result = subprocess.run(
                ['node', '-e', code],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout or result.stderr
        except Exception as e:
            return f"JavaScript execution error: {e}"
    
    def get_name(self) -> str:
        return "code_execution"

class UniversalTaskProcessor:
    def __init__(self, base_config: str = "processor_config.yaml"):
        self.base_config_file = Path(base_config)
        self.queue_file = Path("task_queue.json")
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        # Use data directory for database in Docker, current dir otherwise
        data_dir = Path("data")
        if data_dir.exists():
            self.db_path = data_dir / "universal_processor.db"
        else:
            self.db_path = Path("universal_processor.db")
        
        # Load base configuration
        self.config = self.load_base_config()
        
        # Task type configurations
        self.task_configs = {}
        self.load_task_configs()
        
        # Initialize plugins
        self.plugins: Dict[str, TaskPlugin] = {}
        self.init_plugins()
        
        # Ollama settings - check environment variable first
        self.api_base = os.getenv('OLLAMA_HOST') or self.config.get('ollama_host', 'http://localhost:11434')
        self.session = requests.Session()
        self.session.timeout = None  # No timeout
        
        # Initialize database
        self.init_database()
        
        # Task queue
        self.queue: List[Task] = []
        self.load_queue()
        
        # Processing control
        self.stop_processing = threading.Event()
        
    def init_plugins(self):
        """Initialize all plugins"""
        self.plugins['web_search'] = WebSearchPlugin()
        self.plugins['file_operations'] = FileOperationsPlugin()
        self.plugins['code_execution'] = CodeExecutionPlugin()
        logger.info(f"Initialized {len(self.plugins)} plugins")
        
    def load_base_config(self) -> dict:
        """Load base configuration"""
        if self.base_config_file.exists():
            with open(self.base_config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Create default config
            default_config = {
                'model': 'gpt-oss:20b',
                'ollama_host': 'http://localhost:11434',
                'delay_between_items': 2,
                'delay_between_steps': 1,
                'max_retries': 3,
                'save_interval': 5,
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': -1,
                'task_configs_dir': 'task_configs',
                'enable_web_api': True,
                'api_port': 5001
            }
            with open(self.base_config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            logger.info(f"Created default config at {self.base_config_file}")
            return default_config
    
    def load_task_configs(self):
        """Load all task type configurations"""
        config_dir = Path(self.config.get('task_configs_dir', 'task_configs'))
        config_dir.mkdir(exist_ok=True)
        
        # Create default task configs if they don't exist
        self.create_default_task_configs(config_dir)
        
        # Load all YAML configs
        for config_file in config_dir.glob('*.yaml'):
            task_type = config_file.stem
            with open(config_file, 'r') as f:
                self.task_configs[task_type] = yaml.safe_load(f)
            logger.info(f"Loaded config: {task_type}")
    
    def create_default_task_configs(self, config_dir: Path):
        """Create default task configuration files"""
        
        # Search tasks config
        if not (config_dir / 'search_tasks.yaml').exists():
            search_config = {
                'type': 'search',
                'steps': [
                    {
                        'name': 'web_search',
                        'plugin': 'web_search',
                        'prompt': None
                    },
                    {
                        'name': 'summarize',
                        'prompt': 'Summarize these search results in a clear, organized way: {web_search_results}'
                    },
                    {
                        'name': 'create_report',
                        'prompt': 'Create a detailed report based on this summary: {summarize_result}'
                    },
                    {
                        'name': 'save_report',
                        'plugin': 'file_operations',
                        'operation': 'create',
                        'filename_template': 'search_{task_id}.md'
                    }
                ]
            }
            with open(config_dir / 'search_tasks.yaml', 'w') as f:
                yaml.dump(search_config, f, default_flow_style=False)
        
        # Process tasks config
        if not (config_dir / 'process_tasks.yaml').exists():
            process_config = {
                'type': 'process',
                'steps': [
                    {
                        'name': 'analyze',
                        'prompt': 'Analyze this content and identify key points: {content}'
                    },
                    {
                        'name': 'improve',
                        'prompt': 'Improve and enhance this content: {content}'
                    },
                    {
                        'name': 'final_polish',
                        'prompt': 'Give this a final polish and make it perfect: {improve_result}'
                    }
                ]
            }
            with open(config_dir / 'process_tasks.yaml', 'w') as f:
                yaml.dump(process_config, f, default_flow_style=False)
        
        # Create tasks config
        if not (config_dir / 'create_tasks.yaml').exists():
            create_config = {
                'type': 'create',
                'steps': [
                    {
                        'name': 'outline',
                        'prompt': 'Create a detailed outline for: {content}'
                    },
                    {
                        'name': 'draft',
                        'prompt': 'Write a first draft based on this outline: {outline_result}'
                    },
                    {
                        'name': 'revise',
                        'prompt': 'Revise and improve this draft: {draft_result}'
                    },
                    {
                        'name': 'save_document',
                        'plugin': 'file_operations',
                        'operation': 'create',
                        'filename_template': 'created_{task_id}.md'
                    }
                ]
            }
            with open(config_dir / 'create_tasks.yaml', 'w') as f:
                yaml.dump(create_config, f, default_flow_style=False)
        
        # Code tasks config
        if not (config_dir / 'code_tasks.yaml').exists():
            code_config = {
                'type': 'code',
                'steps': [
                    {
                        'name': 'analyze_requirements',
                        'prompt': 'Analyze these requirements and plan the implementation: {content}'
                    },
                    {
                        'name': 'write_code',
                        'prompt': 'Write clean, working code based on this plan: {analyze_requirements_result}'
                    },
                    {
                        'name': 'add_tests',
                        'prompt': 'Add comprehensive tests for this code: {write_code_result}'
                    },
                    {
                        'name': 'save_code',
                        'plugin': 'file_operations',
                        'operation': 'create',
                        'filename_template': 'code_{task_id}.py'
                    }
                ]
            }
            with open(config_dir / 'code_tasks.yaml', 'w') as f:
                yaml.dump(code_config, f, default_flow_style=False)
    
    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                config_name TEXT,
                status TEXT NOT NULL,
                results TEXT,
                metadata TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processing_time REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def parse_task_file(self, filepath: str):
        """Parse task file with type markers"""
        file_path = Path(filepath)
        if not file_path.exists():
            logger.error(f"File not found: {filepath}")
            return
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Parse tasks with type markers like {search}, {process}, {create}, etc.
        task_pattern = r'\{(\w+)\}(.*?)(?=\{|\Z)'
        matches = re.findall(task_pattern, content, re.DOTALL)
        
        tasks_added = 0
        for task_type_str, task_content in matches:
            task_content = task_content.strip()
            if not task_content:
                continue
                
            # Map string to TaskType
            try:
                task_type = TaskType(task_type_str.lower())
            except ValueError:
                task_type = TaskType.CUSTOM
            
            # Parse any metadata in the task
            metadata = {}
            if '::' in task_content:
                # Format: metadata::actual_content
                meta_part, content_part = task_content.split('::', 1)
                # Parse metadata as key=value pairs
                for item in meta_part.split(','):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        metadata[key.strip()] = value.strip()
                task_content = content_part.strip()
            
            # Create task
            task_id = f"{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{tasks_added}"
            task = Task(
                id=task_id,
                type=task_type,
                content=task_content,
                config_name=f"{task_type.value}_tasks",
                metadata=metadata
            )
            
            self.queue.append(task)
            tasks_added += 1
        
        self.save_queue()
        logger.info(f"Added {tasks_added} tasks from {filepath}")
    
    def process_task(self, task: Task) -> bool:
        """Process a single task through its configured steps"""
        logger.info(f"Processing task: {task.id} (type: {task.type.value})")
        
        # Get task configuration
        config = self.task_configs.get(task.config_name, {})
        if not config:
            logger.error(f"No configuration found for {task.config_name}")
            return False
        
        task.status = TaskStatus.PROCESSING
        start_time = time.time()
        
        try:
            # Process each step in the configuration
            for step in config.get('steps', []):
                if self.stop_processing.is_set():
                    logger.info("Processing stop requested")
                    return False
                
                step_name = step['name']
                logger.info(f"  Step: {step_name}")
                
                # Check if this step uses a plugin
                if 'plugin' in step:
                    plugin_name = step['plugin']
                    if plugin_name in self.plugins:
                        plugin = self.plugins[plugin_name]
                        
                        # Prepare context for plugin
                        context = {
                            'task': task,
                            'step': step,
                            'previous_results': task.results
                        }
                        
                        # Execute plugin
                        result = plugin.execute(task, context)
                        task.results[step_name] = result
                        logger.info(f"    Plugin {plugin_name} completed")
                    else:
                        logger.warning(f"    Plugin {plugin_name} not found")
                
                # Check if this step has a prompt for LLM
                elif 'prompt' in step and step['prompt']:
                    prompt_template = step['prompt']
                    
                    # Replace variables in prompt
                    prompt = self.format_prompt(prompt_template, task)
                    
                    # Call Ollama
                    result = self.process_with_ollama(prompt)
                    task.results[step_name] = result
                    
                    # Save intermediate results
                    self.save_task_to_db(task)
                
                # Delay between steps
                if step != config['steps'][-1]:  # Not last step
                    delay = self.config.get('delay_between_steps', 1)
                    if delay > 0:
                        time.sleep(delay)
            
            task.status = TaskStatus.COMPLETED
            task.processing_time = time.time() - start_time
            task.updated_at = datetime.now().isoformat()
            
            # Save final results
            self.save_task_results(task)
            self.save_task_to_db(task)
            
            logger.info(f"✓ Completed task: {task.id} in {task.processing_time:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < self.config.get('max_retries', 3):
                task.status = TaskStatus.RETRYING
            else:
                task.status = TaskStatus.FAILED
            
            task.updated_at = datetime.now().isoformat()
            self.save_task_to_db(task)
            return False
    
    def format_prompt(self, template: str, task: Task) -> str:
        """Format prompt template with task data"""
        if not template:
            return ""
            
        prompt = template
        
        # Replace {content} with task content
        prompt = prompt.replace('{content}', task.content)
        
        # Replace {task_id} with task ID
        prompt = prompt.replace('{task_id}', task.id)
        
        # Replace results from previous steps - both with and without _result suffix
        for result_key, result_value in task.results.items():
            # Try with _result suffix for backward compatibility
            placeholder_result = f'{{{result_key}_result}}'
            if placeholder_result in prompt:
                prompt = prompt.replace(placeholder_result, str(result_value))
            
            # Try without suffix (new format)
            placeholder = f'{{{result_key}}}'
            if placeholder in prompt:
                # Format the result value appropriately
                if isinstance(result_value, dict):
                    formatted_value = json.dumps(result_value, indent=2)
                elif isinstance(result_value, list):
                    formatted_value = '\n'.join(str(item) for item in result_value)
                else:
                    formatted_value = str(result_value)
                prompt = prompt.replace(placeholder, formatted_value)
        
        # Replace metadata values
        for meta_key, meta_value in task.metadata.items():
            placeholder = f'{{{meta_key}}}'
            if placeholder in prompt:
                prompt = prompt.replace(placeholder, str(meta_value))
        
        # Handle any remaining placeholders with empty string to avoid errors
        import re
        remaining_placeholders = re.findall(r'\{[^}]+\}', prompt)
        for placeholder in remaining_placeholders:
            if placeholder not in ['{', '}']:  # Skip literal braces
                prompt = prompt.replace(placeholder, '')
        
        return prompt
    
    def process_with_ollama(self, prompt: str) -> str:
        """Process prompt with Ollama (no timeout)"""
        try:
            payload = {
                'model': self.config['model'],
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': self.config.get('temperature', 0.7),
                    'top_p': self.config.get('top_p', 0.9),
                    'num_predict': self.config.get('max_tokens', -1),
                }
            }
            
            logger.debug(f"Sending to Ollama: {len(prompt)} chars")
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=None  # No timeout
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                logger.debug(f"Ollama responded in {elapsed:.1f}s")
                return response_text
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise
    
    def save_task_results(self, task: Task):
        """Save task results to file"""
        result_file = self.results_dir / f"{task.id}.json"
        
        # Convert task to dict
        task_dict = asdict(task)
        task_dict['type'] = task.type.value
        task_dict['status'] = task.status.value
        
        with open(result_file, 'w') as f:
            json.dump(task_dict, f, indent=2)
    
    def save_task_to_db(self, task: Task):
        """Save task to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (id, type, content, config_name, status, results, metadata, 
                 error, retry_count, updated_at, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.type.value,
                task.content,
                task.config_name,
                task.status.value,
                json.dumps(task.results),
                json.dumps(task.metadata),
                task.error,
                task.retry_count,
                task.updated_at,
                task.processing_time
            ))
            
            conn.commit()
        finally:
            conn.close()
    
    def load_queue(self):
        """Load task queue from file"""
        if self.queue_file.exists():
            with open(self.queue_file, 'r') as f:
                data = json.load(f)
                self.queue = []
                for item_data in data:
                    # Convert strings back to enums
                    if 'type' in item_data:
                        item_data['type'] = TaskType(item_data['type'])
                    if 'status' in item_data:
                        item_data['status'] = TaskStatus(item_data['status'])
                    self.queue.append(Task(**item_data))
                logger.info(f"Loaded {len(self.queue)} tasks from queue")
    
    def save_queue(self):
        """Save queue to file"""
        queue_data = []
        for task in self.queue:
            task_dict = asdict(task)
            task_dict['type'] = task.type.value
            task_dict['status'] = task.status.value
            queue_data.append(task_dict)
        
        with open(self.queue_file, 'w') as f:
            json.dump(queue_data, f, indent=2)
    
    def clear_queue(self, clear_all=False):
        """Clear tasks from the queue
        
        Args:
            clear_all: If True, clear all tasks. If False, clear only pending tasks.
        """
        # Count tasks before clearing
        pending_count = sum(1 for task in self.queue if task.status == TaskStatus.PENDING)
        total_count = len(self.queue)
        
        if clear_all:
            # Clear all tasks
            cleared_count = len(self.queue)
            self.queue = []
            logger.info(f"Cleared ALL {cleared_count} tasks from queue")
        else:
            # Clear only pending tasks from queue
            self.queue = [task for task in self.queue if task.status != TaskStatus.PENDING]
            logger.info(f"Cleared {pending_count} pending tasks from queue (kept {len(self.queue)} non-pending tasks)")
        
        # Save the updated queue
        self.save_queue()
        
        return pending_count, total_count
    
    def run_batch(self):
        """Run all tasks in queue"""
        logger.info("=" * 50)
        logger.info("Starting Universal Task Processor")
        logger.info(f"Tasks in queue: {len(self.queue)}")
        logger.info("=" * 50)
        
        for task in self.queue:
            if task.status == TaskStatus.COMPLETED:
                continue
                
            success = self.process_task(task)
            
            # Save progress
            self.save_queue()
            
            # Delay between tasks
            delay = self.config.get('delay_between_items', 2)
            if delay > 0:
                time.sleep(delay)
        
        logger.info("Batch processing complete!")
    
    def start_web_api(self):
        """Start REST API for remote task submission"""
        from flask import Flask, request, jsonify
        
        app = Flask(__name__)
        
        @app.route('/add_task', methods=['POST'])
        def add_task():
            data = request.json
            task = Task(
                id=f"api_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                type=TaskType(data.get('type', 'process')),
                content=data['content'],
                config_name=data.get('config', 'process_tasks'),
                metadata=data.get('metadata', {})
            )
            self.queue.append(task)
            self.save_queue()
            return jsonify({'task_id': task.id, 'status': 'queued'})
        
        @app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                'total': len(self.queue),
                'pending': sum(1 for t in self.queue if t.status == TaskStatus.PENDING),
                'completed': sum(1 for t in self.queue if t.status == TaskStatus.COMPLETED),
                'failed': sum(1 for t in self.queue if t.status == TaskStatus.FAILED)
            })
        
        @app.route('/task/<task_id>', methods=['GET'])
        def get_task(task_id):
            task = next((t for t in self.queue if t.id == task_id), None)
            if task:
                task_dict = asdict(task)
                task_dict['type'] = task.type.value
                task_dict['status'] = task.status.value
                return jsonify(task_dict)
            return jsonify({'error': 'Task not found'}), 404
        
        port = self.config.get('api_port', 5001)
        logger.info(f"Starting web API on port {port}")
        app.run(host='0.0.0.0', port=port, threaded=True)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal Task Processor')
    parser.add_argument('--add-file', help='Add tasks from file')
    parser.add_argument('--run', action='store_true', help='Run batch processing')
    parser.add_argument('--api', action='store_true', help='Start REST API server')
    parser.add_argument('--status', action='store_true', help='Show queue status')
    parser.add_argument('--clear', action='store_true', help='Clear all pending tasks from queue')
    parser.add_argument('--clear-all', action='store_true', help='Clear ALL tasks from queue (including completed/failed)')
    
    args = parser.parse_args()
    
    processor = UniversalTaskProcessor()
    
    if args.add_file:
        processor.parse_task_file(args.add_file)
    elif args.run:
        processor.run_batch()
    elif args.api:
        processor.start_web_api()
    elif args.status:
        print(f"Tasks in queue: {len(processor.queue)}")
        for task_type in TaskType:
            count = sum(1 for t in processor.queue if t.type == task_type)
            if count > 0:
                print(f"  {task_type.value}: {count}")
    elif args.clear:
        # Show current status before clearing
        print(f"Current queue status: {len(processor.queue)} tasks")
        pending_count = sum(1 for t in processor.queue if t.status == TaskStatus.PENDING)
        print(f"  Pending: {pending_count}")
        print(f"  Processing/Completed/Failed: {len(processor.queue) - pending_count}")
        
        # Confirm before clearing
        if pending_count > 0:
            response = input(f"\nAre you sure you want to clear {pending_count} pending tasks? (y/N): ")
            if response.lower() == 'y':
                cleared, total = processor.clear_queue()
                print(f"✓ Cleared {cleared} pending tasks from queue")
                print(f"  Remaining tasks: {len(processor.queue)}")
            else:
                print("Clear operation cancelled")
        else:
            print("No pending tasks to clear")
    elif args.clear_all:
        # Show current status before clearing
        print(f"Current queue status: {len(processor.queue)} tasks")
        pending_count = sum(1 for t in processor.queue if t.status == TaskStatus.PENDING)
        print(f"  Pending: {pending_count}")
        print(f"  Processing/Completed/Failed: {len(processor.queue) - pending_count}")
        
        # Confirm before clearing ALL tasks
        if len(processor.queue) > 0:
            response = input(f"\n⚠️  Are you sure you want to clear ALL {len(processor.queue)} tasks? (y/N): ")
            if response.lower() == 'y':
                processor.clear_queue(clear_all=True)
                print(f"✓ Cleared ALL tasks from queue")
            else:
                print("Clear operation cancelled")
        else:
            print("No tasks to clear")
    else:
        print("Usage: python obp-CLI.py [--add-file tasks.txt] [--run] [--api] [--status] [--clear] [--clear-all]")

if __name__ == "__main__":
    main()