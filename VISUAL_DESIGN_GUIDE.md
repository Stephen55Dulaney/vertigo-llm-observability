# Vertigo Debug Toolkit - Visual Design System Guide

## 🎨 **Design Philosophy**
*"Clean, professional, and data-driven interfaces that prioritize clarity and usability for AI prompt management and evaluation."*

---

## 🎯 **Core Design Principles**

### **1. Information Hierarchy**
- **Primary actions** are prominently displayed with blue buttons
- **Secondary actions** use subtle styling (grey/outline buttons)
- **Data visualization** takes center stage with clean cards and metrics

### **2. Professional Color Palette**
- **Primary Blue**: `#007bff` - Navigation, primary buttons, key actions
- **Success Green**: `#28a745` - Success states, positive metrics
- **Warning Orange**: `#ffc107` - Alerts, pending states
- **Neutral Grey**: `#6c757d` - Secondary text, borders, inactive states
- **Light Background**: `#f8f9fa` - Page backgrounds, card containers

### **3. Consistent Spacing & Layout**
- **Card-based design** for content organization
- **Generous whitespace** for readability
- **Consistent padding**: 1rem (16px) for cards, 0.5rem (8px) for buttons
- **Grid-based layouts** using Bootstrap's responsive grid system

---

## 📋 **Page-Specific Design Standards**

## **1. Add Prompt Page (`/prompts/add`) - ✅ GOLD STANDARD**

### **Layout Structure:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Navigation Bar - Blue Background]                              │
├─────────────────────────────────────────────────────────────────┤
│ ⊕ Add New Prompt                    [Back to Prompts - Outline] │
├─────────────────────────────────────────────────────────────────┤
│ ┌─ Prompt Details ─────────────┐ ┌─ Prompt Guidelines ────────┐ │
│ │ • Name* [_____________]       │ │ Available Placeholders:     │ │
│ │ • Version* [1.0] Type* [▼]   │ │ {transcript} - Meeting...   │ │
│ │ • Tags [JSON array]          │ │ {project} - Project name    │ │
│ │ • Content* [Large textarea]  │ │ Best Practices:             │ │
│ │                              │ │ • Be specific about format  │ │
│ │ [Test Prompt - Blue]         │ │ • Include clear instructions│ │
│ └──────────────────────────────┘ │ Example Structure:          │ │
│                                  │ You are a [role]...         │ │
│                                  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Design Elements:**
- **Two-column layout**: Left for input, right for guidance
- **Clear form hierarchy**: Required fields marked with *
- **Helpful guidance panel**: Examples, placeholders, best practices
- **Prominent CTA**: Blue "Test Prompt" button
- **Consistent card styling**: White background, subtle shadows

---

## **2. Prompts Management Page (`/prompts/`) - ✅ GOLD STANDARD**

### **Layout Structure:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Navigation Bar - Blue Background]                              │
├─────────────────────────────────────────────────────────────────┤
│ 💬 Prompts Management    [Load Existing] [Add New - Blue]       │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│ │ sagev1   v1 │ │Risk Assess  │ │Action Orient│                 │
│ │ Transcript  │ │Meeting_anal │ │Meeting_anal │                 │
│ │ new custom  │ │risk mitigꞏ  │ │action delivꞏ│                 │
│ │ 📅2025-08-01│ │📅2025-08-01 │ │📅2025-08-01 │                 │
│ │[▷Test][✏Edit]│ │[▷Test][✏Edit]│ │[▷Test][✏Edit]│                 │
│ │[👁View]     │ │[👁View]     │ │[👁View]     │                 │
│ └─────────────┘ └─────────────┘ └─────────────┘                 │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                 │
│ │Daily Sum... │ │Technical... │ │Executive... │                 │
│ │Daily_summary│ │Meeting_anal │ │Meeting_anal │                 │
│ │daily boss_uꞏ │ │technical ar │ │executive stꞏ│                 │
│ │📅2025-08-01 │ │📅2025-08-01 │ │📅2025-08-01 │                 │
│ │[▷Test][✏Edit]│ │[▷Test][✏Edit]│ │[▷Test][✏Edit]│                 │
│ │[👁View]     │ │[👁View]     │ │[👁View]     │                 │
│ └─────────────┘ └─────────────┘ └─────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Design Elements:**
- **Card-based grid layout**: 3 columns on desktop, responsive
- **Consistent card structure**: Title, type, tags, date, actions
- **Action button styling**: 
  - Blue outline "Test" button (primary action)
  - Grey outline "Edit" and "View" buttons (secondary)
- **Information hierarchy**: Name → Type → Tags → Date → Actions
- **Visual consistency**: Same card shadows, spacing, typography

---

## **3. Prompt Manager (`/prompts/manager`) - ✅ REFERENCE DESIGN**

