#!/usr/bin/env python3
"""
OSS at Night - Overnight AI Assistant
Single file with web interface for local network access
Run: python task_processor_gui.py
Access: http://your-ip:5001
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
import socket
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
from flask import Flask, render_template_string, request, jsonify, send_file
from flask_cors import CORS
import traceback

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("python-dotenv not installed, environment variables from .env file won't be loaded")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enums
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

# Data classes
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

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OSS at Night - Overnight AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --background: #0a0a0a;
            --foreground: #fafafa;
            --muted: #171717;
            --muted-foreground: #a3a3a3;
            --border: #262626;
            --input: #171717;
            --primary: #3b82f6;
            --primary-foreground: #ffffff;
            --secondary: #1f1f1f;
            --secondary-foreground: #e5e5e5;
            --accent: #262626;
            --accent-foreground: #fafafa;
            --destructive: #dc2626;
            --destructive-foreground: #ffffff;
            --ring: #3b82f6;
            --radius: 0.75rem;
            --glow: rgba(59, 130, 246, 0.5);
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--background);
            background-image: 
                radial-gradient(ellipse at top, rgba(59, 130, 246, 0.1) 0%, transparent 50%),
                radial-gradient(ellipse at bottom, rgba(139, 92, 246, 0.05) 0%, transparent 50%);
            color: var(--foreground);
            line-height: 1.5;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        header {
            border-bottom: 1px solid var(--border);
            padding-bottom: 2rem;
            margin-bottom: 2rem;
        }
        
        h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: var(--muted-foreground);
            font-size: 0.875rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-bottom: 2rem;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
        }
        
        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.7;
            }
        }
        
        @keyframes spin {
            to {
                transform: rotate(360deg);
            }
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* Custom Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 10px;
            height: 10px;
        }
        
        ::-webkit-scrollbar-track {
            background: rgba(23, 23, 23, 0.5);
            border-radius: 5px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 5px;
            border: 2px solid rgba(23, 23, 23, 0.5);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
        }
        
        /* Firefox scrollbar */
        * {
            scrollbar-width: thin;
            scrollbar-color: #3b82f6 rgba(23, 23, 23, 0.5);
        }
        
        .card {
            background: rgba(23, 23, 23, 0.5);
            backdrop-filter: blur(10px);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            animation: fadeIn 0.3s ease-out;
        }
        
        .card-header {
            margin-bottom: 1rem;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.25rem;
        }
        
        .card-description {
            color: var(--muted-foreground);
            font-size: 0.875rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        
        input, textarea, select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid var(--border);
            border-radius: calc(var(--radius) - 2px);
            font-size: 0.875rem;
            transition: border-color 0.15s;
            background: var(--input);
            color: var(--foreground);
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--ring);
            box-shadow: 0 0 0 3px var(--glow);
        }
        
        textarea {
            min-height: 100px;
            resize: vertical;
            font-family: inherit;
        }
        
        .button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0.5rem 1rem;
            font-size: 0.875rem;
            font-weight: 500;
            border-radius: calc(var(--radius) - 2px);
            border: 1px solid transparent;
            cursor: pointer;
            transition: all 0.15s;
            text-decoration: none;
        }
        
        .button-primary {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: var(--primary-foreground);
            border: none;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
        }
        
        .button-primary:hover {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.5);
            transform: translateY(-1px);
        }
        
        .button-secondary {
            background: var(--secondary);
            color: var(--secondary-foreground);
            border-color: var(--border);
        }
        
        .button-secondary:hover {
            background: var(--accent);
        }
        
        .button-destructive {
            background: var(--destructive);
            color: var(--destructive-foreground);
        }
        
        .button-destructive:hover {
            opacity: 0.9;
        }
        
        .button-ghost {
            background: transparent;
            color: var(--foreground);
        }
        
        .button-ghost:hover {
            background: var(--accent);
        }
        
        .button-group {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .task-type-selector {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        
        .task-type-btn {
            padding: 0.75rem;
            text-align: center;
            border: 2px solid var(--border);
            background: var(--background);
            border-radius: calc(var(--radius) - 2px);
            cursor: pointer;
            transition: all 0.15s;
            font-weight: 500;
        }
        
        .task-type-btn:hover {
            background: var(--secondary);
        }
        
        .task-type-btn.active {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
            border-color: #3b82f6;
            box-shadow: 0 0 15px rgba(59, 130, 246, 0.3);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: linear-gradient(135deg, rgba(31, 31, 31, 0.8) 0%, rgba(38, 38, 38, 0.6) 100%);
            backdrop-filter: blur(10px);
            padding: 1rem;
            border-radius: calc(var(--radius) - 2px);
            text-align: center;
            border: 1px solid var(--border);
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--muted-foreground);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        .task-list {
            border: 1px solid var(--border);
            border-radius: var(--radius);
            overflow: hidden;
            background: rgba(23, 23, 23, 0.3);
            backdrop-filter: blur(5px);
        }
        
        .task-item {
            padding: 1rem;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.15s;
        }
        
        .task-item:last-child {
            border-bottom: none;
        }
        
        .task-item:hover {
            background: var(--secondary);
        }
        
        .task-info {
            flex: 1;
        }
        
        .task-id {
            font-size: 0.75rem;
            color: var(--muted-foreground);
            font-family: monospace;
        }
        
        .task-content {
            margin: 0.25rem 0;
            font-size: 0.875rem;
        }
        
        .task-meta {
            display: flex;
            gap: 0.5rem;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            font-weight: 500;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        
        .badge-default {
            background: var(--secondary);
            color: var(--secondary-foreground);
        }
        
        .badge-pending {
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
        }
        
        .badge-processing {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            animation: pulse 2s infinite;
        }
        
        .badge-completed {
            background: rgba(34, 197, 94, 0.2);
            color: #22c55e;
            border: 1px solid rgba(34, 197, 94, 0.3);
        }
        
        .badge-failed {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            border: 1px solid rgba(239, 68, 68, 0.3);
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--muted-foreground);
        }
        
        .metadata-inputs {
            display: grid;
            gap: 0.5rem;
        }
        
        .metadata-row {
            display: grid;
            grid-template-columns: 1fr 1fr auto;
            gap: 0.5rem;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .icon-button {
            width: 2rem;
            height: 2rem;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: calc(var(--radius) - 2px);
        }
        
        .toast {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: rgba(31, 31, 31, 0.95);
            color: var(--foreground);
            padding: 1rem 1.5rem;
            border-radius: var(--radius);
            border: 1px solid var(--border);
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s;
            z-index: 1000;
            max-width: 400px;
            backdrop-filter: blur(10px);
        }
        
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        
        .toast.error {
            background: var(--destructive);
            color: var(--destructive-foreground);
        }
        
        .tabs {
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.5rem;
        }
        
        .tab-list {
            display: flex;
            gap: 2rem;
        }
        
        .tab-trigger {
            padding: 0.5rem 0;
            border-bottom: 2px solid transparent;
            background: none;
            border-top: none;
            border-left: none;
            border-right: none;
            cursor: pointer;
            font-weight: 500;
            color: var(--muted-foreground);
            transition: all 0.15s;
        }
        
        .tab-trigger:hover {
            color: var(--foreground);
        }
        
        .tab-trigger.active {
            color: #3b82f6;
            border-bottom-color: #3b82f6;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .server-info {
            background: linear-gradient(135deg, rgba(31, 31, 31, 0.8) 0%, rgba(38, 38, 38, 0.6) 100%);
            padding: 1rem;
            border-radius: var(--radius);
            margin-bottom: 2rem;
            font-family: monospace;
            font-size: 0.875rem;
            border: 1px solid var(--border);
            backdrop-filter: blur(10px);
        }
        
        .loader {
            width: 1rem;
            height: 1rem;
            border: 2px solid rgba(59, 130, 246, 0.2);
            border-top-color: #3b82f6;
            border-radius: 50%;
            animation: spin 0.6s linear infinite;
            display: inline-block;
            margin-left: 0.5rem;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .result-viewer {
            background: var(--secondary);
            padding: 1rem;
            border-radius: calc(var(--radius) - 2px);
            font-family: monospace;
            font-size: 0.75rem;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🌙 OSS at Night</h1>
            <p class="subtitle">Queue tasks during the day, wake up to completed work • Accessible at {{ server_info }}</p>
        </header>
        
        <div class="server-info">
            <strong>Server Status:</strong> Running<br>
            <strong>Model:</strong> {{ model }}<br>
            <strong>Access URL:</strong> http://{{ server_info }}
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="stat-total">0</div>
                <div class="stat-label">Total Tasks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-pending">0</div>
                <div class="stat-label">Pending</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-processing">0</div>
                <div class="stat-label">Processing</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-completed">0</div>
                <div class="stat-label">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-failed">0</div>
                <div class="stat-label">Failed</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Add New Task</h2>
                    <p class="card-description">Queue a task for processing</p>
                </div>
                
                <form id="task-form">
                    <div class="form-group">
                        <label for="command">Describe Your Task</label>
                        <textarea id="command" name="command" placeholder="Example: Research the latest AI developments and create a comprehensive report..." style="min-height: 120px;" required></textarea>
                    </div>
                    
                    <div class="button-group">
                        <button type="button" class="button button-primary" onclick="interpretTask()">Interpret Task</button>
                        <button type="button" class="button button-secondary" onclick="clearAll()">Clear</button>
                    </div>
                </form>
                
                <div id="confirmation-area" style="display: none; margin-top: 2rem; padding: 1.5rem; background: var(--secondary); border-radius: var(--radius);">
                    <h3 style="margin-bottom: 1rem;">Task Interpretation</h3>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>Type:</strong>
                        <span id="interpreted-type" class="badge badge-default" style="margin-left: 0.5rem;"></span>
                    </div>
                    
                    <div style="margin-bottom: 1rem;">
                        <strong>Content:</strong>
                        <div id="interpreted-content" style="margin-top: 0.5rem; padding: 0.75rem; background: var(--background); border-radius: calc(var(--radius) - 2px); font-size: 0.875rem;"></div>
                    </div>
                    
                    <div style="margin-bottom: 1.5rem;">
                        <strong>Metadata:</strong>
                        <div id="interpreted-metadata" style="margin-top: 0.5rem; padding: 0.75rem; background: var(--background); border-radius: calc(var(--radius) - 2px); font-family: monospace; font-size: 0.75rem;"></div>
                    </div>
                    
                    <div class="button-group">
                        <button class="button button-primary" onclick="confirmAndQueue()">Add to Queue</button>
                        <button class="button button-secondary" onclick="clearConfirmation()">Clear</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Processing Controls</h2>
                    <p class="card-description">Manage task processing</p>
                </div>
                
                <div class="button-group">
                    <button id="process-btn" class="button button-primary" onclick="startProcessing()">
                        Start Processing
                    </button>
                    <button class="button button-destructive" onclick="stopProcessing()">Stop</button>
                    <button class="button button-secondary" onclick="clearCompleted()">Clear Completed</button>
                    <button class="button button-secondary" onclick="resetFailed()">Reset Failed</button>
                </div>
                
                <div style="margin-top: 1rem;">
                    <label for="auto-refresh">
                        <input type="checkbox" id="auto-refresh" checked> Auto-refresh (5s)
                    </label>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="tabs">
                <div class="tab-list">
                    <button class="tab-trigger active" onclick="switchTab('queue')">Task Queue</button>
                    <button class="tab-trigger" onclick="switchTab('results')">Results</button>
                    <button class="tab-trigger" onclick="switchTab('logs')">Logs</button>
                    <button class="tab-trigger" onclick="switchTab('files')">Files 📁</button>
                    <a href="/gallery" target="_blank" class="tab-trigger" style="text-decoration: none;">Gallery View 🎨</a>
                </div>
            </div>
            
            <div class="tab-content active" id="tab-queue">
                <div id="task-list">
                    <div class="empty-state">No tasks in queue</div>
                </div>
            </div>
            
            <div class="tab-content" id="tab-results">
                <div id="results-list">
                    <div class="empty-state">No completed tasks</div>
                </div>
            </div>
            
            <div class="tab-content" id="tab-logs">
                <div class="result-viewer" id="logs-viewer">
                    Logs will appear here...
                </div>
            </div>
            
            <div class="tab-content" id="tab-files">
                <div style="margin-bottom: 1rem;">
                    <button onclick="refreshFiles()" class="btn">🔄 Refresh Files</button>
                    <button onclick="downloadWorkspace()" class="btn">📦 Download Workspace</button>
                </div>
                <div id="files-list">
                    <div class="empty-state">Click refresh to load workspace files</div>
                </div>
            </div>
        </div>
    </div>
    
    <div class="toast" id="toast"></div>
    
    <script>
        let processingInterval = null;
        let refreshInterval = null;
        let interpretedTask = null;
        
        async function interpretTask() {
            const command = document.getElementById('command').value.trim();
            if (!command) {
                showToast('Please enter a task description', 'error');
                return;
            }
            
            // Show loading state
            const button = event.target;
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Interpreting...';
            
            try {
                const response = await fetch('/api/interpret_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command})
                });
                
                if (response.ok) {
                    interpretedTask = await response.json();
                    displayInterpretation(interpretedTask);
                } else {
                    const error = await response.json();
                    showToast('Failed to interpret task: ' + (error.error || 'Unknown error'), 'error');
                }
            } catch (error) {
                showToast('Error: ' + error.message, 'error');
            } finally {
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        function displayInterpretation(task) {
            // Show the confirmation area
            document.getElementById('confirmation-area').style.display = 'block';
            
            // Display task type
            const typeSpan = document.getElementById('interpreted-type');
            typeSpan.textContent = task.type.toUpperCase();
            typeSpan.className = 'badge badge-default';
            
            // Display content
            document.getElementById('interpreted-content').textContent = task.content;
            
            // Display metadata
            const metadataDiv = document.getElementById('interpreted-metadata');
            if (task.metadata && Object.keys(task.metadata).length > 0) {
                metadataDiv.textContent = JSON.stringify(task.metadata, null, 2);
            } else {
                metadataDiv.textContent = 'No metadata specified';
            }
            
            // Scroll to confirmation area
            document.getElementById('confirmation-area').scrollIntoView({ behavior: 'smooth' });
        }
        
        async function confirmAndQueue() {
            if (!interpretedTask) {
                showToast('No task to queue', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/add_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(interpretedTask)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showToast(`Task queued: ${result.task_id}`);
                    clearAll();
                    updateStatus();
                    loadTasks();
                } else {
                    showToast('Failed to queue task', 'error');
                }
            } catch (error) {
                showToast('Error: ' + error.message, 'error');
            }
        }
        
        function clearConfirmation() {
            document.getElementById('confirmation-area').style.display = 'none';
            interpretedTask = null;
        }
        
        function clearAll() {
            document.getElementById('command').value = '';
            clearConfirmation();
        }
        
        function clearForm() {
            clearAll();
        }
        
        // Keep for backward compatibility but won't be used with new flow
        async function submitTask(event) {
            event.preventDefault();
            // This form submission is now handled through the interpret flow
            interpretTask();
        }
        
        async function startProcessing() {
            const processBtn = document.getElementById('process-btn');
            processBtn.disabled = true;
            processBtn.innerHTML = 'Processing... <span class="loader" style="display: inline-block;"></span>';
            
            try {
                const response = await fetch('/api/start_processing', {method: 'POST'});
                if (response.ok) {
                    showToast('Processing started');
                    processingInterval = setInterval(updateStatus, 2000);
                    processBtn.classList.add('processing');
                }
            } catch (error) {
                showToast('Error starting processing', 'error');
                processBtn.innerHTML = 'Start Processing';
                processBtn.disabled = false;
            }
        }
        
        async function stopProcessing() {
            const processBtn = document.getElementById('process-btn');
            
            try {
                const response = await fetch('/api/stop_processing', {method: 'POST'});
                if (response.ok) {
                    showToast('Processing stopped');
                    if (processingInterval) {
                        clearInterval(processingInterval);
                        processingInterval = null;
                    }
                    processBtn.innerHTML = 'Start Processing';
                    processBtn.classList.remove('processing');
                    processBtn.disabled = false;
                }
            } catch (error) {
                showToast('Error stopping processing', 'error');
            }
        }
        
        async function clearCompleted() {
            try {
                const response = await fetch('/api/clear_completed', {method: 'POST'});
                if (response.ok) {
                    showToast('Completed tasks cleared');
                    updateStatus();
                    loadTasks();
                }
            } catch (error) {
                showToast('Error clearing tasks', 'error');
            }
        }
        
        async function resetFailed() {
            try {
                const response = await fetch('/api/reset_failed', {method: 'POST'});
                if (response.ok) {
                    showToast('Failed tasks reset');
                    updateStatus();
                    loadTasks();
                }
            } catch (error) {
                showToast('Error resetting tasks', 'error');
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                if (response.ok) {
                    const stats = await response.json();
                    document.getElementById('stat-total').textContent = stats.total || 0;
                    document.getElementById('stat-pending').textContent = stats.pending || 0;
                    document.getElementById('stat-processing').textContent = stats.processing || 0;
                    document.getElementById('stat-completed').textContent = stats.completed || 0;
                    document.getElementById('stat-failed').textContent = stats.failed || 0;
                    
                    // Update button state based on actual processing status
                    const processBtn = document.getElementById('process-btn');
                    const isProcessing = stats.processing === true;
                    
                    if (isProcessing) {
                        processBtn.innerHTML = 'Processing... <span class="loader" style="display: inline-block;"></span>';
                        processBtn.classList.add('processing');
                        processBtn.disabled = true;
                    } else {
                        processBtn.innerHTML = 'Start Processing';
                        processBtn.classList.remove('processing');
                        processBtn.disabled = false;
                        
                        // Clear processing interval when processing stops
                        if (processingInterval) {
                            clearInterval(processingInterval);
                            processingInterval = null;
                        }
                    }
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        
        function renderTasks(tasks) {
            const container = document.getElementById('task-list');
            
            if (tasks.length === 0) {
                container.innerHTML = '<div class="empty-state">No tasks in queue</div>';
                return;
            }
            
            container.innerHTML = '<div class="task-list">' + 
                tasks.map(task => `
                    <div class="task-item">
                        <div class="task-info">
                            <div class="task-id">${task.id}</div>
                            <div class="task-content">${task.content.substring(0, 100)}${task.content.length > 100 ? '...' : ''}</div>
                            <div class="task-meta">
                                <span class="badge badge-default">${task.type}</span>
                                <span class="badge badge-${task.status}">${task.status}</span>
                                ${task.processing_time ? `<span class="badge badge-default">${task.processing_time.toFixed(1)}s</span>` : ''}
                            </div>
                        </div>
                        <div class="task-actions" style="display: flex; gap: 0.5rem;">
                            ${task.status === 'completed' ? 
                                `<button class="button button-ghost" onclick="viewResults('${task.id}')">View</button>` : 
                                ''}
                            ${task.status === 'pending' ? 
                                `<button class="button button-ghost" onclick="editTask('${task.id}')">Edit</button>` : 
                                ''}
                            <button class="button button-ghost" onclick="deleteTask('${task.id}')" style="color: #ef4444;">Delete</button>
                        </div>
                    </div>
                `).join('') + '</div>';
        }
        
        async function viewResults(taskId) {
            try {
                const response = await fetch(`/api/task/${taskId}`);
                if (response.ok) {
                    const task = await response.json();
                    switchTab('results');
                    document.getElementById('results-list').innerHTML = 
                        `<div class="result-viewer">${JSON.stringify(task.results, null, 2)}</div>`;
                }
            } catch (error) {
                showToast('Error loading results', 'error');
            }
        }
        
        function switchTab(tabName) {
            // Update current tab tracker
            currentTab = tabName;
            
            // Update tab buttons
            document.querySelectorAll('.tab-trigger').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Find the clicked button and activate it
            const clickedButton = Array.from(document.querySelectorAll('.tab-trigger'))
                .find(btn => btn.textContent.toLowerCase().includes(tabName) || btn.onclick?.toString().includes(tabName));
            if (clickedButton) {
                clickedButton.classList.add('active');
            }
            
            // Show the correct tab content
            const tabContent = document.getElementById(`tab-${tabName}`);
            if (tabContent) {
                tabContent.classList.add('active');
                
                // Load content based on tab
                if (tabName === 'files') {
                    refreshFiles();
                } else if (tabName === 'results') {
                    loadCompletedTasks();
                }
            }
        }
        
        function showToast(message, type = 'success') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show' + (type === 'error' ? ' error' : '');
            
            setTimeout(() => {
                toast.classList.remove('show');
            }, 3000);
        }
        
        // Auto-refresh
        document.getElementById('auto-refresh').addEventListener('change', function() {
            if (this.checked) {
                refreshInterval = setInterval(() => {
                    updateStatus();
                    loadTasks();
                    if (currentTab === 'files') refreshFiles();
                }, 5000);
            } else {
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                    refreshInterval = null;
                }
            }
        });
        
        // File management functions
        async function refreshFiles() {
            try {
                const response = await fetch('/api/files');
                if (response.ok) {
                    const files = await response.json();
                    displayFiles(files);
                } else {
                    showToast('Error loading files', 'error');
                }
            } catch (error) {
                console.error('Error loading files:', error);
                showToast('Error loading files', 'error');
            }
        }
        
        function displayFiles(files) {
            const filesList = document.getElementById('files-list');
            
            if (files.length === 0) {
                filesList.innerHTML = '<div class="empty-state">No files in workspace</div>';
                return;
            }
            
            filesList.innerHTML = files.map(file => `
                <div class="task-card" style="cursor: pointer; margin-bottom: 0.5rem;" onclick="downloadFile('${file.name}')">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${file.name}</strong>
                            <div style="font-size: 0.75rem; color: #666;">
                                ${formatFileSize(file.size)} • ${new Date(file.modified).toLocaleDateString()}
                            </div>
                        </div>
                        <button class="btn" onclick="event.stopPropagation(); downloadFile('${file.name}')" style="font-size: 0.75rem;">📥 Download</button>
                    </div>
                </div>
            `).join('');
        }
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }
        
        async function downloadFile(filename) {
            try {
                const response = await fetch(`/api/download/${encodeURIComponent(filename)}`);
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    showToast('File downloaded: ' + filename, 'success');
                } else {
                    showToast('Error downloading file', 'error');
                }
            } catch (error) {
                showToast('Download failed: ' + error.message, 'error');
            }
        }
        
        async function downloadWorkspace() {
            try {
                const response = await fetch('/api/download/workspace.zip');
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'workspace.zip';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    window.URL.revokeObjectURL(url);
                    showToast('Workspace downloaded', 'success');
                } else {
                    showToast('Error downloading workspace', 'error');
                }
            } catch (error) {
                showToast('Download failed: ' + error.message, 'error');
            }
        }
        
        // Enhanced task display with progress
        function displayEnhancedTask(task) {
            const results = typeof task.results === 'string' ? JSON.parse(task.results || '{}') : (task.results || {});
            const steps = Object.keys(results);
            
            let progressHtml = '';
            if (task.status === 'processing' && steps.length > 0) {
                progressHtml = `
                    <div style="margin: 0.5rem 0; font-size: 0.75rem;">
                        <strong>Progress:</strong> ${steps.map(step => 
                            `<span style="background: #10b981; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; margin: 0 0.25rem;">${step}</span>`
                        ).join('')}
                        <span style="background: #f59e0b; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem;">Processing...</span>
                    </div>
                `;
            }
            
            // Show web search indicator
            let searchIndicator = '';
            if (results.web_search || results.search_docs || results.research) {
                searchIndicator = '<span style="background: #3b82f6; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem;">🔍 Web Search</span>';
            }
            
            return progressHtml + searchIndicator;
        }
        
        // Track current tab for refresh
        let currentTab = 'queue';
        
        // Load completed tasks for results tab
        async function loadCompletedTasks() {
            try {
                const response = await fetch('/api/tasks');
                if (response.ok) {
                    const data = await response.json();
                    const tasks = data.tasks || data;
                    const completedTasks = tasks.filter(t => t.status === 'completed');
                    
                    const resultsDiv = document.getElementById('results-list');
                    if (completedTasks.length === 0) {
                        resultsDiv.innerHTML = '<div class="empty-state">No completed tasks</div>';
                        return;
                    }
                    
                    resultsDiv.innerHTML = completedTasks.map(task => `
                        <div class="task-item" style="margin-bottom: 1rem; padding: 1rem; border: 1px solid #ddd; border-radius: 0.5rem;">
                            <div style="display: flex; justify-content: between; margin-bottom: 0.5rem;">
                                <strong>${task.type}</strong>
                                <small>${new Date(task.created_at).toLocaleString()}</small>
                            </div>
                            <div style="margin-bottom: 0.5rem; font-size: 0.875rem;">
                                ${task.content.substring(0, 150)}...
                            </div>
                            <button onclick="viewTaskResults('${task.id}')" class="btn" style="font-size: 0.75rem;">View Results</button>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading completed tasks:', error);
            }
        }
        
        // Delete a task
        async function deleteTask(taskId) {
            if (!confirm('Are you sure you want to delete this task?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/delete_task/${taskId}`, {method: 'DELETE'});
                if (response.ok) {
                    showToast('Task deleted successfully');
                    updateStatus();
                    loadTasks();
                } else {
                    const error = await response.json();
                    showToast(error.error || 'Failed to delete task', 'error');
                }
            } catch (error) {
                showToast('Error deleting task', 'error');
            }
        }
        
        // Edit a task
        async function editTask(taskId) {
            const task = allTasks ? allTasks.find(t => t.id === taskId) : null;
            if (!task) {
                showToast('Task not found', 'error');
                return;
            }
            
            if (task.status !== 'pending') {
                showToast('Can only edit pending tasks', 'error');
                return;
            }
            
            // Create a modal for editing
            const modal = document.getElementById('task-modal');
            const modalTitle = document.getElementById('modal-title');
            const modalBody = document.getElementById('modal-body');
            
            modalTitle.textContent = `Edit Task ${task.id}`;
            
            modalBody.innerHTML = `
                <div class="form-group">
                    <label for="edit-content">Task Content:</label>
                    <textarea id="edit-content" style="width: 100%; min-height: 100px;">${task.content}</textarea>
                </div>
                
                <div class="form-group">
                    <label>Metadata (Optional):</label>
                    <div id="edit-metadata-container"></div>
                    <button type="button" class="button button-secondary" onclick="addEditMetadataRow()">+ Add Metadata</button>
                </div>
                
                <div style="display: flex; gap: 1rem; margin-top: 1.5rem;">
                    <button class="button button-primary" onclick="saveTaskEdit('${task.id}')">Save Changes</button>
                    <button class="button button-secondary" onclick="closeModal()">Cancel</button>
                </div>
            `;
            
            // Populate existing metadata
            const metadataContainer = document.getElementById('edit-metadata-container');
            if (task.metadata && Object.keys(task.metadata).length > 0) {
                Object.entries(task.metadata).forEach(([key, value]) => {
                    const row = document.createElement('div');
                    row.className = 'metadata-row';
                    row.innerHTML = `
                        <input type="text" placeholder="Key" class="meta-key" value="${key}">
                        <input type="text" placeholder="Value" class="meta-value" value="${value}">
                        <button type="button" class="button button-ghost icon-button" onclick="removeMetadataRow(this)">×</button>
                    `;
                    metadataContainer.appendChild(row);
                });
            } else {
                addEditMetadataRow();
            }
            
            modal.classList.add('active');
        }
        
        function addEditMetadataRow() {
            const container = document.getElementById('edit-metadata-container');
            const row = document.createElement('div');
            row.className = 'metadata-row';
            row.innerHTML = `
                <input type="text" placeholder="Key" class="meta-key">
                <input type="text" placeholder="Value" class="meta-value">
                <button type="button" class="button button-ghost icon-button" onclick="removeMetadataRow(this)">×</button>
            `;
            container.appendChild(row);
        }
        
        async function saveTaskEdit(taskId) {
            const content = document.getElementById('edit-content').value.trim();
            if (!content) {
                showToast('Task content cannot be empty', 'error');
                return;
            }
            
            const metadata = {};
            document.querySelectorAll('#edit-metadata-container .metadata-row').forEach(row => {
                const key = row.querySelector('.meta-key').value.trim();
                const value = row.querySelector('.meta-value').value.trim();
                if (key && value) {
                    metadata[key] = value;
                }
            });
            
            try {
                const response = await fetch(`/api/update_task/${taskId}`, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({content, metadata})
                });
                
                if (response.ok) {
                    showToast('Task updated successfully');
                    closeModal();
                    updateStatus();
                    loadTasks();
                } else {
                    const error = await response.json();
                    showToast(error.error || 'Failed to update task', 'error');
                }
            } catch (error) {
                showToast('Error updating task', 'error');
            }
        }
        
        // Store tasks globally for edit/delete operations  
        let allTasks = [];
        
        // Update loadTasks to store tasks globally
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                if (response.ok) {
                    const data = await response.json();
                    allTasks = data.tasks || data; // Store globally and handle both formats
                    renderTasks(allTasks);
                }
            } catch (error) {
                console.error('Error loading tasks:', error);
            }
        }

        // View individual task results
        async function viewTaskResults(taskId) {
            try {
                const response = await fetch(`/api/task/${taskId}`);
                if (response.ok) {
                    const task = await response.json();
                    const resultsDiv = document.getElementById('results-list');
                    
                    let resultsHtml = '<div class="result-viewer">';
                    resultsHtml += `<h3>Task: ${task.type}</h3>`;
                    resultsHtml += `<p><strong>Content:</strong> ${task.content}</p>`;
                    resultsHtml += `<p><strong>Processing Time:</strong> ${task.processing_time}s</p>`;
                    resultsHtml += '<h4>Results:</h4>';
                    
                    if (task.results && typeof task.results === 'object') {
                        Object.entries(task.results).forEach(([key, value]) => {
                            resultsHtml += `<div style="margin-bottom: 1rem;">`;
                            resultsHtml += `<h5>${key.replace(/_/g, ' ').toUpperCase()}</h5>`;
                            resultsHtml += `<pre style="background: #f5f5f5; padding: 1rem; border-radius: 0.25rem; white-space: pre-wrap; font-size: 0.875rem;">${typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</pre>`;
                            resultsHtml += `</div>`;
                        });
                    }
                    
                    resultsHtml += `<button onclick="loadCompletedTasks()" class="btn" style="margin-top: 1rem;">← Back to Results</button>`;
                    resultsHtml += '</div>';
                    
                    resultsDiv.innerHTML = resultsHtml;
                }
            } catch (error) {
                console.error('Error loading task results:', error);
            }
        }
        
        
        // Form submission
        document.getElementById('task-form').addEventListener('submit', submitTask);
        
        // Initial load
        updateStatus();
        loadTasks();
        
        // Start auto-refresh
        refreshInterval = setInterval(() => {
            updateStatus();
            loadTasks();
        }, 5000);
    </script>
</body>
</html>
'''

def create_ai_router_prompt():
    """Create a system prompt for the AI to interpret user commands into task JSON"""
    return """You are a Task Interpreter for a batch processing system. Your role is to analyze user commands and convert them into structured task JSON objects.

