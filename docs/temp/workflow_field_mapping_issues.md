# Workflow Field Mapping Issues
 
## Current State
- The "Initial" step works correctly
- "Idea Scope" step: selection works but doesn't persist
- "Idea Seed" step: missing dropdown menu in Inputs
- Outputs accordion shows duplicate couplets, with only the second one working correctly

## Identified Issues

### 1. Step Configuration Inconsistency
- "Initial" step has proper configuration in `workflow_step_entity`
- "Idea Scope" and "Idea Seed" steps have different/missing configurations
- Database backups show inconsistency in step configurations
- **Action Required**: Audit and standardize step configurations across all steps

### 2. Field Mapping Database State
Current mapping in `workflow_field_mapping` table:
- `idea_seed` (id: 33, order: 1)
- `basic_idea` (id: 1, order: 2)
- `provisional_title` (id: 2, order: 3)
- `idea_scope` (id: 3, order: 4)
**Action Required**: Verify these mappings are correctly reflected in the UI

### 3. Accordion Type Parameter
- Now included in API call but potential issues with determination:
```javascript
const accordion_type = section === 'inputs' ? 'inputs' : 'outputs';
```
- All non-'inputs' sections treated as 'outputs'
- **Action Required**: Review if this binary classification is correct for all cases

### 4. Template Inheritance Issue
- Duplicate output couplets appearing in template
- First couplet: Shows default value (basic_idea)
- Second couplet: Works correctly
- **Action Required**: Investigate template inheritance and includes

### 5. Database Configuration Dependencies
- JSONB configuration data required for proper field mapping
- Different configurations exist for different steps
- **Action Required**: Audit JSONB configurations across all steps

## Next Steps

1. **Template Investigation**
   - Trace template inheritance
   - Identify source of duplicate outputs
   - Fix template includes

2. **Configuration Standardization**
   - Audit step configurations
   - Standardize JSONB format
   - Apply consistent configuration across all steps

3. **Field Mapping Verification**
   - Verify database mappings
   - Test field persistence
   - Validate accordion type handling

4. **UI Component Testing**
   - Test dropdown population
   - Verify field selection
   - Check persistence behavior

## Progress Tracking

- [ ] Fix template inheritance
- [ ] Standardize step configurations
- [ ] Verify field mappings
- [ ] Test UI components
- [ ] Document final configuration format 