#!/usr/bin/env python3
"""
Universal Task Processor - Complete Flask GUI Application
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
    <title>Task Processor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --background: #ffffff;
            --foreground: #000000;
            --muted: #f9fafb;
            --muted-foreground: #6b7280;
            --border: #e5e7eb;
            --input: #ffffff;
            --primary: #000000;
            --primary-foreground: #ffffff;
            --secondary: #f3f4f6;
            --secondary-foreground: #1f2937;
            --accent: #f3f4f6;
            --accent-foreground: #1f2937;
            --destructive: #ef4444;
            --destructive-foreground: #ffffff;
            --ring: #000000;
            --radius: 0.5rem;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: var(--background);
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
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
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
        
        .card {
            background: var(--background);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 1.5rem;
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
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--ring);
            box-shadow: 0 0 0 3px rgba(0,0,0,0.05);
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
            background: var(--primary);
            color: var(--primary-foreground);
            border-color: var(--primary);
        }
        
        .button-primary:hover {
            background: var(--foreground);
            opacity: 0.9;
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
            background: var(--foreground);
            color: var(--background);
            border-color: var(--foreground);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: var(--secondary);
            padding: 1rem;
            border-radius: calc(var(--radius) - 2px);
            text-align: center;
        }
        
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
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
            background: #fef3c7;
            color: #92400e;
        }
        
        .badge-processing {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .badge-completed {
            background: #d1fae5;
            color: #065f46;
        }
        
        .badge-failed {
            background: #fee2e2;
            color: #991b1b;
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
            background: var(--foreground);
            color: var(--background);
            padding: 1rem 1.5rem;
            border-radius: var(--radius);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s;
            z-index: 1000;
            max-width: 400px;
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
            color: var(--foreground);
            border-bottom-color: var(--foreground);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .server-info {
            background: var(--secondary);
            padding: 1rem;
            border-radius: var(--radius);
            margin-bottom: 2rem;
            font-family: monospace;
            font-size: 0.875rem;
        }
        
        .loader {
            width: 1rem;
            height: 1rem;
            border: 2px solid var(--border);
            border-top-color: var(--foreground);
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
            <h1>Task Processor</h1>
            <p class="subtitle">Queue tasks for AI processing • Accessible at {{ server_info }}</p>
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
                
                <div class="task-type-selector">
                    <div class="task-type-btn active" data-type="search">Search</div>
                    <div class="task-type-btn" data-type="process">Process</div>
                    <div class="task-type-btn" data-type="create">Create</div>
                    <div class="task-type-btn" data-type="code">Code</div>
                    <div class="task-type-btn" data-type="chain">Chain</div>
                </div>
                
                <form id="task-form">
                    <div class="form-group">
                        <label for="content">Task Description</label>
                        <textarea id="content" name="content" placeholder="Describe what you want to accomplish..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label>Metadata (Optional)</label>
                        <div class="metadata-inputs" id="metadata-container">
                            <div class="metadata-row">
                                <input type="text" placeholder="Key" class="meta-key">
                                <input type="text" placeholder="Value" class="meta-value">
                                <button type="button" class="button button-ghost icon-button" onclick="removeMetadataRow(this)">×</button>
                            </div>
                        </div>
                        <button type="button" class="button button-secondary" onclick="addMetadataRow()">+ Add Metadata</button>
                    </div>
                    
                    <div class="button-group">
                        <button type="submit" class="button button-primary">Queue Task</button>
                        <button type="button" class="button button-secondary" onclick="clearForm()">Clear</button>
                    </div>
                </form>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <h2 class="card-title">Processing Controls</h2>
                    <p class="card-description">Manage task processing</p>
                </div>
                
                <div class="button-group">
                    <button class="button button-primary" onclick="startProcessing()">
                        Start Processing
                        <span id="processing-loader" class="loader" style="display: none;"></span>
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
        let selectedType = 'search';
        let processingInterval = null;
        let refreshInterval = null;
        
        // Task type selection
        document.querySelectorAll('.task-type-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.task-type-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                selectedType = this.dataset.type;
                updatePlaceholder();
            });
        });
        
        function updatePlaceholder() {
            const placeholders = {
                search: "Research AI advancements in healthcare and create a comprehensive report...",
                process: "Take this text and make it more professional and engaging...",
                create: "Write a detailed guide about setting up a home automation system...",
                code: "Create a Python script that processes CSV files and generates charts...",
                chain: "Research, analyze, and create a report about quantum computing impacts..."
            };
            document.getElementById('content').placeholder = placeholders[selectedType] || "Describe your task...";
        }
        
        function addMetadataRow() {
            const container = document.getElementById('metadata-container');
            const row = document.createElement('div');
            row.className = 'metadata-row';
            row.innerHTML = `
                <input type="text" placeholder="Key" class="meta-key">
                <input type="text" placeholder="Value" class="meta-value">
                <button type="button" class="button button-ghost icon-button" onclick="removeMetadataRow(this)">×</button>
            `;
            container.appendChild(row);
        }
        
        function removeMetadataRow(button) {
            button.parentElement.remove();
        }
        
        function clearForm() {
            document.getElementById('content').value = '';
            document.querySelectorAll('.meta-key, .meta-value').forEach(input => input.value = '');
        }
        
        async function submitTask(event) {
            event.preventDefault();
            
            const content = document.getElementById('content').value.trim();
            if (!content) {
                showToast('Please enter a task description', 'error');
                return;
            }
            
            const metadata = {};
            document.querySelectorAll('.metadata-row').forEach(row => {
                const key = row.querySelector('.meta-key').value.trim();
                const value = row.querySelector('.meta-value').value.trim();
                if (key && value) {
                    metadata[key] = value;
                }
            });
            
            const taskData = {
                type: selectedType,
                content: content,
                metadata: metadata
            };
            
            try {
                const response = await fetch('/api/add_task', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(taskData)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    showToast(`Task queued: ${result.task_id}`);
                    clearForm();
                    updateStatus();
                    loadTasks();
                } else {
                    showToast('Failed to queue task', 'error');
                }
            } catch (error) {
                showToast('Error: ' + error.message, 'error');
            }
        }
        
        async function startProcessing() {
            document.getElementById('processing-loader').style.display = 'inline-block';
            try {
                const response = await fetch('/api/start_processing', {method: 'POST'});
                if (response.ok) {
                    showToast('Processing started');
                    processingInterval = setInterval(updateStatus, 2000);
                }
            } catch (error) {
                showToast('Error starting processing', 'error');
            }
        }
        
        async function stopProcessing() {
            document.getElementById('processing-loader').style.display = 'none';
            try {
                const response = await fetch('/api/stop_processing', {method: 'POST'});
                if (response.ok) {
                    showToast('Processing stopped');
                    if (processingInterval) {
                        clearInterval(processingInterval);
                        processingInterval = null;
                    }
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
                }
            } catch (error) {
                console.error('Status update error:', error);
            }
        }
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                if (response.ok) {
                    const tasks = await response.json();
                    renderTasks(tasks);
                }
            } catch (error) {
                console.error('Error loading tasks:', error);
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
                        ${task.status === 'completed' ? 
                            `<button class="button button-ghost" onclick="viewResults('${task.id}')">View</button>` : 
                            ''}
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
            document.querySelectorAll('.tab-trigger').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            event.target.classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
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
        
        function switchTab(tab) {
            currentTab = tab;
            // ... existing switchTab code ...
            if (tab === 'files' && document.getElementById('files-list').innerHTML.includes('Click refresh')) {
                refreshFiles();
            }
        }
        
        // Form submission
        document.getElementById('task-form').addEventListener('submit', submitTask);
        
        // Initial load
        updateStatus();
        loadTasks();
        updatePlaceholder();
        
        // Start auto-refresh
        refreshInterval = setInterval(() => {
            updateStatus();
            loadTasks();
        }, 5000);
    </script>
</body>
</html>
'''

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
                time.sleep(5)  # Check for new tasks
    
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

@app.route('/')
def index():
    server_info = f"{get_local_ip()}:5001"
    return render_template_string(HTML_TEMPLATE, 
                                 server_info=server_info,
                                 model=processor.config['model'])

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
    return jsonify(processor.get_stats())

@app.route('/api/tasks')
def get_tasks():
    tasks_data = []
    for task in processor.queue:
        task_dict = asdict(task)
        task_dict['type'] = task.type.value
        task_dict['status'] = task.status.value
        tasks_data.append(task_dict)
    return jsonify(tasks_data)

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

if __name__ == '__main__':
    local_ip = get_local_ip()
    print("\n" + "="*60)
    print("TASK PROCESSOR GUI STARTED")
    print("="*60)
    print(f"Local Access:   http://localhost:5001")
    print(f"Network Access: http://{local_ip}:5001")
    print(f"Phone Access:   http://{local_ip}:5001")
    print("="*60)
    print("Make sure Ollama is running: ollama serve")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False)