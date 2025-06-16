# Modular Refactoring Project

⚠️ **CRITICAL DATABASE WARNING** ⚠️
1. **NEVER** modify the database schema without explicit written permission
2. **NEVER** run any database migration scripts without explicit written permission
3. **NEVER** create new database tables without explicit written permission
4. **ALWAYS** check /docs/database/ before any database-related work
5. **ALWAYS** use existing database schema as documented
6. **ALWAYS** verify database operations against /docs/database/schema.md
7. **ALWAYS** make a full backup using `pg_dump` before any database changes
8. **ALWAYS** test database changes in a development environment first
9. **ALWAYS** document any database changes in /docs/database/changes.md
10. **ALWAYS** get user review and approval for any database changes

The existing database schema is fully functional and powers the current system. Any unauthorized database changes will be considered a critical security violation.

## ⚠️ CRITICAL WARNING ⚠️

This project operates under a **ZERO TOLERANCE** policy for unauthorized changes or deviations from the defined process. Any attempt to:
- Skip steps
- Make unauthorized changes
- Modify working code without permission
- Proceed without explicit user approval
- Assume functionality without verification

**WILL RESULT IN IMMEDIATE ROLLBACK AND POTENTIAL PROJECT DELAYS**

## Core Principles and Rules

This project implements a strict modular architecture where each module operates as an independent silo. The primary goals are:

1. **Module Independence**: Each module must be self-sufficient and cannot interfere with other modules
2. **LLM Safety**: Even a determined LLM cannot damage one module while working in another without explicit user permission
3. **Controlled Evolution**: All changes must follow the defined workflow and obtain user permission for any modifications beyond the strict remit

## MANDATORY Rules (No Exceptions)

1. **NEVER** make changes to code or data beyond the strict remit in these documents without explicit user permission
2. **ALWAYS** check the [Transition Checklist](transition_checklist.md) before starting any work
3. **NEVER** modify working code without explicit permission
4. **ALWAYS** test thoroughly before claiming any functionality is working
5. **NEVER** proceed with coding without explicit instructions
6. **ALWAYS** verify each step is complete before proceeding
7. **NEVER** assume anything works without testing
8. **ALWAYS** document all changes and test results
9. **NEVER** skip validation steps
10. **ALWAYS** wait for user review before proceeding

## Getting Started

1. First, read this README completely
2. Review the [Transition Checklist](transition_checklist.md) to understand current progress
3. Consult the [Technical Implementation Guide](transition_implementation.md) for detailed steps
4. Follow the [Development Setup Guide](dev_setup.md) to configure your environment
5. **VERIFY** you understand all requirements before proceeding

## Documentation Structure

### Core Implementation
- [Transition Checklist](transition_checklist.md) - Track progress and next steps
- [Technical Implementation Guide](transition_implementation.md) - Detailed implementation steps
- [Module Contracts](module_contracts.md) - Module interface definitions
- [Code Mapping](code_mapping.md) - Current to new code structure mapping

### Standards and Guidelines
- [API Standards](api_standards.md) - API design and implementation standards
- [Testing Standards](testing_standards.md) - Testing requirements and procedures
- [Error Handling Guide](error_handling.md) - Error handling patterns and procedures
- [Security Guide](security_guide.md) - Security requirements and best practices

### Development Process
- [Development Setup](dev_setup.md) - Environment setup and configuration
- [Testing Guide](testing_guide.md) - Comprehensive testing procedures
- [Integration Guide](integration_guide.md) - Module integration procedures
- [Versioning Guide](versioning.md) - Version control and release procedures

### Performance and Monitoring
- [Performance Optimization](performance_optimization.md) - Performance requirements and optimization
- [Monitoring and Logging](monitoring_logging.md) - System monitoring and logging standards

## Workflow Process

1. **Check Current Status** (MANDATORY)
   - Review the [Transition Checklist](transition_checklist.md)
   - Identify the next uncompleted task
   - Verify no other work is in progress
   - **DO NOT PROCEED** without completing this step

2. **Implementation** (MANDATORY)
   - Follow the [Technical Implementation Guide](transition_implementation.md)
   - Adhere to all standards and guidelines
   - Test thoroughly before proceeding
   - **DO NOT PROCEED** without completing this step

3. **Validation** (MANDATORY)
   - Complete all required tests
   - Verify against performance requirements
   - Document any issues or deviations
   - **DO NOT PROCEED** without completing this step

4. **Review** (MANDATORY)
   - Mark completed tasks in the checklist
   - Update relevant documentation
   - Wait for user review before proceeding
   - **DO NOT PROCEED** without completing this step

## Module Independence

Each module must:
1. Have its own isolated codebase
2. Define clear interfaces through contracts
3. Handle its own errors and logging
4. Maintain its own test suite
5. Have independent deployment procedures

## LLM Safety Measures

1. **Strict Boundaries**
   - Each module has defined interfaces
   - No direct access to other modules' internals
   - All cross-module communication through defined channels

2. **Permission System**
   - Explicit user permission required for cross-module changes
   - Clear documentation of module boundaries
   - Validation of all cross-module operations

3. **Change Control**
   - All changes must follow the defined workflow
   - No autonomous modifications without permission
   - Thorough testing of all changes

## Progress Tracking

1. **Daily Progress** (MANDATORY)
   - Update the [Transition Checklist](transition_checklist.md)
   - Document completed tasks
   - Note any issues or blockers
   - **VERIFY** all steps are complete

2. **Review Points** (MANDATORY)
   - After each phase completion
   - Before major changes
   - When encountering issues
   - **DO NOT PROCEED** without review

3. **Documentation Updates** (MANDATORY)
   - Keep all documentation current
   - Update relevant guides
   - Maintain change logs
   - **VERIFY** all updates are complete

## Emergency Procedures

1. **Code Issues**
   - Stop all work immediately
   - Document the issue
   - Wait for user guidance
   - **DO NOT ATTEMPT FIXES** without permission

2. **System Problems**
   - Use the restart script: `/scripts/dev/restart_flask_dev.sh`
   - Never use alternative ports
   - Follow the error handling guide
   - **DO NOT MODIFY** system configuration

3. **Data Problems**
   - Do not attempt fixes without permission
   - Document the issue
   - Wait for user guidance
   - **DO NOT MODIFY** any data

## Important Reminders

1. **NEVER**:
   - Make unauthorized changes
   - Skip testing steps
   - Modify working code without permission
   - Assume functionality without verification
   - Use alternative ports or configurations
   - Proceed without explicit permission
   - Skip documentation updates
   - Ignore error messages
   - Make assumptions about functionality
   - Take shortcuts in the process

2. **ALWAYS**:
   - Check documentation first
   - Test thoroughly
   - Get explicit permission
   - Follow the defined workflow
   - Update the checklist
   - Verify each step
   - Document all changes
   - Wait for user review
   - Follow error handling procedures
   - Maintain proper logs

## Getting Help

1. **Documentation**
   - Review all relevant guides
   - Check the checklist
   - Consult implementation details
   - **DO NOT PROCEED** without understanding

2. **Issues**
   - Document the problem
   - Check existing documentation
   - Wait for user guidance
   - **DO NOT ATTEMPT FIXES** without permission

3. **Questions**
   - Review all documentation
   - Check the checklist
   - Ask for clarification
   - **DO NOT MAKE ASSUMPTIONS**

## ⚠️ FINAL WARNING ⚠️

Remember: When in doubt, stop and ask. It's better to wait for guidance than to make potentially harmful changes. Any deviation from these guidelines will result in immediate rollback and potential project delays.

**THERE ARE NO SHORTCUTS IN THIS PROCESS** 