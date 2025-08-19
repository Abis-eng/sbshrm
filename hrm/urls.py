"""
URL configuration for hrm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.urls import include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),  # admin only
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),  # employee only
    path('employees/', views.employee_list, name='employee_list'),  # admin only
    path('add-employee/', views.add_employee, name='add_employee'),  # admin only
    path('edit-employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),  # admin
    path('delete-employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),  # admin
    path('logout/', views.logout_view, name='logout'),
    path('users/', views.user_list, name='user_list'),  # admin only
    path('chat-users/', views.chat_user_list, name='chat_user_list'),  # chat sidebar
    path('my-tickets/', views.my_tickets, name='my_tickets'),  # employee
    path('submit-ticket/', views.submit_ticket, name='submit_ticket'),  # employee
    path('all-tickets/', views.all_tickets, name='all_tickets'),  # admin
    path('update-ticket/<int:ticket_id>/', views.update_ticket_status, name='update_ticket'),  # admin
    path('my-attendance/', views.my_attendance, name='my_attendance'),  # employee
    path('all-attendance/', views.all_attendance, name='all_attendance'),  # admin
    path('attendance-logs/', views.attendance_logs, name='attendance_logs'),  # admin
    path('sync-zkt-machine/', views.sync_zkt_machine, name='sync_zkt_machine'),  # admin
    path('manage-attendance-machines/', views.manage_attendance_machines, name='manage_attendance_machines'),  # admin
    path('edit-attendance-machine/<int:machine_id>/', views.edit_attendance_machine, name='edit_attendance_machine'),  # admin
    path('delete-attendance-machine/<int:machine_id>/', views.delete_attendance_machine, name='delete_attendance_machine'),  # admin
    path('manage-employee-machine-ids/', views.manage_employee_machine_ids, name='manage_employee_machine_ids'),  # admin
    path('manual-attendance-entry/', views.manual_attendance_entry, name='manual_attendance_entry'),  # admin
    path('test-zkt-connection/', views.test_zkt_connection, name='test_zkt_connection'),  # admin
    path('departments/', views.manage_departments, name='manage_departments'),  # admin
    path('my-department/', views.my_department, name='my_department'),  # employee
    path('designations/', views.manage_designations, name='manage_designations'),  # admin
    path('my-designation/', views.my_designation, name='my_designation'),  # employee
    path('manage-holidays/', views.manage_holidays, name='manage_holidays'),  # admin
    path('delete-holiday/<int:holiday_id>/', views.delete_holiday, name='delete_holiday'),  # admin
    path('holidays/', views.holidays, name='holidays'),  # employee
    path('apply-leave/', views.apply_leave, name='apply_leave'),  # employee
    path('my-leaves/', views.my_leaves, name='my_leaves'),  # employee
    path('manage-leaves/', views.manage_leaves, name='manage_leaves'),  # admin
    path('delete-department/<int:department_id>/', views.delete_department, name='delete_department'),  # admin
    path('delete-designation/<int:designation_id>/', views.delete_designation, name='delete_designation'),  # admin
    path('delete-ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('clients/', views.client_list, name='client_list'),
    path('add-client/', views.add_client, name='add_client'),
    path('edit-client/<int:client_id>/', views.edit_client, name='edit_client'),
    path('delete-client/<int:client_id>/', views.delete_client, name='delete_client'),
    path('projects/', views.project_list, name='project_list'),
    path('add-project/', views.add_project, name='add_project'),
    path('edit-project/<int:project_id>/', views.edit_project, name='edit_project'),
    path('delete-project/<int:project_id>/', views.delete_project, name='delete_project'),
    path('core/', include('core.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
