# Hybrid Calendar Ideas Implementation Plan

## **OVERVIEW**
Implementing a hybrid week + post system for calendar ideas to solve the fundamental confusion between week-based idea selection and post-specific development.

## **PROBLEM STATEMENT**
- Current URL: `/planning/posts/60/calendar/ideas` 
- Issue: Hardcoded to Post 60 (from Sept 28) but we're in Week 39 (October)
- Confusion: Same post ID for different time periods
- Limitation: Can't create multiple posts per week easily

## **SOLUTION APPROACH**
**Hybrid System**: Week-based idea selection + Topic-based post creation

### **New Workflow:**
```
1. User visits: /planning/calendar/ideas/week/39
2. Page loads ideas for Week 39
3. User selects idea → Check topic deduplication
4. If new topic → Create new post ID
5. Redirect to: /planning/posts/{new_post_id}/development
6. User can return to create more posts for same week
```

---

## **PHASE 1: CORE INFRASTRUCTURE**

### **1.1 New Routes to Add**

#### **Week-Based Route:**
```python
@bp.route('/calendar/ideas/week/<int:week_number>')
def planning_calendar_ideas_week(week_number):
    """Week-based idea generation - creates new posts as needed"""
    # Load ideas for specific week
    # No post_id context - week-based
    # Template: ideas_week.html
```

#### **Post Creation Redirect Route:**
```python
@bp.route('/api/posts/redirect-after-creation', methods=['POST'])
def api_redirect_after_creation():
    """Handle post creation and redirect logic"""
    # Create new post
    # Return redirect URL
    # Used by JavaScript after idea selection
```

### **1.2 Template Changes**

#### **New Template:**
- `templates/planning/calendar/ideas_week.html`
- Week-based version of ideas page
- No post_id context
- Clear messaging about creating new posts

#### **Modified Template:**
- `templates/planning/calendar/ideas.html`
- Detect context (week vs post)
- Show appropriate messaging
- Handle both modes

### **1.3 JavaScript Logic Updates**

#### **Context Detection:**
```javascript
// Detect if working with week or post
if (window.weekNumber && !window.postId) {
    // Week-based mode - create posts as needed
    mode = 'week-based';
} else if (window.postId) {
    // Post-based mode - work with existing post
    mode = 'post-based';
}
```

#### **Updated confirmSelection Function:**
```javascript
async function confirmSelection() {
    if (mode === 'week-based') {
        // Check topic deduplication
        // Create new post if needed
        // Redirect to post development
    } else if (mode === 'post-based') {
        // Current logic - work with existing post
    }
}
```

---

## **PHASE 2: NAVIGATION UPDATES**

### **2.1 Files to Update**

#### **Main Navigation:**
- `templates/shared/blog_pipeline_header.html`
- `templates/planning/includes/navigation.html`
- `templates/planning/includes/condensed_header.html`

#### **Dashboard Links:**
- `templates/index.html`
- `templates/planning/dashboard.html`

### **2.2 Navigation Strategy**

#### **Week-Based Links:**
```html
<a href="{{ url_for('planning.planning_calendar_ideas_week', week_number=current_week) }}">
    💡 Idea Generation (Week {{ current_week }})
</a>
```

#### **Post-Based Links:**
```html
<a href="{{ url_for('planning.planning_calendar_ideas', post_id=post_id) }}">
    💡 Idea Generation (Post {{ post_id }})
</a>
```

### **2.3 URL Structure**

#### **New URLs:**
- `/planning/calendar/ideas/week/39` - Week-based idea generation
- `/planning/calendar/ideas/week/40` - Different week

#### **Existing URLs (Modified):**
- `/planning/posts/60/calendar/ideas` - Post-specific (existing posts)
- `/planning/posts/61/calendar/ideas` - New post after creation

---

## **PHASE 3: API ENDPOINTS**

### **3.1 Existing Endpoints (Working)**
- ✅ `/planning/api/calendar/ideas/week/{week_number}` - Load ideas for week
- ✅ `/planning/api/posts/check-topic` - Topic deduplication
- ✅ `/planning/api/posts/create-new` - New post creation
- ✅ `/planning/api/posts/{post_id}/idea-seed` - Get/Set idea seed
- ✅ `/planning/api/posts/{post_id}/expanded-idea` - Get/Generate expanded idea

### **3.2 New Endpoints Needed**
```python
@bp.route('/api/posts/redirect-after-creation', methods=['POST'])
def api_redirect_after_creation():
    """Handle post creation and return redirect URL"""
    
@bp.route('/api/calendar/current-week')
def api_current_week():
    """Get current week number for navigation"""
```

### **3.3 Endpoint Testing Checklist**
- [ ] `/planning/api/calendar/ideas/week/39` - Returns ideas for week 39
- [ ] `/planning/api/posts/check-topic` - Detects existing topics
- [ ] `/planning/api/posts/create-new` - Creates new post ID
- [ ] `/planning/api/posts/redirect-after-creation` - Returns redirect URL

---

## **PHASE 4: WORKFLOW INTEGRATION**

### **4.1 User Journey Mapping**

#### **Scenario 1: New Week, New Topic**
```
1. User visits: /planning/calendar/ideas/week/39
2. Page shows: "Ideas for Week 39"
3. User selects: "Scottish Highland Games"
4. System checks: Topic doesn't exist this year
5. System creates: New post ID 61
6. System redirects: /planning/posts/61/development
7. User develops: Post 61 content
```

#### **Scenario 2: New Week, Existing Topic**
```
1. User visits: /planning/calendar/ideas/week/39
2. Page shows: "Ideas for Week 39"
3. User selects: "Celtic folklore"
4. System checks: Topic exists (Post 60)
5. System redirects: /planning/posts/60/development
6. User continues: Existing post development
```

