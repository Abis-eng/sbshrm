#!/usr/bin/env python3
"""
Script to update color theme across all template files
Replaces old purple/pink gradients with new professional teal/indigo/emerald theme
"""

import os
import re
from pathlib import Path

# Color replacements
REPLACEMENTS = {
    # Primary purple -> Teal
    '#667eea': '#0e7490',
    '#764ba2': '#0891b2',
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)': 'linear-gradient(135deg, #0e7490 0%, #0891b2 100%)',
    'rgba(102, 126, 234, 0.3)': 'rgba(14, 116, 144, 0.3)',
    'rgba(102, 126, 234, 0.2)': 'rgba(14, 116, 144, 0.2)',
    'rgba(102, 126, 234, 0.8)': 'rgba(14, 116, 144, 0.8)',
    
    # Pink -> Indigo
    '#f093fb': '#6366f1',
    '#f5576c': '#4f46e5',
    'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)': 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
    'rgba(245, 87, 108, 0.3)': 'rgba(79, 70, 229, 0.3)',
    'rgba(245, 87, 108, 0.2)': 'rgba(79, 70, 229, 0.2)',
    
    # Blue -> Sky Blue
    '#3b82f6': '#0ea5e9',
    '#1d4ed8': '#0284c7',
    '#2563eb': '#0284c7',
    'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)': 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)': 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
    'rgba(59, 130, 246, 0.3)': 'rgba(14, 165, 233, 0.3)',
    'rgba(59, 130, 246, 0.2)': 'rgba(14, 165, 233, 0.2)',
    'rgba(59, 130, 246, 0.25)': 'rgba(14, 165, 233, 0.25)',
    
    # Cyan -> Teal
    '#4facfe': '#0891b2',
    '#00f2fe': '#06b6d4',
    'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)': 'linear-gradient(135deg, #0891b2 0%, #06b6d4 100%)',
    
    # Light Green -> Emerald
    '#43e97b': '#10b981',
    '#38f9d7': '#059669',
    'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)': 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    
    # Yellow -> Amber (keep similar)
    '#fbbf24': '#f59e0b',
    '#f59e0b': '#d97706',
    'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)': 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    
    # Border colors
    'border-left: 4px solid #667eea': 'border-left: 4px solid #0e7490',
    'border-left: 4px solid #f5576c': 'border-left: 4px solid #6366f1',
    'border-left: 4px solid #3b82f6': 'border-left: 4px solid #0ea5e9',
    'border-color: #667eea': 'border-color: #0e7490',
    'border-color: #764ba2': 'border-color: #0891b2',
    'border-color: #f5576c': 'border-color: #6366f1',
    'border-color: #3b82f6': 'border-color: #0ea5e9',
    'border: 2px dashed #667eea': 'border: 2px dashed #0e7490',
    'border: 2px dashed #764ba2': 'border: 2px dashed #0891b2',
    
    # Text colors
    'color: #667eea': 'color: #0e7490',
    'color: #f5576c': 'color: #6366f1',
    'color: #3b82f6': 'color: #0ea5e9',
}

# Files to update
TEMPLATE_DIR = Path('templates/core')
FILES_TO_UPDATE = [
    'employee_list.html',
    'add_employee.html',
    'edit_employee.html',
    'view_employee_profile.html',
    'manage_departments.html',
    'manage_designations.html',
    'edit_department.html',
    'edit_designation.html',
    'department_employees.html',
    'designation_employees.html',
    'holidays.html',
    'manage_holidays.html',
    'edit_holiday.html',
    'my_leaves.html',
    'apply_leave.html',
    'manage_leaves.html',
    'my_department.html',
    'my_designation.html',
    'client_list.html',
    'add_client.html',
    'edit_client.html',
]

def update_file(filepath):
    """Update colors in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for old, new in REPLACEMENTS.items():
            content = content.replace(old, new)
        
        # Only write if changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error updating {filepath}: {e}")
        return False

if __name__ == '__main__':
    updated = 0
    for filename in FILES_TO_UPDATE:
        filepath = TEMPLATE_DIR / filename
        if filepath.exists():
            if update_file(filepath):
                print(f"Updated: {filename}")
                updated += 1
            else:
                print(f"No changes: {filename}")
        else:
            print(f"Not found: {filename}")
    
    print(f"\nTotal files updated: {updated}")

