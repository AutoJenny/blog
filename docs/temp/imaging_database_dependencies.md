# Imaging Module Database Dependencies Audit

## Summary
The imaging module has dependencies on several core database tables that are shared across multiple stages (planning, authoring, imaging). These are **NOT** authoring-specific or planning-specific tables, but rather core system tables.

## Database Tables Used by Imaging Module

### Core System Tables (Shared Across All Stages)

#### 1. `post` table
- **Used by**: `blueprints/imaging.py` (line 146)
- **Purpose**: Stores basic post information (id, title, summary, status, created_at, updated_at)
- **Dependency Type**: Core system table - used by planning, authoring, and imaging
- **Risk Level**: LOW - This is a fundamental table used by all stages

#### 2. `post_development` table  
- **Used by**: `blueprints/imaging.py` (line 157)
- **Purpose**: Stores post development data (idea_seed, expanded_idea, basic_idea, provisional_title)
- **Dependency Type**: Core system table - used by planning, authoring, and imaging
- **Risk Level**: LOW - This is a fundamental table used by all stages

#### 3. `post_section` table
- **Used by**: `blueprints/imaging.py` (lines 184, 283), `modules/image_generation/api.py` (line 103)
- **Purpose**: Stores section data including image_prompts JSON field
- **Dependency Type**: Core system table - used by planning, authoring, and imaging
- **Risk Level**: LOW - This is a fundamental table used by all stages

#### 4. `llm_prompt` table
- **Used by**: `blueprints/imaging.py` (lines 208, 232), `modules/image_generation/api.py` (lines 31, 78)
- **Purpose**: Stores LLM prompts including "Image Generation" prompt
- **Dependency Type**: Core system table - used by planning, authoring, and imaging
- **Risk Level**: LOW - This is a shared LLM system table

#### 5. `llm_model` table
- **Used by**: `modules/image_generation/api.py` (line 40)
- **Purpose**: Stores available LLM models (sdxl-lora, dall-e-3, dall-e-2)
- **Dependency Type**: Core system table - used by authoring and imaging
- **Risk Level**: LOW - This is a shared LLM system table

#### 6. `llm_provider` table
- **Used by**: `modules/image_generation/api.py` (line 41)
- **Purpose**: Stores LLM provider information
- **Dependency Type**: Core system table - used by authoring and imaging
- **Risk Level**: LOW - This is a shared LLM system table

### Imaging-Specific Tables (Independent)

#### 1. `imaging_llm_config` table
- **Used by**: `modules/imaging/llm_config.py` (multiple lines)
- **Purpose**: Stores imaging-specific LLM configuration
- **Dependency Type**: Imaging-specific - independent from other stages
- **Risk Level**: NONE - This is imaging-specific and doesn't affect other stages

## Analysis Results

### ✅ GOOD NEWS: No Authoring-Specific Dependencies
The imaging module does **NOT** use any tables that are specific to the authoring stage. All tables it uses are core system tables shared across multiple stages.

### ✅ GOOD NEWS: No Planning-Specific Dependencies  
The imaging module does **NOT** use any tables that are specific to the planning stage. All tables it uses are core system tables shared across multiple stages.

### ✅ GOOD NEWS: Independent Configuration Storage
The imaging module has its own independent configuration storage (`imaging_llm_config` table) that doesn't interfere with other stages.

## Risk Assessment

### LOW RISK Tables
All tables used by the imaging module are **LOW RISK** because:
1. They are core system tables used by multiple stages
2. Changes to imaging functionality won't break other stages
3. The imaging module only reads from these tables (no destructive operations)
4. The imaging module has its own independent configuration storage

### NO RISK Tables
The `imaging_llm_config` table is **NO RISK** because:
1. It's imaging-specific and independent
2. Other stages don't use this table
3. Changes to this table won't affect other stages

## Recommendations

### ✅ PROCEED WITH CONFIDENCE
The imaging module can be safely modified without breaking other stages because:
1. It only uses core system tables that are designed to be shared
2. It has its own independent configuration storage
3. It doesn't perform destructive operations on shared tables
4. All dependencies are read-only operations on core system data

### ✅ NO ADDITIONAL DATABASE SCHEMA NEEDED
The imaging module doesn't need additional database schema because:
1. It uses existing core system tables appropriately
2. It has its own independent configuration storage
3. All required functionality is supported by existing tables

## Conclusion
The imaging module has **ZERO** dependencies on authoring-specific or planning-specific tables. All dependencies are on core system tables that are designed to be shared across stages. The imaging module is **SAFE TO MODIFY** without risk of breaking other stages.
