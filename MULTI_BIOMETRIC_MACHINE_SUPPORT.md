# Multi-Biometric Machine Support

## Overview

The HRM system now supports multiple biometric machines, allowing you to connect and sync attendance from various brands and types of biometric devices. The system uses a flexible driver-based architecture that makes it easy to add support for new machines.

## Supported Machine Types

### Currently Implemented

1. **ZKTeco Machines** (ZKT K70, ZKT K40, etc.)
   - Protocol: TCP/IP
   - Connection: IP Address + Port (default: 4370)
   - Uses ZKT SDK or pyzk library

2. **Generic API/Webhook Machines**
   - Protocol: HTTP/HTTPS
   - Connection: Full URL
   - Supports API key authentication
   - Configurable endpoints

### Placeholder Drivers (Ready for Implementation)

3. **RealTime** - Driver structure ready
4. **BioStar** - Driver structure ready
5. **Hikvision** - Can use Generic API driver
6. **Dahua** - Can use Generic API driver
7. **Attendance Pro** - Can use Generic API driver
8. **Custom/Other** - Can use Generic API driver

## Features

### 1. Multiple Machine Support
- Add unlimited biometric machines
- Each machine can be configured independently
- Support for different connection protocols (TCP/IP, HTTP, HTTPS, WebSocket, Serial, USB)

### 2. Flexible Configuration
- Machine type/brand selection
- Protocol selection (TCP/IP, HTTP, HTTPS, WebSocket, Serial, USB)
- Network configuration (IP, Port, URL)
- Serial/USB configuration (COM port, baud rate)
- Authentication (Username/Password, API Key)
- Custom JSON configuration for machine-specific settings

### 3. Unified Attendance Tracking
- All attendance records (manual and machine) stored in one place
- Attendance logs reference the specific machine that recorded them
- Support for multiple attendance sources:
  - Manual Entry
  - Biometric Machine
  - API/Webhook
  - Mobile App
  - Web Interface

### 4. Easy Machine Management
- Add, edit, and delete machines through admin interface
- Test connection to machines
- Sync attendance from specific machines or all machines
- View sync status and error messages
- Configure sync intervals

## How to Add a New Machine

### Step 1: Access Machine Management

1. Log in as admin
2. Navigate to "Manage Attendance Machines" (or go to `/manage-attendance-machines/`)

### Step 2: Add Machine Configuration

Click "Add Machine" and fill in the form:

#### Basic Information
- **Name**: Give your machine a descriptive name (e.g., "Main Entrance ZKT K70")
- **Machine Type**: Select the brand/type of your machine
- **Protocol**: Select how the machine connects
- **Location**: Physical location of the machine
- **Description**: Optional notes about the machine
- **Active**: Check to enable automatic syncing

#### Network Configuration (for TCP/IP, HTTP, HTTPS, WebSocket)
- **IP Address**: Machine's IP address (for TCP/IP)
- **Port**: Connection port (default: 4370 for ZKT)
- **URL**: Full URL for HTTP/HTTPS/API connections (e.g., `https://api.example.com`)

#### Serial/USB Configuration (for Serial protocol)
- **Serial Port**: COM port (Windows: COM1, Linux: /dev/ttyUSB0)
- **Baud Rate**: Serial communication speed (default: 9600)

#### Authentication
- **Username**: If machine requires authentication
- **Password**: Machine password
- **API Key**: For API-based machines

#### Advanced Configuration
- **Sync Interval**: How often to sync in minutes (default: 15)
- **Configuration**: JSON field for machine-specific settings

### Step 3: Test Connection

After adding the machine, click "Test Connection" to verify:
- The machine is reachable
- Authentication credentials are correct
- The connection protocol is working

### Step 4: Configure Employee Machine IDs

1. Go to "Manage Employee Machine IDs"
2. For each employee, set their machine ID as registered in the biometric device
3. You can set:
   - **Machine ID**: Primary user ID in the machine
   - **Fingerprint ID**: If using fingerprint authentication
   - **Face ID**: If using face recognition
   - **Card ID**: If using card/RFID authentication

The system will try to match attendance records using any of these IDs.

## Syncing Attendance

### Sync from Specific Machine

1. Go to "All Attendance" page
2. Click "Sync Machine" next to the machine you want to sync
3. Optionally select date range
4. Click "Sync"

### Sync from All Machines

1. Go to "All Attendance" page
2. Click "Sync All Machines"
3. Optionally select date range
4. Click "Sync"

The system will:
- Connect to each active machine
- Fetch attendance records
- Match employees by machine ID
- Create attendance logs
- Process logs into daily attendance records