#### **Scenario 3: Existing Post**
```
1. User visits: /planning/posts/60/calendar/ideas
2. Page shows: "Post 60 - Celtic folklore"
3. User selects: Different idea
4. System updates: Post 60 with new idea
5. User continues: Post 60 development
```

### **4.2 Error Handling**

#### **Edge Cases:**
- No ideas available for week
- Topic check fails
- Post creation fails
- Redirect fails
- Invalid week number

#### **User Messaging:**
- "Creating new post for this topic..."
- "Using existing post for this topic..."
- "No ideas available for this week"
- "Error creating post - please try again"

---

## **PHASE 5: TESTING & VALIDATION**

### **5.1 Test Scenarios**

#### **Week-Based Testing:**
- [ ] Load ideas for current week (39)
- [ ] Load ideas for past week (38)
- [ ] Load ideas for future week (40)
- [ ] Create new post for new topic
- [ ] Reuse existing post for existing topic
- [ ] Multiple posts per week

#### **Post-Based Testing:**
- [ ] Load existing post (60)
- [ ] Update idea for existing post
- [ ] Generate expanded idea
- [ ] Navigate between post stages

#### **Navigation Testing:**
- [ ] Week-based links work
- [ ] Post-based links work
- [ ] Redirects work correctly
- [ ] Back navigation works

### **5.2 URL Testing Checklist**

#### **Week-Based URLs:**
- [ ] `/planning/calendar/ideas/week/39` - Current week
- [ ] `/planning/calendar/ideas/week/40` - Next week
- [ ] `/planning/calendar/ideas/week/38` - Previous week

#### **Post-Based URLs:**
- [ ] `/planning/posts/60/calendar/ideas` - Existing post
- [ ] `/planning/posts/61/calendar/ideas` - New post
- [ ] `/planning/posts/62/calendar/ideas` - Another new post

#### **API URLs:**
- [ ] `/planning/api/calendar/ideas/week/39`
- [ ] `/planning/api/posts/check-topic`
- [ ] `/planning/api/posts/create-new`
- [ ] `/planning/api/posts/redirect-after-creation`

---

## **PHASE 6: IMPLEMENTATION ORDER**

### **6.1 Step-by-Step Implementation**

#### **Step 1: Fix Server Issues**
- [ ] Resolve duplicate endpoint error
- [ ] Get server running
- [ ] Test existing functionality

#### **Step 2: Add New Routes**
- [ ] Add week-based route
- [ ] Add redirect route
- [ ] Test routes work

#### **Step 3: Create New Template**
- [ ] Create ideas_week.html
- [ ] Implement week-based logic
- [ ] Test template rendering

#### **Step 4: Update JavaScript**
- [ ] Add context detection
- [ ] Update confirmSelection function
- [ ] Test JavaScript logic

#### **Step 5: Update Navigation**
- [ ] Update main navigation
- [ ] Update dashboard links
- [ ] Test navigation works

#### **Step 6: End-to-End Testing**
- [ ] Test complete workflow
- [ ] Test error cases
- [ ] Test edge cases

---

## **PHASE 7: DEBUGGING REFERENCE**

### **7.1 Common Issues & Solutions**

#### **Server Won't Start:**
- Check for duplicate function names
- Check for syntax errors
- Check for missing imports

#### **Routes Not Working:**
- Check route definitions
- Check blueprint registration
- Check URL patterns

#### **JavaScript Errors:**
- Check context detection
- Check API calls
- Check error handling

#### **Navigation Issues:**
- Check URL generation
- Check template includes
- Check JavaScript navigation

### **7.2 Logging & Debugging**

#### **Add Debug Logging:**
```python
logger.debug(f"Week-based mode: week_number={week_number}")
logger.debug(f"Post-based mode: post_id={post_id}")
logger.debug(f"Topic check result: {check_result}")
logger.debug(f"Post creation result: {post_id}")
```

#### **JavaScript Console Logging:**
```javascript
console.log('Mode detected:', mode);
console.log('Selected idea:', selectedIdea);
console.log('Topic check result:', checkData);
console.log('Post creation result:', newPostData);
```

---

## **PHASE 8: SUCCESS CRITERIA**

### **8.1 Functional Requirements**
- [ ] Week-based idea selection works
- [ ] Post creation works for new topics
- [ ] Post reuse works for existing topics
- [ ] Multiple posts per week possible
- [ ] Navigation works correctly
- [ ] Error handling works

### **8.2 User Experience Requirements**
- [ ] Clear messaging about context
- [ ] Smooth transitions between modes
- [ ] Intuitive workflow
- [ ] No confusion about post IDs
- [ ] Easy to create multiple posts

### **8.3 Technical Requirements**
- [ ] Backward compatibility maintained
- [ ] Performance acceptable
- [ ] Error handling robust
- [ ] Code maintainable
- [ ] Documentation complete

---

## **PHASE 9: ROLLBACK PLAN**

### **9.1 If Implementation Fails**
- Revert to current system
- Keep existing routes working
- Maintain current functionality
- Document issues for future

### **9.2 Backup Strategy**
- Git commits at each phase
- Test existing functionality
- Keep current templates
- Maintain current API endpoints

---

## **IMPLEMENTATION STATUS**

### **Completed:**
- [x] Problem analysis
- [x] Solution design
- [x] Implementation plan
- [x] API endpoints (partially)

### **In Progress:**
- [ ] Server issues resolution
- [ ] New routes implementation
- [ ] Template creation
- [ ] JavaScript updates

### **Pending:**
- [ ] Navigation updates
- [ ] End-to-end testing
- [ ] Error handling
- [ ] Documentation

---

**Last Updated:** October 8, 2025
**Status:** Ready for implementation
**Next Step:** Fix server issues and begin Phase 1
