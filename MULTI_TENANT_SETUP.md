# Multi-Tenant Company System Setup Guide

## Overview
This HRM system now supports multi-tenant architecture where multiple companies can use the same system with complete data isolation and customizable feature access.

## Key Features

1. **Company Isolation**: Each company's data is completely isolated from others
2. **Feature Access Control**: Super Admin can enable/disable features per company
3. **Company Admin Role**: Each company can have a Company Admin who manages their company
4. **Super Admin Panel**: Django Admin interface for managing companies and features

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. Initialize Companies and Features
```bash
python manage.py init_companies_and_features
```

This command will:
- Create all HRM features (employees, attendance, projects, etc.)
- Create a default company for existing data
- Assign all existing data to the default company
- Create user profiles for existing users

### 3. Access Django Admin
1. Go to `/admin/`
2. Login as Super Admin
3. Navigate to **Companies** section

### 4. Create New Companies
1. Click "Add Company"
2. Fill in:
   - **Name**: Company name
   - **Slug**: URL-friendly identifier (auto-generated)
   - **Description**: Optional description
   - **Is Active**: Check to activate
   - **Admin**: Select a user to be Company Admin
   - **Features**: Select which features this company can access

### 5. Assign Users to Companies
1. Go to **Users** section in Django Admin
2. Edit a user
3. In the "Company Profile" section:
   - Select the **Company**
   - Check **Is Company Admin** if this user should be Company Admin

### 6. Assign Features to Companies
1. Go to **Companies** section
2. Edit a company
3. In the "Features" section, select which features this company can access
4. Save

## Feature Codes

Available feature codes for assignment:
- `employees` - Employees Management
- `attendance` - Attendance Management
- `leaves` - Leave Management
- `holidays` - Holiday Management
- `payroll` - Payroll Management
- `loans` - Loan Management
- `advances` - Advance Requests
- `projects` - Project Management
- `tasks` - Task Management
- `tickets` - Ticket Management
- `clients` - Client Management
- `budgets` - Budget Management
- `expenses` - Expense Management
- `revenues` - Revenue Management
- `assets` - Asset Management
- `invoices` - Invoice Management
- `estimates` - Estimate Management
- `reports` - Reports & Analytics
- `chat` - Chat & Messaging
- `notifications` - Notifications
- `settings` - Settings
- `marzi` - Marzi Features (custom)

## Usage in Views

### Require Feature Access
```python
from core.company_utils import require_feature

@login_required
@require_feature('employees')
def employee_list(request):
    # View code here
    pass
```

### Filter by Company
```python
from core.company_utils import filter_by_company, get_user_company

def my_view(request):
    user_company = get_user_company(request.user)
    employees = Employee.objects.filter(company=user_company)
    # Or use the helper
    employees = filter_by_company(Employee.objects.all(), request.user)
```

### Check Feature Access
```python
from core.company_utils import has_feature_access

if has_feature_access(request.user, 'employees'):
    # Show employees feature
    pass
```

## Usage in Templates

### Check Feature Access
```django
{% load core_extras %}

{% has_feature 'employees' as can_access_employees %}
{% if can_access_employees %}
    <a href="{% url 'employee_list' %}">Employees</a>
{% endif %}
```

### Check User Roles
```django
{% is_super_admin_user as is_super_admin %}
{% is_company_admin_user as is_company_admin %}

{% if is_super_admin %}
    <!-- Super Admin content -->
{% elif is_company_admin %}
    <!-- Company Admin content -->
{% endif %}
```

## Data Isolation

All data is automatically filtered by company:
- Employees belong to a company
- Departments belong to a company
- Projects belong to a company
- Clients belong to a company
- And more...

Super Admins see all data, Company Admins and Employees see only their company's data.

## Security

- Feature access is enforced at both backend (decorators) and frontend (template tags)
- Company isolation is enforced via middleware and view filters
- Super Admins have access to everything
- Company Admins can only manage their own company
- Regular employees can only see their own data (unless Company Admin)

## Next Steps

1. Create additional companies in Django Admin
2. Assign features to each company
3. Assign Company Admins
4. Assign users to their respective companies
5. Test feature access and data isolation

## Notes

- Existing data is assigned to "Default Company"
- All features are enabled for the default company
- You can create new companies and assign different feature sets
- Company Admins can manage employees but not change company settings
- Only Super Admins can manage companies and features

