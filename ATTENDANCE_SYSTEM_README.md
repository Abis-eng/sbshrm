# ZKT K70 Attendance System Integration

This document explains the new attendance system that integrates with your ZKT K70 machine and allows both manual and machine-based attendance tracking.

## Overview

The new attendance system provides:
- **Dual Attendance Tracking**: Employees can mark attendance through the ZKT machine or the HRM system
- **Automatic Data Sync**: Attendance data from the ZKT machine is automatically synced to the HRM system
- **Comprehensive Logging**: All attendance events are logged with source tracking (manual/machine)
- **Advanced Features**: Break tracking, late arrival detection, work hours calculation

## System Architecture

### Models

1. **Employee** (Enhanced)
   - Added machine ID fields for ZKT integration
   - `machine_id`: Employee ID in ZKT machine
   - `fingerprint_id`: Fingerprint ID in ZKT machine
   - `face_id`: Face ID in ZKT machine
   - `card_id`: Card ID in ZKT machine

2. **AttendanceMachine**
   - Manages ZKT machine configurations
   - Stores IP address, port, location
   - Tracks last sync time

3. **AttendanceLog**
   - Raw attendance events from all sources
   - Tracks attendance type (check-in, check-out, break)
   - Records source (manual, machine, API)
   - Stores machine-specific data

4. **Attendance** (Enhanced)
   - Daily attendance summaries
   - Calculated work hours and break hours
   - Late arrival detection
   - Status tracking (present, late, absent, etc.)

### ZKT Service

The `core/zkt_service.py` module handles:
- Connection to ZKT machine
- Data synchronization
- Attendance log processing
- Machine status monitoring

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The system requires the `pyzk` package for ZKT machine communication.

### 2. Configure ZKT Machine

1. **Access the Admin Panel**:
   - Go to `http://your-domain/admin/`
   - Navigate to "Attendance Machines"
   - Add your ZKT K70 machine with:
     - IP Address: `192.168.18.1`
     - Port: `4370`
     - Location: `Main Office`

2. **Test Connection**:
   - Use the "Test Connection" button to verify connectivity
   - Ensure the machine is powered on and connected to the network

### 3. Configure Employee Machine IDs

1. **Access Employee Management**:
   - Go to "Manage Employee Machine IDs"
   - For each employee, set their machine ID as registered in the ZKT device
   - You can also set fingerprint, face, and card IDs if applicable

### 4. Run Database Migrations

```bash
python manage.py migrate
```

## Usage Guide

### For Employees

#### Manual Attendance Entry
1. Go to "My Attendance" page
2. Select the appropriate action (Check In, Check Out, Break Start, Break End)
3. Click "Record Attendance"

#### Machine-Based Attendance
1. Use the ZKT machine as usual
2. Data will be automatically synced to the HRM system
3. View your attendance records in "My Attendance"

### For Administrators

#### View All Attendance
1. Go to "All Attendance" page
2. Use filters to view specific employees, dates, or statuses
3. View detailed attendance logs

#### Sync ZKT Data
1. Go to "All Attendance" page
2. Click "Sync ZKT Machine" button
3. The system will fetch and process attendance data from the machine

#### Manual Attendance Entry
1. Go to "Manual Attendance Entry"
2. Select employee, attendance type, and timestamp
3. Add optional notes
4. Save the entry

#### View Attendance Logs
1. Go to "Attendance Logs" page
2. View raw attendance events from all sources
3. Filter by employee, date range, or source

#### Manage Machines
1. Go to "Manage Attendance Machines"
2. Add, edit, or remove ZKT machines
3. Test connections and monitor sync status

## API Endpoints

### Manual Attendance Entry
```
POST /manual-attendance-entry/
```

### Sync ZKT Machine
```
POST /sync-zkt-machine/
```

### Test ZKT Connection
```
GET /test-zkt-connection/
```

## Management Commands

### Sync Attendance Data
```bash
python manage.py sync_zkt_attendance --days 7
python manage.py sync_zkt_attendance --start-date 2024-01-01 --end-date 2024-01-31
```

## Configuration

### ZKT Machine Settings
- **Default IP**: 192.168.18.1
- **Default Port**: 4370
- **Timeout**: 5 seconds
- **SDK Path**: C:\Users\SBS\Desktop\sdk

### Attendance Rules
- **Work Start Time**: 9:00 AM (configurable)
- **Late Threshold**: Any check-in after 9:00 AM
- **Break Tracking**: Supports break start/end events
- **Hours Calculation**: Automatic calculation of work and break hours

## Troubleshooting

### Connection Issues
1. **Check Network Connectivity**:
   - Ensure the ZKT machine is on the same network
   - Verify IP address and port settings
   - Check firewall settings

2. **SDK Issues**:
   - Verify ZKT SDK is installed at `C:\Users\SBS\Desktop\sdk`
   - Check SDK compatibility with your machine model

3. **Machine Not Responding**:
   - Restart the ZKT machine
   - Check power and network connections
   - Verify machine is not in sleep mode

### Data Sync Issues
1. **No Data Synced**:
   - Check if employees have machine IDs configured
   - Verify date range for sync
   - Check machine connection status

2. **Duplicate Records**:
   - The system automatically prevents duplicate logs
   - Check for manual entries that conflict with machine data

### Performance Issues
1. **Slow Sync**:
   - Reduce sync date range
   - Check network bandwidth
   - Monitor machine response time

## Security Considerations

1. **Network Security**:
   - Use VPN for remote access
   - Implement network segmentation
   - Regular security updates

2. **Data Privacy**:
   - Encrypt sensitive attendance data
   - Implement access controls
   - Regular backup procedures

3. **Machine Security**:
   - Change default passwords
   - Regular firmware updates
   - Physical security measures

## Support

For technical support:
1. Check the troubleshooting section above
2. Review Django logs for error messages
3. Verify ZKT machine documentation
4. Contact system administrator

## Future Enhancements

Potential improvements:
- Real-time attendance monitoring
- Mobile app integration
- Advanced reporting and analytics
- Multi-location support
- Integration with payroll systems
