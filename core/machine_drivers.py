"""
Generic machine driver interface and implementations for different biometric machines.
This allows easy integration of any biometric machine by creating a driver class.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from django.utils import timezone

logger = logging.getLogger(__name__)


class MachineDriver(ABC):
    """Base class for all biometric machine drivers"""
    
    def __init__(self, machine):
        """
        Initialize driver with machine configuration
        
        Args:
            machine: AttendanceMachine instance
        """
        self.machine = machine
        self.connected = False
        self.connection = None
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the machine. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the machine. Returns True if successful."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if currently connected to the machine."""
        pass
    
    @abstractmethod
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        """
        Get attendance data from the machine.
        
        Args:
            start_date: Start date for filtering (datetime or date)
            end_date: End date for filtering (datetime or date)
        
        Returns:
            List of attendance records, each containing:
            - user_id: User ID in the machine
            - timestamp: Attendance timestamp
            - status: Attendance status (check_in, check_out, etc.)
            - raw_data: Any additional raw data
        """
        pass
    
    @abstractmethod
    def get_users(self) -> List[Dict]:
        """
        Get list of users registered in the machine.
        
        Returns:
            List of user records, each containing:
            - user_id: User ID in the machine
            - name: User name
            - privilege: User privilege level
            - raw_data: Any additional raw data
        """
        pass
    
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to the machine.
        
        Returns:
            Dict with 'success' (bool) and 'message' (str)
        """
        pass
    
    def get_machine_info(self) -> Dict[str, Any]:
        """Get machine information"""
        return {
            'name': self.machine.name,
            'type': self.machine.get_machine_type_display(),
            'location': self.machine.location,
            'connection_string': self.machine.get_connection_string(),
        }


class ZKTDriver(MachineDriver):
    """Driver for ZKTeco machines (ZKT K70, ZKT K40, etc.)"""
    
    def __init__(self, machine):
        super().__init__(machine)
        self.zk = None
        self.connection_error = None
        
        # Try to import ZKT SDK
        import os
        import sys
        sdk_path = r"C:\Users\SBS\Desktop\sdk"
        if os.path.exists(sdk_path):
            sys.path.append(sdk_path)
        
        try:
            from zk import ZK
            self.ZK = ZK
        except ImportError:
            try:
                from pyzk import ZK
                self.ZK = ZK
            except ImportError:
                self.ZK = None
                logger.warning("ZKT SDK not available. Install zk or pyzk package.")
    
    def connect(self) -> bool:
        """Connect to ZKT machine"""
        if not self.ZK:
            error_msg = "ZKT SDK not available. Please install 'zk' or 'pyzk' package."
            logger.error(error_msg)
            self.connection_error = error_msg
            return False
        
        try:
            ip = self.machine.ip_address
            port = self.machine.port or 4370
            timeout = self.machine.configuration.get('timeout', 5)
            
            if not ip:
                error_msg = "IP address is not configured for this machine"
                logger.error(error_msg)
                self.connection_error = error_msg
                return False
            
            # Get connection options from configuration
            ommit_ping = self.machine.configuration.get('ommit_ping', True)  # Skip ping by default
            force_udp = self.machine.configuration.get('force_udp', False)
            password = self.machine.configuration.get('password', 0)
            verbose = self.machine.configuration.get('verbose', False)
            
            logger.info(f"Attempting to connect to ZKT machine at {ip}:{port} (timeout: {timeout}s, skip_ping: {ommit_ping})")
            
            # Initialize ZK with options to skip ping test (useful when ping is blocked but TCP works)
            self.zk = self.ZK(
                ip, 
                port=port, 
                timeout=timeout,
                password=password,
                force_udp=force_udp,
                ommit_ping=ommit_ping,  # Skip ping test - useful when firewall blocks ICMP
                verbose=verbose
            )
            self.zk.connect()
            self.connected = True
            self.connection_error = None
            logger.info(f"Successfully connected to ZKT machine at {ip}:{port}")
            return True
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e)
            full_error = f"Failed to connect to ZKT machine at {ip}:{port}. Error ({error_type}): {error_msg}"
            logger.error(full_error)
            self.connected = False
            self.connection_error = full_error
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from ZKT machine"""
        if self.zk and self.connected:
            try:
                self.zk.disconnect()
                self.connected = False
                logger.info("Disconnected from ZKT machine")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from ZKT machine: {str(e)}")
                return False
        return True
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.connected and self.zk is not None
    
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        """Get attendance data from ZKT machine"""
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            attendance_records = self.zk.get_attendance()
            results = []
            
            for record in attendance_records:
                record_date = record.timestamp.date() if hasattr(record.timestamp, 'date') else record.timestamp
                
                # Filter by date range if provided
                if start_date:
                    if isinstance(start_date, datetime):
                        start_date = start_date.date()
                    if record_date < start_date:
                        continue
                
                if end_date:
                    if isinstance(end_date, datetime):
                        end_date = end_date.date()
                    if record_date > end_date:
                        continue
                
                results.append({
                    'user_id': str(record.user_id),
                    'timestamp': record.timestamp,
                    'status': record.status if hasattr(record, 'status') else 'check_in',
                    'raw_data': {
                        'punch': record.punch if hasattr(record, 'punch') else None,
                        'uid': record.uid if hasattr(record, 'uid') else None,
                    }
                })
            
            return results
        except Exception as e:
            logger.error(f"Error getting attendance data from ZKT: {str(e)}")
            return []
    
    def get_users(self) -> List[Dict]:
        """Get users from ZKT machine"""
        if not self.is_connected():
            if not self.connect():
                return []
        
        try:
            users = self.zk.get_users()
            results = []
            
            for user in users:
                results.append({
                    'user_id': str(user.uid),
                    'name': user.name if hasattr(user, 'name') else '',
                    'privilege': user.privilege if hasattr(user, 'privilege') else 0,
                    'raw_data': {
                        'password': user.password if hasattr(user, 'password') else None,
                    }
                })
            
            return results
        except Exception as e:
            logger.error(f"Error getting users from ZKT: {str(e)}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """Test ZKT connection"""
        try:
            if not self.ZK:
                return {
                    'success': False,
                    'message': 'ZKT SDK not available. Please install "zk" or "pyzk" package.'
                }
            
            ip = self.machine.ip_address
            port = self.machine.port or 4370
            
            if not ip:
                return {
                    'success': False,
                    'message': 'IP address is not configured for this machine'
                }
            
            # Try to connect
            if self.connect():
                # Try to get machine time to verify connection
                try:
                    machine_time = self.zk.get_time()
                    self.disconnect()
                    return {
                        'success': True,
                        'message': f'Successfully connected to {ip}:{port}. Machine time: {machine_time}'
                    }
                except Exception as e:
                    self.disconnect()
                    return {
                        'success': True,
                        'message': f'Successfully connected to {ip}:{port} (could not get machine time: {str(e)})'
                    }
            else:
                return {
                    'success': False,
                    'message': f'Failed to connect to {ip}:{port}. Check IP address, port, network connectivity, and firewall settings.'
                }
        except ConnectionError as e:
            return {
                'success': False,
                'message': str(e)
            }
        except Exception as e:
            error_type = type(e).__name__
            return {
                'success': False,
                'message': f'Connection error ({error_type}): {str(e)}'
            }


class GenericAPIDriver(MachineDriver):
    """Driver for generic API/Webhook based machines"""
    
    def __init__(self, machine):
        super().__init__(machine)
        import requests
        self.requests = requests
    
    def connect(self) -> bool:
        """For API, connection is just validation"""
        if not self.machine.url:
            logger.error("API URL not configured")
            return False
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """No persistent connection for API"""
        self.connected = False
        return True
    
    def is_connected(self) -> bool:
        """Check if API is accessible"""
        return self.connected and bool(self.machine.url)
    
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        """Get attendance data via API"""
        if not self.is_connected():
            return []
        
        try:
            url = self.machine.url
            if not url.endswith('/'):
                url += '/'
            
            # Construct API endpoint
            endpoint = self.machine.configuration.get('attendance_endpoint', 'attendance')
            api_url = f"{url}{endpoint}"
            
            # Prepare request parameters
            params = {}
            headers = {}
            
            if self.machine.api_key:
                auth_type = self.machine.configuration.get('auth_type', 'header')
                if auth_type == 'header':
                    header_name = self.machine.configuration.get('api_key_header', 'X-API-Key')
                    headers[header_name] = self.machine.api_key
                elif auth_type == 'query':
                    params['api_key'] = self.machine.api_key
            
            if start_date:
                params['start_date'] = start_date.isoformat() if hasattr(start_date, 'isoformat') else str(start_date)
            if end_date:
                params['end_date'] = end_date.isoformat() if hasattr(end_date, 'isoformat') else str(end_date)
            
            # Make API request
            response = self.requests.get(api_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response (adjust based on API format)
            results = []
            attendance_list = data.get('data', data.get('attendance', data.get('results', [])))
            
            for record in attendance_list:
                results.append({
                    'user_id': str(record.get('user_id', record.get('employee_id', ''))),
                    'timestamp': datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00')) if isinstance(record.get('timestamp'), str) else record.get('timestamp'),
                    'status': record.get('status', 'check_in'),
                    'raw_data': record
                })
            
            return results
        except Exception as e:
            logger.error(f"Error getting attendance data from API: {str(e)}")
            return []
    
    def get_users(self) -> List[Dict]:
        """Get users via API"""
        if not self.is_connected():
            return []
        
        try:
            url = self.machine.url
            if not url.endswith('/'):
                url += '/'
            
            endpoint = self.machine.configuration.get('users_endpoint', 'users')
            api_url = f"{url}{endpoint}"
            
            headers = {}
            if self.machine.api_key:
                header_name = self.machine.configuration.get('api_key_header', 'X-API-Key')
                headers[header_name] = self.machine.api_key
            
            response = self.requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            users_list = data.get('data', data.get('users', data.get('results', [])))
            
            results = []
            for user in users_list:
                results.append({
                    'user_id': str(user.get('user_id', user.get('id', ''))),
                    'name': user.get('name', ''),
                    'privilege': user.get('privilege', 0),
                    'raw_data': user
                })
            
            return results
        except Exception as e:
            logger.error(f"Error getting users from API: {str(e)}")
            return []
    
    def test_connection(self) -> Dict[str, Any]:
        """Test API connection"""
        try:
            url = self.machine.url
            if not url:
                return {
                    'success': False,
                    'message': 'API URL not configured'
                }
            
            # Try to access health/status endpoint
            test_endpoint = self.machine.configuration.get('test_endpoint', 'health')
            if not url.endswith('/'):
                url += '/'
            test_url = f"{url}{test_endpoint}"
            
            headers = {}
            if self.machine.api_key:
                header_name = self.machine.configuration.get('api_key_header', 'X-API-Key')
                headers[header_name] = self.machine.api_key
            
            response = self.requests.get(test_url, headers=headers, timeout=5)
            response.raise_for_status()
            
            return {
                'success': True,
                'message': f'Successfully connected to API. Status: {response.status_code}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'API connection error: {str(e)}'
            }


class RealTimeDriver(MachineDriver):
    """Driver for RealTime biometric machines"""
    
    def connect(self) -> bool:
        """Connect to RealTime machine"""
        # Implementation for RealTime machines
        # This is a placeholder - implement based on RealTime SDK
        logger.warning("RealTime driver not fully implemented")
        return False
    
    def disconnect(self) -> bool:
        return True
    
    def is_connected(self) -> bool:
        return self.connected
    
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        return []
    
    def get_users(self) -> List[Dict]:
        return []
    
    def test_connection(self) -> Dict[str, Any]:
        return {
            'success': False,
            'message': 'RealTime driver not yet implemented'
        }


class BioStarDriver(MachineDriver):
    """Driver for BioStar biometric machines"""
    
    def connect(self) -> bool:
        """Connect to BioStar machine"""
        # Implementation for BioStar machines
        # This is a placeholder - implement based on BioStar SDK
        logger.warning("BioStar driver not fully implemented")
        return False
    
    def disconnect(self) -> bool:
        return True
    
    def is_connected(self) -> bool:
        return self.connected
    
    def get_attendance_data(self, start_date=None, end_date=None) -> List[Dict]:
        return []
    
    def get_users(self) -> List[Dict]:
        return []
    
    def test_connection(self) -> Dict[str, Any]:
        return {
            'success': False,
            'message': 'BioStar driver not yet implemented'
        }


# Driver factory
def get_machine_driver(machine):
    """
    Factory function to get appropriate driver for a machine
    
    Args:
        machine: AttendanceMachine instance
    
    Returns:
        MachineDriver instance
    """
    from .models import AttendanceMachine
    
    machine_type = machine.machine_type
    
    if machine_type == AttendanceMachine.MACHINE_TYPE_ZKT:
        return ZKTDriver(machine)
    elif machine_type == AttendanceMachine.MACHINE_TYPE_GENERIC_API:
        return GenericAPIDriver(machine)
    elif machine_type == AttendanceMachine.MACHINE_TYPE_REALTIME:
        return RealTimeDriver(machine)
    elif machine_type == AttendanceMachine.MACHINE_TYPE_BIOSTAR:
        return BioStarDriver(machine)
    else:
        # Default to API driver for unknown types
        logger.warning(f"Unknown machine type {machine_type}, using GenericAPIDriver")
        return GenericAPIDriver(machine)