### **Layout Structure:**
```
┌─────────────────────────────────────────────────────────────────┐
│ [Navigation Bar - Blue Background]                              │
├─────────────────────────────────────────────────────────────────┤
│ ⚙ Prompt Manager                     [Add New Prompt - Blue]    │
├─────────────────────────────────────────────────────────────────┤
│ Search [lily___] Type[All Types▼] Status[All▼] ⚡Quick Actions  │
│                                                 [✓Test Selected]│
│                                                 [↔Compare Prompts]│
│                                                 [⚡Optimize Perf]│
├─────────────────────────────────────────────────────────────────┤
│ 7 prompts found                              📊 Test Workspace │
│ [Cards display same as Prompts Management]   Sample Email Content│
│                                              [Large textarea]   │
│                                              Project Context     │
│                                              [Select project ▼] │
│                                              [▷Test Active Prompt]│
│                                              📈 Performance Insights│
│                                              Avg Response Time   │
│                                              Success Rate        │
└─────────────────────────────────────────────────────────────────┘
```

### **Key Design Elements:**
- **Advanced filtering**: Search, type, and status filters
- **Quick Actions panel**: Colored action buttons with icons
- **Test Workspace**: Right sidebar with testing interface
- **Performance metrics**: Data visualization components
- **Same card design**: Maintains consistency with main prompts page

---

## 🔧 **Component Design Standards**

### **Buttons**
```css
/* Primary Actions */
.btn-primary {
  background: #007bff;
  border: 2px solid #0056b3;
  font-weight: 600;
  padding: 8px 16px;
  border-radius: 6px;
}

/* Secondary Actions */
.btn-outline-secondary {
  border: 1px solid #6c757d;
  color: #6c757d;
  background: transparent;
}

/* Action Buttons in Cards */
.btn-sm {
  padding: 4px 12px;
  font-size: 0.875rem;
}
```

### **Cards**
```css
.card {
  background: white;
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 1rem;
  margin-bottom: 1rem;
}

.card-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
}
```

### **Typography**
```css
/* Page Headers */
h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: #212529;
}

/* Card Titles */
h6.card-title {
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
}

/* Body Text */
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
  font-size: 0.875rem;
  line-height: 1.5;
}
```

### **Form Elements**
```css
.form-control {
  border: 1px solid #ced4da;
  border-radius: 6px;
  padding: 8px 12px;
  font-size: 0.875rem;
}

.form-label {
  font-weight: 500;
  margin-bottom: 4px;
  color: #495057;
}
```

---

## 🚨 **Pages Needing Design Updates**

### **CRITICAL - Immediate Attention Needed**

#### **1. Edit Prompt Page (`/prompts/X/edit`)**
**Current Issues:**
- ❌ Basic form layout instead of two-column design
- ❌ Missing guidance panel with placeholders
- ❌ Inconsistent button styling
- ❌ Plain form appearance vs. professional card design

**Required Changes:**
- ✅ Match Add Prompt two-column layout exactly
- ✅ Add Prompt Guidelines panel on right
- ✅ Use consistent card styling and shadows
- ✅ Implement proper form hierarchy

#### **2. View Prompt Page (`/prompts/X/view`)**
**Current Issues:**
- ❌ Plain list layout instead of card-based design
- ❌ Missing visual hierarchy
- ❌ No consistent spacing or typography
- ❌ Lacks professional appearance

**Required Changes:**
- ✅ Professional card-based layout
- ✅ Clear information hierarchy (Name → Details → Content)
- ✅ Consistent with other pages' visual style
- ✅ Proper action buttons (Edit, Test, Back)

### **MODERATE - Future Improvements**

#### **3. Test Prompt Page (`/prompts/X/test`)**
**Current State:** Partially good
**Improvements Needed:**
- ✅ Better result display formatting
- ✅ Enhanced error state styling
- ✅ Consistent with overall design system

#### **4. Dashboard Pages**
**Current State:** Unknown
**Assessment Needed:**
- 🔍 Review dashboard design consistency
- 🔍 Ensure card-based layouts
- 🔍 Verify color scheme alignment

---

## 📐 **Implementation Guidelines**

### **For Developers:**

1. **Always use Bootstrap 5 classes** for consistency
2. **Follow the card pattern**: `.card > .card-body > content`
3. **Maintain color scheme**: Primary blue (#007bff), consistent greys
4. **Use consistent spacing**: `mb-3`, `p-4`, `g-3` for gaps
5. **Implement responsive breakpoints**: `col-md-6`, `col-xl-4`

### **Template Structure Pattern:**
```html
{% extends "base.html" %}
{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="max-w-6xl mx-auto">
        <div class="bg-white rounded-lg shadow-md p-6">
            <!-- Header with title and actions -->
            <div class="flex justify-between items-center mb-6">
                <h1>Page Title</h1>
                <button class="btn btn-primary">Primary Action</button>
            </div>
            
            <!-- Two-column layout for forms -->
            <div class="row">
                <div class="col-md-8">
                    <!-- Main content -->
                </div>
                <div class="col-md-4">
                    <!-- Sidebar/guidance -->
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

---

## 🎯 **Next Steps - Priority Order**

1. **Fix Edit Prompt page** - Match Add Prompt design exactly
2. **Fix View Prompt page** - Professional card-based layout  
3. **Resolve Prompt Manager display issue** - Make cards appear
4. **Audit remaining pages** - Ensure design consistency
5. **Implement Quick Actions** - Functional buttons in Manager

---

**Design Goal:** *Every page should feel like part of the same professional, cohesive application with consistent visual language and user experience patterns.*