Based on the user's input, determine the appropriate task type and extract relevant metadata.

Task Types:
- search: For research, web searches, information gathering
- process: For text processing, formatting, improving existing content
- create: For generating new content from scratch
- code: For programming, script generation, code analysis
- chain: For multi-step complex tasks

Use the following metadata guidelines:

For SEARCH tasks:
- search_query: The main search topic
- comparison: true if comparing multiple things
- filename: Output filename (default: research_report.md)

For PROCESS tasks:
- format: Output format (bullet_points, markdown, json)
- improve_clarity: true to enhance clarity
- simplify: true to simplify content

For CREATE tasks:
- tone: Writing tone (professional, casual, conversational)
- audience: Target audience
- format: Output format
- filename: Output filename

For CODE tasks:
- language: Programming language (python, javascript, etc)
- filename: Output filename with appropriate extension
- include_docs: true to include documentation
- include_tests: true to include tests

For CHAIN tasks:
- Include relevant metadata for the overall workflow

IMPORTANT: Return ONLY a clean JSON object with this structure:
{
  "type": "task_type_here",
  "content": "the user's request clearly stated",
  "metadata": {
    "key": "value"
  }
}

Do not include any explanation, markdown formatting, or additional text. Only return the JSON object."""

# Processor class (simplified for single file)
class TaskProcessor:
    def __init__(self):
        # Use data directory for database in Docker, current dir otherwise
        data_dir = Path("data")
        if data_dir.exists():
            self.db_path = data_dir / "task_processor.db"
        else:
            self.db_path = Path("task_processor.db")
        self.queue_file = Path("task_queue.json")
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        self.config = {
            'model': 'gpt-oss:20b',
            'ollama_host': os.getenv('OLLAMA_HOST', 'http://localhost:11434'),
            'temperature': 0.7,
            'max_retries': 3
        }
        
        self.queue = []
        self.processing = False
        self.processing_thread = None
        
        self.init_database()
        self.load_queue()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
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
        conn.commit()
        conn.close()
    
    def load_queue(self):
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    data = json.load(f)
                    self.queue = []
                    for item in data:
                        if 'type' in item and isinstance(item['type'], str):
                            item['type'] = TaskType(item['type'])
                        if 'status' in item and isinstance(item['status'], str):
                            item['status'] = TaskStatus(item['status'])
                        self.queue.append(Task(**item))
            except:
                self.queue = []
    
    def save_queue(self):
        queue_data = []
        for task in self.queue:
            task_dict = asdict(task)
            task_dict['type'] = task.type.value
            task_dict['status'] = task.status.value
            queue_data.append(task_dict)
        
        with open(self.queue_file, 'w') as f:
            json.dump(queue_data, f, indent=2)
    
    def add_task(self, task_type: str, content: str, metadata: dict = None) -> str:
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:17]}"
        task = Task(
            id=task_id,
            type=TaskType(task_type),
            content=content,
            metadata=metadata or {}
        )
        self.queue.append(task)
        self.save_queue()
        self.save_to_db(task)
        return task_id
    
    def save_to_db(self, task: Task):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            (id, type, content, status, results, metadata, error, retry_count, updated_at, processing_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.id,
            task.type.value,
            task.content,
            task.status.value,
            json.dumps(task.results),
            json.dumps(task.metadata),
            task.error,
            task.retry_count,
            datetime.now().isoformat(),
            task.processing_time
        ))
        conn.commit()
        conn.close()
    
    def process_with_ollama(self, prompt: str) -> str:
        try:
            payload = {
                'model': self.config['model'],
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': self.config.get('temperature', 0.7),
                }
            }
            
            response = requests.post(
                f"{self.config['ollama_host']}/api/generate",
                json=payload,
                timeout=None
            )
            
            if response.status_code == 200:
                return response.json().get('response', '')
            return "Error: Failed to get response"
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error: {str(e)}"
    
    def process_task(self, task: Task):
        task.status = TaskStatus.PROCESSING
        task.updated_at = datetime.now().isoformat()
        start_time = time.time()
        
        try:
            # Simple processing based on task type
            if task.type == TaskType.SEARCH:
                # Simulate web search
                task.results['search'] = f"Search results for: {task.content[:50]}"
                prompt = f"Summarize this search query and create a report: {task.content}"
                task.results['report'] = self.process_with_ollama(prompt)
                
            elif task.type == TaskType.PROCESS:
                prompt = f"Process and improve this content: {task.content}"
                task.results['processed'] = self.process_with_ollama(prompt)
                
            elif task.type == TaskType.CREATE:
                prompt = f"Create content based on: {task.content}"
                task.results['created'] = self.process_with_ollama(prompt)
                
            elif task.type == TaskType.CODE:
                prompt = f"Write code for: {task.content}"
                task.results['code'] = self.process_with_ollama(prompt)
                
            elif task.type == TaskType.CHAIN:
                # Multi-step processing
                steps = ["analyze", "expand", "finalize"]
                for step in steps:
                    prompt = f"{step.capitalize()} this: {task.content}"
                    task.results[step] = self.process_with_ollama(prompt)
            
            # Save content to file if filename is specified in metadata
            self._save_results_to_file(task)
            
            task.status = TaskStatus.COMPLETED
            task.processing_time = time.time() - start_time
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.retry_count += 1
        
        task.updated_at = datetime.now().isoformat()
        self.save_to_db(task)
        self.save_queue()
    
    def start_processing(self):
        if not self.processing:
            self.processing = True
            self.processing_thread = threading.Thread(target=self._process_loop)
            self.processing_thread.daemon = True
            self.processing_thread.start()
    
    def stop_processing(self):
        self.processing = False
    
    def _process_loop(self):
        while self.processing:
            pending_tasks = [t for t in self.queue if t.status == TaskStatus.PENDING]
            if pending_tasks:
                task = pending_tasks[0]
                self.process_task(task)
                time.sleep(2)  # Delay between tasks
            else:
                # No more pending tasks, stop processing
                logger.info("No more pending tasks, stopping processing")
                self.processing = False
                break
    
    def get_stats(self):
        return {
            'total': len(self.queue),
            'pending': sum(1 for t in self.queue if t.status == TaskStatus.PENDING),
            'processing': sum(1 for t in self.queue if t.status == TaskStatus.PROCESSING),
            'completed': sum(1 for t in self.queue if t.status == TaskStatus.COMPLETED),
            'failed': sum(1 for t in self.queue if t.status == TaskStatus.FAILED),
        }
    
    def clear_completed(self):
        self.queue = [t for t in self.queue if t.status != TaskStatus.COMPLETED]
        self.save_queue()
    
    def reset_failed(self):
        for task in self.queue:
            if task.status == TaskStatus.FAILED:
                task.status = TaskStatus.PENDING
                task.retry_count = 0
                task.error = None
        self.save_queue()
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task from the queue"""
        initial_len = len(self.queue)
        self.queue = [t for t in self.queue if t.id != task_id]
        if len(self.queue) < initial_len:
            self.save_queue()
            return True
        return False
    
    def update_task(self, task_id: str, content: str = None, metadata: dict = None) -> bool:
        """Update a task's content and/or metadata (only if pending)"""
        task = next((t for t in self.queue if t.id == task_id), None)
        if task and task.status == TaskStatus.PENDING:
            if content is not None:
                task.content = content
            if metadata is not None:
                task.metadata = metadata
            task.updated_at = datetime.now().isoformat()
            self.save_queue()
            self.save_to_db(task)
            return True
        return False
    
    def _save_results_to_file(self, task: Task):
        """Save task results to a file in the workspace directory"""
        try:
            # Create workspace directory if it doesn't exist
            workspace_dir = Path("workspace")
            workspace_dir.mkdir(exist_ok=True)
            
            # Determine filename from metadata or use default
            filename = task.metadata.get('filename', f"{task.id}.txt")
            
            # If no extension, add .txt
            if '.' not in filename:
                filename += '.txt'
            
            # Combine all results into one content string
            content_parts = []
            
            # Add task description
            content_parts.append(f"Task: {task.content}\n")
            content_parts.append(f"Type: {task.type.value}\n")
            content_parts.append(f"Generated: {task.updated_at}\n")
            content_parts.append("=" * 50 + "\n")
            
            # Add all result sections
            for key, value in task.results.items():
                if isinstance(value, str) and value.strip():
                    content_parts.append(f"\n## {key.upper().replace('_', ' ')}\n")
                    content_parts.append(f"{value}\n")
                elif isinstance(value, dict):
                    # For nested dict results (like web search), extract meaningful content
                    if key == 'research' and 'organic' in value:
                        content_parts.append(f"\n## WEB SEARCH RESULTS\n")
                        for result in value['organic'][:3]:  # Top 3 results
                            content_parts.append(f"- {result.get('title', 'No title')}\n")
                            content_parts.append(f"  {result.get('snippet', 'No description')}\n")
                            content_parts.append(f"  Link: {result.get('link', 'No link')}\n\n")
                    else:
                        content_parts.append(f"\n## {key.upper().replace('_', ' ')}\n")
                        content_parts.append(f"{json.dumps(value, indent=2)}\n")
            
            # Write to file
            file_path = workspace_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(content_parts)
            
            # Update results with file save confirmation
            task.results['save_document'] = f"Content saved to: {filename}"
            logger.info(f"Saved task results to: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save results to file: {e}")
            task.results['save_document'] = f"Error saving file: {str(e)}"

