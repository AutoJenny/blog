# Template Canonicalization Strategy

## Problem Statement

The blog project has accumulated **massive template duplication** across multiple microservice directories and stages, causing:

- **280 HTML files** with significant duplicates (22 `index.html`, 6 `sections_panel.html`, etc.)
- **Tool confusion**: `read_file` tool returning incorrect cached/canonical versions instead of actual files
- **Development errors**: Editing wrong files, changes not applying, inconsistent behavior
- **Maintenance nightmare**: Changes need to be replicated across multiple duplicate files

## Current Problematic Structure

```
/Users/autojenny/Documents/projects/blog/
├── blog-core/templates/              # Duplicate templates
├── blog-launchpad/templates/         # Duplicate templates  
├── blog-post-info/templates/         # Duplicate templates
├── blog-post-sections/templates/    # Duplicate templates
├── templates/                        # Current canonical location
│   ├── shared/                      # Properly shared
│   ├── imaging/                     # Stage-specific
│   ├── authoring/                   # Stage-specific
│   └── planning/                    # Stage-specific
└── templates/post_sections/         # More duplicates
```

## Target Canonical Structure

```
/templates/
├── shared/                          # Truly shared across ALL services
│   ├── blog_pipeline_header.html    # ✅ Already canonical
│   ├── sections_panel.html          # ⚠️ NEEDS CANONICALIZATION
│   ├── header.html                  # ⚠️ NEEDS CANONICALIZATION
│   └── data_tab.html                # ⚠️ NEEDS CANONICALIZATION
├── imaging/                         # Imaging-stage specific ONLY  
│   ├── includes/
│   │   ├── model_selection_panel.html
│   │   ├── prompt_construction_panel.html
│   │   └── debugging_panel_image_generation.html
│   └── sections/
│       └── image_generation.html
├── authoring/                       # Authoring-stage specific ONLY
└── planning/                        # Planning-stage specific ONLY
```

## Canonicalization Strategy

### Phase 1: Fix Immediate Issues (Current Focus)
- ✅ Fix `sections_panel.html` duplication for imaging page
- ✅ Create canonical version in `/templates/shared/`
- ✅ Update imaging includes to use canonical path
- ✅ Test imaging page functionality

### Phase 2: Ongoing Cleanup (As Pages Are Worked On)
When working on any page that has template issues:

1. **Identify duplicates**: `find -name "template_name.html"`
2. **Determine canonical location**: Based on usage and stage specificity
3. **Create/or update canonical version**: Ensure it has latest functionality
4. **Update all includes**: Point to canonical path
5. **Test thoroughly**: Verify page works with canonical version
6. **Remove duplicates**: Only after validation
7. **Document changes**: Update this strategy document

### Phase 3: Prevention Mechanisms

#### Tool-Level Safeguards
- **`read_file` tool**: Must resolve to actual file paths, not cached versions
- **Path validation**: Warn when accessing duplicate templates
- **Canonical enforcement**: Prevent editing non-canonical files

#### Development Conventions
- **Single source of truth**: Each template type has ONE canonical location
- **Clear naming**: Template names indicate their purpose and scope
- **Include path standards**: Always use canonical paths in `{% include %}`
- **Documentation**: Maintain this strategy document with current canonical locations

## Current Canonical Template Locations

| Template Type | Canonical Location | Status |
|---------------|-------------------|---------|
| `blog_pipeline_header.html` | `templates/shared/blog_pipeline_header.html` | ✅ Canonical |
| `sections_panel.html` | `templates/shared/sections_panel.html` | ✅ Canonical |
| `image_generation.html` | `templates/imaging/sections/image_generation.html` | ✅ Canonical |
| `model_selection_panel.html` | `templates/imaging/includes/model_selection_panel.html` | ✅ Canonical |

## Known Duplications Requiring Future Cleanup

### High Priority
- **✅ `sections_panel.html`**: FIXED - Now canonical with symlinks
- **5x `header.html`**: Navigation/base templates  
- **4x `image_generation.html`**: Workflow step templates

### Medium Priority  
- **22x `index.html`**: Various microservice index pages
- **Multiple debugging panels**: Authoring vs Imaging specific versions
- **Data tab variations**: Different implementations across stages

### Low Priority
- **Microservice templates**: Legacy templates in `blog-*` directories
- **Test templates**: Multiple test/sandbox implementations

## Implementation Notes

### Git Workflow for Canonicalization
1. **Commit before changes**: Always backup before template canonicalization
2. **Incremental commits**: One template type per commit for easier rollback
3. **Documentation updates**: Update this file with each canonicalization
4. **Validation required**: Test affected pages before marking complete

### Emergency Rollback
If canonicalization breaks functionality:

```bash
# Revert last canonicalization commit
git reset --hard HEAD~1

# Or restore from backup
tar -xzf /tmp/blog_backup_*.tar.gz /Users/autojenny/Documents/projects/blog
```

### Prevention Checklist
- [ ] Use canonical paths in all `{% include %}` statements
- [ ] Don't create templates in microservice directories
- [ ] Update this document when fixing duplications
- [ ] Test thoroughly before committing canonicalization changes
- [ ] Consider if template really needs stage-specific customization

## Success Metrics

- **Reduce duplication**: Target <5 duplicate template files
- **Tool reliability**: `read_file` always shows actual file content
- **Development speed**: Changes apply immediately without confusion
- **Maintenance burden**: Single template to update instead of multiple

---

*Last Updated: October 3, 2025*
*Status: Phase 1 - Fixing sections_panel.html for imaging stage*
