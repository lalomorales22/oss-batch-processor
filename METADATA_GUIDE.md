# Metadata Usage Guide

## 🎯 What is Metadata?

Metadata allows you to customize how tasks are processed. Think of it as configuration options that tell the system exactly how you want your task handled.

## 🔧 How to Use Metadata in GUI

### Method 1: Key-Value Builder (Recommended)
1. Select your task type
2. Use the "Add Metadata" button to add key-value pairs
3. The system will automatically convert to JSON

### Method 2: Direct JSON Input
Enter JSON directly in the metadata field:
```json
{"filename": "my_report.md", "language": "python"}
```

## 📝 Common Metadata Options

### 🔍 For Search Tasks
```json
{
  "search_query": "AI safety 2025",
  "comparison": true,
  "filename": "research_report.md"
}
```

### ✏️ For Content Creation
```json
{
  "tone": "professional",
  "audience": "executives", 
  "format": "bullet_points",
  "filename": "content.md"
}
```

### ⚙️ For Processing Tasks
```json
{
  "format": "bullet_points",
  "improve_clarity": true,
  "simplify": true
}
```

### 💻 For Code Generation
```json
{
  "language": "python",
  "filename": "analyzer.py",
  "include_docs": true,
  "include_tests": true
}
```

### 📁 For File Operations
```json
{
  "operation": "search",
  "search_text": "TODO",
  "pattern": "*.py",
  "filename": "todo_summary.md"
}
```

## 🎨 File Operations Available

### Basic CRUD:
- **operation**: `create`, `read`, `update`, `delete`
- **filename**: Target file name
- **file_content**: Content to write

### Advanced Operations:
- **operation**: `search` - Find text in files
- **search_text**: Text to search for
- **pattern**: File pattern like `*.py` or `*.js`
- **operation**: `list` - List files
- **recursive**: `true` for subdirectories
- **operation**: `backup` - Create backup

### Examples:

**Search for TODOs:**
```json
{
  "operation": "search",
  "search_text": "TODO",
  "pattern": "*.py"
}
```

**Create a new file:**
```json
{
  "operation": "create",
  "filename": "my_notes.md",
  "file_content": "# My Notes\n\nContent here..."
}
```

**List all Python files:**
```json
{
  "operation": "list",
  "pattern": "*.py",
  "recursive": true
}
```

## 🌐 Web Search Options

All task types now support optional web search:

```json
{
  "search_query": "latest React best practices",
  "filename": "react_guide.md"
}
```

The system will:
1. Search the web for your query
2. Analyze the results
3. Use the information in your task

## 📊 Format Options

### Text Formats:
- `"format": "bullet_points"` - Convert to bullets
- `"format": "markdown"` - Structured markdown
- `"format": "json"` - JSON output
- `"format": "csv"` - Comma separated

### Code Formats:
- `"language": "python"` - Python code
- `"language": "javascript"` - JavaScript
- `"language": "sql"` - SQL queries
- `"style": "functional"` - Functional programming style

## 🎯 Task-Specific Examples

### Research Report:
```json
{
  "search_query": "renewable energy trends 2025",
  "comparison": true,
  "regions": "global",
  "filename": "energy_report.md",
  "format": "markdown"
}
```

### Data Analysis Script:
```json
{
  "language": "python",
  "filename": "data_analyzer.py",
  "include_docs": true,
  "libraries": "pandas,matplotlib",
  "optimize": true
}
```

### Blog Post:
```json
{
  "tone": "conversational",
  "seo_optimized": true,
  "keywords": "productivity,remote work",
  "word_count": 1500,
  "filename": "blog_post.md"
}
```

### File Cleanup:
```json
{
  "operation": "search",
  "search_text": "deprecated",
  "pattern": "*.js",
  "create_backup": true,
  "filename": "cleanup_report.md"
}
```

## 💡 Pro Tips

1. **Start Simple**: Use basic options first, then add more
2. **Use Quotes**: Always quote string values in JSON
3. **Boolean Values**: Use `true/false` not `"true"/"false"`  
4. **File Extensions**: Match the content type (.md, .py, .js)
5. **Combine Options**: Mix search, format, and file options

## 🚨 Common Mistakes

❌ **Wrong**: `{"include_docs": "true"}`
✅ **Right**: `{"include_docs": true}`

❌ **Wrong**: `{filename: "test.md"}`  
✅ **Right**: `{"filename": "test.md"}`

❌ **Wrong**: Missing quotes around keys
✅ **Right**: All keys in quotes

## 🔄 Dynamic Metadata

The GUI now provides smart defaults based on task type. When you select:
- **Search**: Adds filename, search_query options
- **Create**: Adds tone, format options  
- **Code**: Adds language, filename options
- **Process**: Adds format, audience options

Just modify the suggested values or add your own!