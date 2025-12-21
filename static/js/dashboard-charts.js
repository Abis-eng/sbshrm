// Dashboard Charts - Separate file to keep code clean
(function() {
    'use strict';
    
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded');
        return;
    }
    
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { position: 'bottom', labels: { padding: 20, usePointStyle: true, font: { size: 12, weight: '600' } } },
            tooltip: { backgroundColor: 'rgba(0, 0, 0, 0.8)', padding: 12, titleFont: { size: 14, weight: '600' }, bodyFont: { size: 13 }, borderColor: 'rgba(255, 255, 255, 0.1)', borderWidth: 1, cornerRadius: 8 }
        },
        scales: {
            y: { beginAtZero: true, grid: { color: 'rgba(0, 0, 0, 0.05)' }, ticks: { font: { size: 11 } } },
            x: { grid: { display: false }, ticks: { font: { size: 11 } } }
        }
    };
    
    let chartInstances = {};
    
    function initAttendanceChart() {
        const canvas = document.getElementById('attendanceChart');
        if (!canvas) return;
        if (chartInstances['attendanceChart']) {
            chartInstances['attendanceChart'].destroy();
        }
        
        const dataEl = document.getElementById('attendance-stats-data');
        if (!dataEl) return;
        
        const aData = JSON.parse(dataEl.textContent);
        const labels = aData.map(s => s.status.charAt(0).toUpperCase() + s.status.slice(1).replace('_', ' '));
        const counts = aData.map(s => s.count);
        
        chartInstances['attendanceChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Attendance Count',
                    data: counts,
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(139, 92, 246, 0.8)'
                    ],
                    borderColor: [
                        '#10b981',
                        '#ef4444',
                        '#f59e0b',
                        '#3b82f6',
                        '#8b5cf6'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: chartOptions
        });
    }
    
    function initDepartmentChart() {
        const canvas = document.getElementById('deptChart');
        if (!canvas) return;
        if (chartInstances['deptChart']) {
            chartInstances['deptChart'].destroy();
        }
        
        const dataEl = document.getElementById('dept-counts-data');
        if (!dataEl) return;
        
        const dData = JSON.parse(dataEl.textContent);
        chartInstances['deptChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: dData.map(d => d.name),
                datasets: [{
                    label: 'Employees',
                    data: dData.map(d => d.emp_count),
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: chartOptions
        });
    }
    
    function initRevenueExpenseChart() {
        const canvas = document.getElementById('revenueExpenseChart');
        if (!canvas) return;
        if (chartInstances['revenueExpenseChart']) {
            chartInstances['revenueExpenseChart'].destroy();
        }
        
        const expDataEl = document.getElementById('expense-stats-data');
        const revDataEl = document.getElementById('revenue-stats-data');
        if (!expDataEl || !revDataEl) return;
        
        const expData = JSON.parse(expDataEl.textContent);
        const revData = JSON.parse(revDataEl.textContent);
        const months = [...new Set([...expData.map(e => e.month), ...revData.map(r => r.month)])].sort();
        const monthLabels = months.map(m => m ? new Date(m).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '');
        const revValues = months.map(m => { const s = revData.find(r => r.month === m); return s ? parseFloat(s.total) : 0; });
        const expValues = months.map(m => { const s = expData.find(e => e.month === m); return s ? parseFloat(s.total) : 0; });
        
        chartInstances['revenueExpenseChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [
                    {
                        label: 'Revenue',
                        data: revValues,
                        backgroundColor: 'rgba(16, 185, 129, 0.8)',
                        borderColor: '#10b981',
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false
                    },
                    {
                        label: 'Expenses',
                        data: expValues,
                        backgroundColor: 'rgba(239, 68, 68, 0.8)',
                        borderColor: '#ef4444',
                        borderWidth: 2,
                        borderRadius: 8,
                        borderSkipped: false
                    }
                ]
            },
            options: {
                ...chartOptions,
                scales: {
                    ...chartOptions.scales,
                    x: {
                        ...chartOptions.scales.x,
                        stacked: false
                    },
                    y: {
                        ...chartOptions.scales.y,
                        stacked: false
                    }
                }
            }
        });
    }
    
    function initDesignationChart() {
        const canvas = document.getElementById('designationChart');
        if (!canvas) return;
        if (chartInstances['designationChart']) {
            chartInstances['designationChart'].destroy();
        }
        
        const dataEl = document.getElementById('designation-counts-data');
        if (!dataEl) return;
        
        const dData = JSON.parse(dataEl.textContent);
        chartInstances['designationChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: dData.map(d => d.name),
                datasets: [{
                    label: 'Employees',
                    data: dData.map(d => d.emp_count),
                    backgroundColor: 'rgba(139, 92, 246, 0.8)',
                    borderColor: '#8b5cf6',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: chartOptions
        });
    }
    
    function initExpenseChart() {
        const canvas = document.getElementById('expenseChart');
        if (!canvas) return;
        if (chartInstances['expenseChart']) {
            chartInstances['expenseChart'].destroy();
        }
        
        const dataEl = document.getElementById('expense-stats-data');
        if (!dataEl) return;
        
        const expData = JSON.parse(dataEl.textContent);
        const months = expData.map(e => e.month).sort();
        const monthLabels = months.map(m => m ? new Date(m).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '');
        const amounts = months.map(m => { const s = expData.find(e => e.month === m); return s ? parseFloat(s.total) : 0; });
        
        chartInstances['expenseChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: 'Expenses',
                    data: amounts,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    borderColor: '#ef4444',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: chartOptions
        });
    }
    
    function initRevenueChart() {
        const canvas = document.getElementById('revenueChart');
        if (!canvas) return;
        if (chartInstances['revenueChart']) {
            chartInstances['revenueChart'].destroy();
        }
        
        const dataEl = document.getElementById('revenue-stats-data');
        if (!dataEl) return;
        
        const revData = JSON.parse(dataEl.textContent);
        const months = revData.map(r => r.month).sort();
        const monthLabels = months.map(m => m ? new Date(m).toLocaleDateString('en-US', { month: 'short', year: 'numeric' }) : '');
        const amounts = months.map(m => { const s = revData.find(r => r.month === m); return s ? parseFloat(s.total) : 0; });
        
        chartInstances['revenueChart'] = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: monthLabels,
                datasets: [{
                    label: 'Revenue',
                    data: amounts,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    borderColor: '#10b981',
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: chartOptions
        });
    }
    
    function initTaskChart() {
        const canvas = document.getElementById('taskChart');
        if (!canvas) return;
        if (chartInstances['taskChart']) {
            chartInstances['taskChart'].destroy();
        }
        
        const activeTasks = parseInt(canvas.dataset.active || 0);
        const completedTasks = parseInt(canvas.dataset.completed || 0);
        
        chartInstances['taskChart'] = new Chart(canvas.getContext('2d'), {
            type: 'pie',
            data: {
                labels: ['Active Tasks', 'Completed Tasks'],
                datasets: [{
                    data: [activeTasks, completedTasks],
                    backgroundColor: ['rgba(245, 158, 11, 0.9)', 'rgba(16, 185, 129, 0.9)'],
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { ...chartOptions.plugins.legend, position: 'bottom' } } }
        });
    }
    
    function showChartModal(chartType) {
        const modal = document.getElementById('chartModal');
        if (!modal) return;
        
        const modalTitle = modal.querySelector('.modal-title');
        const chartContainer = modal.querySelector('#modalChartContainer');
        
        // Hide all canvases first
        const canvases = chartContainer.querySelectorAll('canvas');
        canvases.forEach(canvas => {
            canvas.style.display = 'none';
            // Destroy existing chart if any
            const chartId = canvas.id;
            if (chartInstances[chartId]) {
                chartInstances[chartId].destroy();
                delete chartInstances[chartId];
            }
        });
        
        // Set title based on chart type
        const titles = {
            'attendance': 'Attendance Overview',
            'department': 'Department Distribution',
            'designation': 'Designation Distribution',
            'revenue': 'Revenue vs Expenses',
            'expense': 'Monthly Expenses',
            'revenue-only': 'Monthly Revenue',
            'task': 'Task Status'
        };
        
        if (modalTitle) modalTitle.textContent = titles[chartType] || 'Chart';
        
        // Show the appropriate canvas
        let targetCanvas = null;
        switch(chartType) {
            case 'attendance':
                targetCanvas = document.getElementById('attendanceChart');
                break;
            case 'department':
                targetCanvas = document.getElementById('deptChart');
                break;
            case 'designation':
                targetCanvas = document.getElementById('designationChart');
                break;
            case 'revenue':
                targetCanvas = document.getElementById('revenueExpenseChart');
                break;
            case 'expense':
                targetCanvas = document.getElementById('expenseChart');
                break;
            case 'revenue-only':
                targetCanvas = document.getElementById('revenueChart');
                break;
            case 'task':
                targetCanvas = document.getElementById('taskChart');
                break;
        }
        
        if (targetCanvas) {
            targetCanvas.style.display = 'block';
        }
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        // Initialize chart after modal is shown
        modal.addEventListener('shown.bs.modal', function initChart() {
            setTimeout(() => {
                switch(chartType) {
                    case 'attendance':
                        initAttendanceChart();
                        break;
                    case 'department':
                        initDepartmentChart();
                        break;
                    case 'designation':
                        initDesignationChart();
                        break;
                    case 'revenue':
                        initRevenueExpenseChart();
                        break;
                    case 'expense':
                        initExpenseChart();
                        break;
                    case 'revenue-only':
                        initRevenueChart();
                        break;
                    case 'task':
                        initTaskChart();
                        break;
                }
            }, 100);
            modal.removeEventListener('shown.bs.modal', initChart);
        }, { once: true });
    }
    
    // Initialize all charts when DOM is ready
    function initializeAllCharts() {
        initAttendanceChart();
        initDepartmentChart();
        initDesignationChart();
        initRevenueExpenseChart();
        initExpenseChart();
        initRevenueChart();
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAllCharts);
    } else {
        initializeAllCharts();
    }
    
    // Export for global use
    window.dashboardCharts = {
        showChart: showChartModal,
        initAttendance: initAttendanceChart,
        initDepartment: initDepartmentChart,
        initDesignation: initDesignationChart,
        initRevenueExpense: initRevenueExpenseChart,
        initExpense: initExpenseChart,
        initRevenue: initRevenueChart,
        initTask: initTaskChart
    };
})();

