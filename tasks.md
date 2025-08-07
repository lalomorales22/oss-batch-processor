# OSS Batch Processor - Implementation Tasks

## Current Issues Identified

### 1. Web Search Integration
- **Problem**: Web search plugin exists but is not properly integrated into all task configs
- **Current State**: Only search_tasks.yaml references web_search plugin
- **Fix Needed**: Add web search capability to all task types

### 2. Task Processing & Results Display
- **Problem**: Tasks show as complete but AI responses aren't visible
- **Current State**: Results are saved but not properly displayed in GUI
- **Fix Needed**: Implement proper results viewer and gallery

### 3. YAML Configuration Issues
- **Problem**: Task configs don't properly chain plugins with LLM calls
- **Current State**: Plugin results aren't being passed to LLM prompts correctly
- **Fix Needed**: Fix prompt variable substitution

## Implementation Tasks

### Priority 1: Fix Core Functionality

#### Task 1.1: Fix Web Search Integration
- [ ] Update search_tasks.yaml to properly use web_search plugin
- [ ] Add environment variable checking for API keys
- [ ] Implement fallback for when no API keys are present
- [ ] Fix result variable passing between steps

#### Task 1.2: Add Web Search to All Task Types
- [ ] Update process_tasks.yaml to include optional web search
- [ ] Update create_tasks.yaml to include research step
- [ ] Update code_tasks.yaml to search for examples/docs
- [ ] Create chain_tasks.yaml for multi-step workflows

#### Task 1.3: Fix Result Display in GUI
- [ ] Implement proper results viewer component
- [ ] Add JSON/Markdown rendering for results
- [ ] Create gallery view for completed tasks
- [ ] Add result export functionality

### Priority 2: Add CRUD Capabilities

#### Task 2.1: Local File Operations
- [ ] Enhance FileOperationsPlugin with full CRUD
- [ ] Add file browser component to GUI
- [ ] Implement file upload/download
- [ ] Add file editing capabilities

#### Task 2.2: Database Operations
- [ ] Add database CRUD plugin
- [ ] Support for SQLite operations
- [ ] Query builder interface
- [ ] Results table viewer

### Priority 3: UI/UX Improvements

#### Task 3.1: Gallery View for Tasks
- [ ] Create card-based gallery layout
- [ ] Add filtering by task type/status
- [ ] Implement search functionality
- [ ] Add pagination for large result sets

#### Task 3.2: Real-time Updates
- [ ] Add WebSocket support for live updates
- [ ] Progress indicators for running tasks
- [ ] Notification system for completed tasks
- [ ] Auto-refresh task list

### Priority 4: General Improvements

#### Task 4.1: Configuration Management
- [ ] Fix duplicate api_port in processor_config.yaml
- [ ] Add config validation
- [ ] Create settings page in GUI
- [ ] Environment variable management

#### Task 4.2: Error Handling
- [ ] Better error messages for missing API keys
- [ ] Retry logic improvements
- [ ] Error recovery mechanisms
- [ ] Detailed logging viewer

#### Task 4.3: Documentation
- [ ] Update README with troubleshooting
- [ ] Add API documentation
- [ ] Create user guide
- [ ] Add example workflows

## Technical Debt

1. **Code Duplication**: obp-CLI.py and obp-GUI.py share significant code
2. **Plugin System**: Needs better abstraction and error handling
3. **Variable Substitution**: Format_prompt method needs enhancement
4. **Database Schema**: Needs optimization for large datasets

## Quick Fixes Needed Now

1. Fix the web_search_results variable name mismatch in search_tasks.yaml
2. Add proper plugin initialization in both CLI and GUI
3. Fix the results display in GUI
4. Add .env file support for API keys
5. Clean up processor_config.yaml duplicate entries

## Recommended Architecture Changes

1. **Separate Core Logic**: Extract shared code into task_processor_core.py
2. **Plugin Manager**: Create dedicated plugin manager class
3. **Result Handlers**: Implement result formatters for different output types
4. **Task Templates**: Create reusable task templates
5. **Workflow Engine**: Build proper workflow orchestration system