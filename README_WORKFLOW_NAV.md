# Workflow Navigation Module - Auto-Start Branch

This branch is configured to automatically display the complete workflow navigation system with real stages, substages, and icons from the `modules/nav` directory.

## 🚀 Quick Start

**To start the server (one command):**
```bash
./start_workflow_nav.sh
```

**To restart the server:**
```bash
./scripts/dev/restart_flask_dev.sh
```

## 🌐 What You Get

When you visit `http://localhost:5000/workflow/`, you'll see:

### ✅ Complete Workflow Navigation
- **Planning Stage**: Idea (💡), Research (🔍), Structure (🗂️)
- **Writing Stage**: Content (✏️), Meta Info (🏷️), Images (🖼️)  
- **Publishing Stage**: Preflight (✅), Launch (🚀), Syndication (📤)

### ✅ Real Step Names (Not "Step 2", "Step 3")
- **Idea substage**: Basic Idea, Provisional Title
- **Research substage**: Concepts, Facts
- **Structure substage**: Outline, Allocate Facts
- **Content substage**: Sections

### ✅ Active State Highlighting
- Current stage/substage is highlighted with blue borders
- Current step is highlighted in blue text

### ✅ Post Selector
- Dropdown with available posts (currently demo data)

## 🔧 How It Works

### Automatic Integration
- The `modules/nav` module is automatically registered in `app/__init__.py`
- The workflow route (`app/routes/workflow.py`) uses real nav module data
- The template (`app/templates/workflow/index.html`) embeds the nav content directly

### No Template Path Issues
- All nav module content is embedded directly in the workflow template
- CSS styles are embedded to avoid path issues
- No external template includes that can break

### Persistent Configuration
- All settings are committed to git
- The branch will work identically every time you switch to it
- No manual setup required

## 📁 Key Files

- `start_workflow_nav.sh` - One-command startup script
- `app/routes/workflow.py` - Workflow route with nav module integration
- `app/templates/workflow/index.html` - Complete workflow template with embedded nav
- `modules/nav/services.py` - Real workflow stages and substages data
- `app/__init__.py` - Nav module blueprint registration

## 🔄 Making Changes

### To Update Workflow Stages/Substages
Edit `modules/nav/services.py` - changes will appear immediately on refresh.

### To Update the Navigation Template
Edit `modules/nav/templates/nav.html`, then copy the changes to `app/templates/workflow/index.html`.

### To Add Real Database Data
Replace the demo data in `app/routes/workflow.py` with actual database queries.

## 🎯 Current Status

✅ **Working**: Complete workflow navigation with real stage names and icons  
✅ **Working**: Active state highlighting  
✅ **Working**: Post selector (demo data)  
✅ **Working**: Auto-start script  
✅ **Working**: Persistent git configuration  

🔄 **Next Steps**: Replace demo data with real database queries

## 🚨 Troubleshooting

**If the server won't start:**
1. Check that you're on the `workflow-navigation` branch
2. Run `./start_workflow_nav.sh` 
3. Check for any missing dependencies

**If the page shows errors:**
1. The template is self-contained - no external dependencies
2. All CSS is embedded
3. All nav module data is integrated directly

This branch is designed to work immediately without any manual configuration or setup steps. 