# Flask application
app = Flask(__name__)
CORS(app)

# Initialize processor
processor = TaskProcessor()

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def get_all_network_interfaces():
    """Get all available network interfaces and their IPs"""
    interfaces = []
    try:
        import subprocess
        result = subprocess.run(['ifconfig'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        current_interface = None
        for line in lines:
            if line and not line.startswith('\t') and not line.startswith(' '):
                current_interface = line.split(':')[0]
            elif 'inet ' in line and '127.0.0.1' not in line and 'inet 169.254' not in line:
                ip = line.split('inet ')[1].split(' ')[0]
                if current_interface:
                    interfaces.append((current_interface, ip))
    except:
        pass
    return interfaces

def test_network_connectivity():
    """Test if the server is accessible from different interfaces"""
    print("🔍 NETWORK DIAGNOSTICS:")
    local_ip = get_local_ip()
    interfaces = get_all_network_interfaces()
    
    print(f"Primary IP detected: {local_ip}")
    if interfaces:
        print("Available network interfaces:")
        for interface, ip in interfaces:
            print(f"  {interface}: {ip}")
    
    # Test if we can bind to the port
    try:
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.bind(('0.0.0.0', 5001))
        test_socket.close()
        print("✅ Port 5001 is available")
    except OSError:
        print("❌ Port 5001 is already in use")
    
    return local_ip, interfaces

def generate_qr_code_ascii(url):
    """Generate a simple ASCII QR-like code for the URL"""
    try:
        # Try to use qrcode library if available
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(url)
        qr.make(fit=True)
        
        # Generate ASCII art
        matrix = qr.modules
        if matrix:
            print(f"\n📱 SCAN QR CODE WITH PHONE:")
            print("█" * (len(matrix[0]) + 2))
            for row in matrix:
                line = "█"
                for cell in row:
                    line += "██" if cell else "  "
                line += "█"
                print(line)
            print("█" * (len(matrix[0]) + 2))
            return True
    except ImportError:
        pass
    return False

@app.route('/')
def index():
    server_info = f"{get_local_ip()}:5001"
    return render_template_string(HTML_TEMPLATE, 
                                 server_info=server_info,
                                 model=processor.config['model'])

@app.route('/api/interpret_task', methods=['POST'])
def interpret_task():
    """Interpret user's natural language command into structured task JSON"""
    try:
        data = request.json
        user_command = data.get('command', '').strip()
        
        if not user_command:
            return jsonify({'error': 'No command provided'}), 400
        
        # Create the prompt for the AI
        system_prompt = create_ai_router_prompt()
        
        # Combine system prompt with user command
        full_prompt = f"{system_prompt}\n\nUser Command: {user_command}\n\nTask JSON:"
        
        # Process with Ollama to get interpretation
        interpretation = processor.process_with_ollama(full_prompt)
        
        # Try to parse the response as JSON
        try:
            # Clean the response - remove any markdown formatting
            cleaned = interpretation.strip()
            if cleaned.startswith('```'):
                # Remove markdown code blocks
                cleaned = cleaned.split('```')[1]
                if cleaned.startswith('json'):
                    cleaned = cleaned[4:]
            
            task_json = json.loads(cleaned)
            
            # Validate the structure
            if 'type' not in task_json or 'content' not in task_json:
                raise ValueError("Missing required fields")
            
            # Ensure metadata exists
            if 'metadata' not in task_json:
                task_json['metadata'] = {}
            
            return jsonify(task_json)
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse AI interpretation: {e}")
            # Fallback: try to extract meaningful parts
            return jsonify({
                'type': 'process',
                'content': user_command,
                'metadata': {},
                'error': 'Could not fully interpret command, using defaults'
            })
            
    except Exception as e:
        logger.error(f"Error in interpret_task: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/add_task', methods=['POST'])
def add_task():
    data = request.json
    task_id = processor.add_task(
        task_type=data.get('type', 'process'),
        content=data.get('content', ''),
        metadata=data.get('metadata', {})
    )
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/api/status')
def status():
    stats = processor.get_stats()
    stats['processing'] = processor.processing
    return jsonify(stats)

@app.route('/api/tasks')
def get_tasks():
    tasks_data = []
    for task in processor.queue:
        task_dict = asdict(task)
        task_dict['type'] = task.type.value
        task_dict['status'] = task.status.value
        tasks_data.append(task_dict)
    return jsonify({'tasks': tasks_data})

@app.route('/api/task/<task_id>')
def get_task(task_id):
    task = next((t for t in processor.queue if t.id == task_id), None)
    if task:
        task_dict = asdict(task)
        task_dict['type'] = task.type.value
        task_dict['status'] = task.status.value
        return jsonify(task_dict)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/start_processing', methods=['POST'])
def start_processing():
    processor.start_processing()
    return jsonify({'status': 'started'})

@app.route('/api/stop_processing', methods=['POST'])
def stop_processing():
    processor.stop_processing()
    return jsonify({'status': 'stopped'})

@app.route('/api/clear_completed', methods=['POST'])
def clear_completed():
    processor.clear_completed()
    return jsonify({'status': 'cleared'})

@app.route('/api/reset_failed', methods=['POST'])
def reset_failed():
    processor.reset_failed()
    return jsonify({'status': 'reset'})

@app.route('/api/delete_task/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific task"""
    success = processor.delete_task(task_id)
    if success:
        return jsonify({'status': 'deleted', 'task_id': task_id})
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/api/update_task/<task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task's content and metadata (only if pending)"""
    data = request.json
    content = data.get('content')
    metadata = data.get('metadata')
    
    success = processor.update_task(task_id, content, metadata)
    if success:
        return jsonify({'status': 'updated', 'task_id': task_id})
    else:
        return jsonify({'error': 'Task not found or not editable (must be pending)'}), 400

@app.route('/gallery')
def gallery():
    """Serve the gallery view"""
    gallery_file = Path('gallery_template.html')
    if gallery_file.exists():
        return send_file(str(gallery_file))
    else:
        return "Gallery template not found", 404

@app.route('/api/export/<task_id>')
def export_task(task_id):
    """Export a single task result"""
    task = processor.get_task(task_id)
    if task:
        return jsonify(task)
    return jsonify({'error': 'Task not found'}), 404

@app.route('/api/files')
def list_files():
    """List files in workspace"""
    workspace_dir = Path('workspace')
    if not workspace_dir.exists():
        return jsonify([])
    
    files = []
    for file_path in workspace_dir.rglob('*'):
        if file_path.is_file():
            try:
                stat = file_path.stat()
                files.append({
                    'name': str(file_path.relative_to(workspace_dir)),
                    'size': stat.st_size,
                    'modified': stat.st_mtime * 1000  # JavaScript timestamp
                })
            except:
                pass
    
    return jsonify(files)

@app.route('/api/download/<path:filename>')
def download_file(filename):
    """Download a file from workspace"""
    workspace_dir = Path('workspace')
    file_path = workspace_dir / filename
    
    # Security check - ensure file is within workspace
    try:
        file_path.resolve().relative_to(workspace_dir.resolve())
    except ValueError:
        return jsonify({'error': 'Access denied'}), 403
    
    if file_path.exists() and file_path.is_file():
        return send_file(str(file_path), as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

@app.route('/api/files/upload', methods=['POST'])
def upload_file():
    """Upload a file to workspace"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    workspace_dir = Path('workspace')
    workspace_dir.mkdir(exist_ok=True)
    
    file_path = workspace_dir / file.filename
    file.save(str(file_path))
    
    return jsonify({'message': 'File uploaded successfully', 'filename': file.filename})

@app.route('/api/cli_tasks')
def get_cli_tasks():
    """Get tasks from CLI database (universal_processor.db)"""
    try:
        # Use data directory for database in Docker, current dir otherwise
        data_dir = Path("data")
        if data_dir.exists():
            cli_db_path = data_dir / "universal_processor.db"
        else:
            cli_db_path = Path("universal_processor.db")
        
        if not cli_db_path.exists():
            return jsonify({'tasks': []})
        
        conn = sqlite3.connect(cli_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, type, content, config_name, status, results, metadata, error, 
                   retry_count, created_at, updated_at, processing_time
            FROM tasks
            ORDER BY created_at DESC
        ''')
        
        tasks_data = []
        for row in cursor.fetchall():
            task = {
                'id': row[0],
                'type': row[1],
                'content': row[2],
                'config_name': row[3],
                'status': row[4],
                'results': json.loads(row[5]) if row[5] else {},
                'metadata': json.loads(row[6]) if row[6] else {},
                'error': row[7],
                'retry_count': row[8],
                'created_at': row[9],
                'updated_at': row[10],
                'processing_time': row[11]
            }
            tasks_data.append(task)
        
        conn.close()
        return jsonify({'tasks': tasks_data})
        
    except Exception as e:
        logger.error(f"Error loading CLI tasks: {e}")
        return jsonify({'tasks': [], 'error': str(e)})

@app.route('/api/cli_task/<task_id>')
def get_cli_task(task_id):
    """Get single CLI task with steps"""
    try:
        # Use data directory for database in Docker, current dir otherwise
        data_dir = Path("data")
        if data_dir.exists():
            cli_db_path = data_dir / "universal_processor.db"
        else:
            cli_db_path = Path("universal_processor.db")
        
        if not cli_db_path.exists():
            return jsonify({'error': 'CLI database not found'}), 404
        
        conn = sqlite3.connect(cli_db_path)
        cursor = conn.cursor()
        
        # Get task details
        cursor.execute('''
            SELECT id, type, content, config_name, status, results, metadata, error, 
                   retry_count, created_at, updated_at, processing_time
            FROM tasks WHERE id = ?
        ''', (task_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Task not found'}), 404
        
        task = {
            'id': row[0],
            'type': row[1],
            'content': row[2],
            'config_name': row[3],
            'status': row[4],
            'results': json.loads(row[5]) if row[5] else {},
            'metadata': json.loads(row[6]) if row[6] else {},
            'error': row[7],
            'retry_count': row[8],
            'created_at': row[9],
            'updated_at': row[10],
            'processing_time': row[11]
        }
        
        # Get task steps
        cursor.execute('''
            SELECT step_name, result, created_at
            FROM task_steps WHERE task_id = ?
            ORDER BY created_at
        ''', (task_id,))
        
        task['steps'] = []
        for step_row in cursor.fetchall():
            step = {
                'step_name': step_row[0],
                'result': step_row[1],
                'created_at': step_row[2]
            }
            task['steps'].append(step)
        
        conn.close()
        return jsonify(task)
        
    except Exception as e:
        logger.error(f"Error loading CLI task {task_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Run network diagnostics first
    local_ip, interfaces = test_network_connectivity()
    
    print("\n" + "="*70)
    print("🚀 TASK PROCESSOR GUI STARTED")
    print("="*70)
    print(f"📱 Local Access:    http://localhost:5001")
    print(f"🌐 Network Access:  http://{local_ip}:5001")
    print(f"📲 Phone Access:    http://{local_ip}:5001")
    print(f"🎨 Gallery View:    http://{local_ip}:5001/gallery")
    print("="*70)
    print("🤖 Make sure Ollama is running: ollama serve")
    print("="*70)
    
    # Show alternative IPs if available
    if interfaces and len(interfaces) > 1:
        print("\n🔄 ALTERNATIVE NETWORK ADDRESSES:")
        for interface, ip in interfaces:
            if ip != local_ip:
                print(f"   {interface}: http://{ip}:5001")
        print("="*70)
    
    print("\n📱 PHONE/TABLET ACCESS TROUBLESHOOTING:")
    print(f"1. Ensure your device is on the same WiFi network")
    print(f"2. Try: http://{local_ip}:5001")
    print(f"3. If blocked, check macOS Firewall:")
    print(f"   System Preferences → Security & Privacy → Firewall")
    print(f"   Allow 'Python' or add port 5001")
    print(f"4. Test connectivity from phone: ping {local_ip}")
    print(f"5. Try alternative addresses listed above")
    print("="*70)
    
    # Try to generate QR code for easy mobile access
    main_url = f"http://{local_ip}:5001"
    if not generate_qr_code_ascii(main_url):
        print(f"\n📱 QUICK PHONE ACCESS:")
        print(f"   Bookmark this: {main_url}")
        print(f"   Or install 'qrcode' for QR codes: pip install qrcode[pil]")
    
    print("="*70 + "\n")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ ERROR: Port 5001 is already in use!")
            print("💡 SOLUTION: Run this command to free the port:")
            print("   lsof -ti:5001 | xargs kill -9")
            print("   Then restart the server.")
        else:
            print(f"❌ ERROR: {e}")
        exit(1)