## Adding Support for New Machine Types

To add support for a new biometric machine brand:

### Step 1: Create Driver Class

Create a new driver class in `core/machine_drivers.py`:

```python
class NewBrandDriver(MachineDriver):
    """Driver for NewBrand biometric machines"""
    
    def connect(self) -> bool:
        # Implement connection logic
        pass
    
    def disconnect(self) -> bool:
        # Implement disconnection logic
        pass
    
    def is_connected(self) -> bool:
        # Check connection status
        pass
    
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        # Fetch attendance data from machine
        # Return list of dicts with: user_id, timestamp, status, raw_data
        pass
    
    def get_users(self) -> List[Dict]:
        # Fetch users from machine
        # Return list of dicts with: user_id, name, privilege, raw_data
        pass
    
    def test_connection(self) -> Dict[str, Any]:
        # Test connection and return success/error message
        pass
```

### Step 2: Add Machine Type to Model

1. Add new choice to `MACHINE_TYPE_CHOICES` in `AttendanceMachine` model
2. Add constant for the new type (e.g., `MACHINE_TYPE_NEWBRAND = 'newbrand'`)

### Step 3: Register Driver in Factory

Update `get_machine_driver()` function to return your new driver:

```python
elif machine_type == AttendanceMachine.MACHINE_TYPE_NEWBRAND:
    return NewBrandDriver(machine)
```

## API/Webhook Integration

For machines that support API/webhook integration:

### Configuration

1. Set **Machine Type** to "Generic API/Webhook"
2. Set **Protocol** to "HTTP" or "HTTPS"
3. Enter the **URL** (e.g., `https://api.example.com`)
4. Set **API Key** if required
5. In **Configuration** JSON field, set:
   ```json
   {
     "attendance_endpoint": "api/attendance",
     "users_endpoint": "api/users",
     "test_endpoint": "api/health",
     "auth_type": "header",
     "api_key_header": "X-API-Key"
   }
   ```

### API Response Format

The system expects attendance data in this format:

```json
{
  "data": [
    {
      "user_id": "123",
      "timestamp": "2025-12-31T09:00:00Z",
      "status": "check_in"
    }
  ]
}
```

Or:

```json
{
  "attendance": [
    {
      "user_id": "123",
      "timestamp": "2025-12-31T09:00:00Z",
      "status": "check_in"
    }
  ]
}
```

## Troubleshooting

### Machine Connection Fails

1. **Check Network Connectivity**
   - Ping the machine's IP address
   - Verify port is open and not blocked by firewall

2. **Verify Configuration**
   - Check IP address, port, and protocol are correct
   - Verify authentication credentials

3. **Check Machine Status**
   - Ensure machine is powered on
   - Check machine's network settings

4. **Review Error Messages**
   - Check "Last Error" field in machine configuration
   - Review Django logs for detailed error messages

### Attendance Not Syncing

1. **Check Employee Machine IDs**
   - Verify employee machine IDs match those in the device
   - Check if using fingerprint_id, face_id, or card_id

2. **Check Sync Status**
   - Verify machine is marked as "Active"
   - Check "Last Sync" timestamp
   - Review sync interval settings

3. **Check Date Range**
   - Ensure date range includes recent attendance records
   - Some machines only store limited history

### Adding Custom Machine Support

If your machine type is not listed:

1. **Try Generic API Driver**
   - If machine has HTTP/HTTPS API
   - Configure as "Generic API/Webhook"

2. **Create Custom Driver**
   - Follow the driver creation guide above
   - Implement connection and data fetching logic
   - Test thoroughly before deploying

## Best Practices

1. **Regular Syncing**: Set appropriate sync intervals based on your needs
2. **Backup Configuration**: Keep records of machine configurations
3. **Monitor Sync Status**: Regularly check "Last Sync" timestamps
4. **Test After Changes**: Always test connection after changing machine settings
5. **Employee ID Management**: Keep employee machine IDs synchronized with devices
6. **Error Monitoring**: Review error messages regularly to catch issues early

## Migration Notes

After running the migration (`0038_add_multi_biometric_machine_support`):

1. Existing ZKT machines will be preserved
2. Machine type will default to "ZKTeco"
3. Protocol will default to "TCP/IP"
4. Existing attendance logs will remain intact
5. You may need to update machine configurations to use new fields

## Support

For issues or questions:
1. Check error messages in machine configuration
2. Review Django logs
3. Test connection using "Test Connection" button
4. Verify employee machine IDs are correctly set

