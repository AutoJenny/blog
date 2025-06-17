# Modular Branch Architecture Project

## ⚠️ CRITICAL WARNING ⚠️

This project operates under a **ZERO TOLERANCE** policy for cross-module contamination or unauthorized branch changes. Any attempt to:
- Modify code in branches other than the current working branch
- Mix code between module branches
- Make changes without explicit branch switching
- Merge into `hub` without review
- Assume module isolation without verification

**WILL RESULT IN IMMEDIATE BRANCH ROLLBACK AND PROJECT RESTART**

## Core Principles and Rules

This project implements a strict branch-based modular architecture where each module exists in its own git branch, completely isolated from others. The primary goals are:

1. **Absolute Module Isolation**: Each module branch contains ONLY its own code, with no possibility of cross-contamination
2. **Technical Enforcement**: Module separation is enforced by git branch boundaries, making it technically impossible to modify other modules
3. **Explicit Integration**: All module combinations happen only through reviewed merges into the `hub` branch

## MANDATORY Rules (No Exceptions)

1. **NEVER** work in multiple module branches simultaneously
2. **ALWAYS** check [ORIENTATION.md](ORIENTATION.md) before any work
3. **NEVER** copy code between module branches
4. **ALWAYS** use the data/API layer for module communication
5. **NEVER** merge into `hub` without complete verification
6. **ALWAYS** start from empty branches for new modules
7. **NEVER** share templates or JS between modules
8. **ALWAYS** document all branch operations
9. **NEVER** bypass branch protection rules
10. **ALWAYS** wait for review before integration

## Branch Structure

1. **Module Branches** (Isolated Development)
   - `base-framework`: Site shell, shared CSS/config only
   - `workflow-navigation`: Navigation module only
   - `workflow-llm-actions`: LLM actions module only
   - `workflow-sections`: Sections module only

2. **Integration Branch**
   - `hub`: Only updated via reviewed merges
   - Contains the integrated, deployable system
   - Protected by strict merge rules

## Getting Started

1. First, read this README completely
2. Review [ORIENTATION.md](ORIENTATION.md) for architecture overview
3. Consult [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for step-by-step process
4. Study [code_mapping.md](code_mapping.md) for module boundaries
5. **VERIFY** you understand branch isolation requirements

## Workflow Process

1. **Branch Selection** (MANDATORY)
   - Identify target module branch
   - Verify current branch is correct
   - Ensure no mixed branch operations
   - **DO NOT PROCEED** without verification

2. **Module Development** (MANDATORY)
   - Work only in current module branch
   - Follow code_mapping.md strictly
   - Remove any cross-module code
   - **DO NOT PROCEED** if other module code found

3. **Integration** (MANDATORY)
   - Verify module is completely isolated
   - Test all endpoints and functionality
   - Document changes for review
   - **DO NOT PROCEED** without complete testing

4. **Hub Merge** (MANDATORY)
   - Request review of changes
   - Verify no cross-contamination
   - Follow merge checklist
   - **DO NOT PROCEED** without approval

## Module Independence

Each module branch must:
1. Contain only its own code
2. Use only the shared data/API layer
3. Have no direct dependencies on other modules
4. Maintain its own templates and assets
5. Be deployable in isolation

## Technical Safeguards

1. **Branch Protection**
   - Protected branches require review
   - No direct pushes to `hub`
   - Strict merge requirements
   - Automated contamination checks

2. **Code Isolation**
   - No shared templates or JS
   - Only CSS/config in base-framework
   - Explicit API boundaries
   - No cross-branch imports

3. **Integration Control**
   - Reviewed merges only
   - Complete testing required
   - Documented changes
   - Explicit approval needed

## Emergency Procedures

1. **Branch Contamination**
   - Stop all work immediately
   - Document the contamination
   - Reset branch to clean state
   - **DO NOT ATTEMPT FIXES** without review

2. **Integration Issues**
   - Revert `hub` merge immediately
   - Document the problem
   - Reset to last known good state
   - **DO NOT FORCE PUSH** or bypass protection

3. **Data Layer Problems**
   - Document the issue
   - Test in isolation
   - Wait for review
   - **DO NOT MODIFY** shared interfaces

## Important Reminders

1. **NEVER**:
   - Mix code between branches
   - Skip branch verification
   - Modify multiple modules at once
   - Assume branch isolation
   - Bypass merge protection
   - Share code between modules
   - Make cross-branch changes
   - Force push to protected branches
   - Skip integration tests
   - Merge without review

2. **ALWAYS**:
   - Verify current branch
   - Test in isolation
   - Get explicit review
   - Follow merge process
   - Document all changes
   - Check for contamination
   - Use data layer only
   - Wait for approval
   - Maintain branch boundaries
   - Follow protection rules

## Getting Help

1. **Documentation**
   - Review ORIENTATION.md
   - Check IMPLEMENTATION_PLAN.md
   - Consult code_mapping.md
   - **DO NOT PROCEED** without understanding

2. **Issues**
   - Document the problem
   - Identify affected branches
   - Wait for review
   - **DO NOT ATTEMPT FIXES** without approval

3. **Questions**
   - Review all documentation first
   - Ask about specific branch/module
   - Wait for explicit guidance
   - **DO NOT MAKE ASSUMPTIONS**

Remember: The entire purpose of this architecture is to make it **technically impossible** to accidentally modify code in other modules. If you find yourself able to affect other modules, something is wrong - stop immediately and seek review. 