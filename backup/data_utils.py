"""
Data processing utilities module.
This module provides additional code for SonarQube analysis.
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User data class."""
    id: int
    name: str
    email: str
    created_at: datetime
    is_active: bool = True


class DataProcessor:
    """Data processing utility class."""
    
    def __init__(self):
        self.processed_count = 0
        self.errors = []
    
    def validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def process_user_data(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Process and validate user data."""
        try:
            # Validate required fields
            required_fields = ['id', 'name', 'email']
            for field in required_fields:
                if field not in user_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Clean and prepare email for validation
            email_cleaned = str(user_data['email']).lower().strip()
            
            # Validate email
            if not self.validate_email(email_cleaned):
                raise ValueError(f"Invalid email format: {user_data['email']}")
            
            # Create user object
            user = User(
                id=int(user_data['id']),
                name=str(user_data['name']).strip(),
                email=email_cleaned,
                created_at=datetime.now(),
                is_active=user_data.get('is_active', True)
            )
            
            self.processed_count += 1
            return user
            
        except (ValueError, TypeError) as e:
            error_msg = f"Error processing user data: {str(e)}"
            self.errors.append(error_msg)
            return None
    
    def process_users_batch(self, users_data: List[Dict[str, Any]]) -> List[User]:
        """Process a batch of user data."""
        valid_users = []
        
        for user_data in users_data:
            user = self.process_user_data(user_data)
            if user:
                valid_users.append(user)
        
        return valid_users
    
    def export_users_to_json(self, users: List[User], filename: str) -> bool:
        """Export users to JSON file."""
        try:
            users_dict = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'is_active': user.is_active
                }
                users_dict.append(user_dict)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(users_dict, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            self.errors.append(f"Error exporting to JSON: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            'processed_count': self.processed_count,
            'error_count': len(self.errors),
            'errors': self.errors.copy()
        }
    
    def reset_statistics(self) -> None:
        """Reset processing statistics."""
        self.processed_count = 0
        self.errors.clear()


def filter_active_users(users: List[User]) -> List[User]:
    """Filter active users from a list."""
    return [user for user in users if user.is_active]


def sort_users_by_name(users: List[User]) -> List[User]:
    """Sort users by name."""
    return sorted(users, key=lambda user: user.name.lower())


def find_user_by_email(users: List[User], email: str) -> Optional[User]:
    """Find user by email address."""
    email_lower = email.lower().strip()
    for user in users:
        if user.email == email_lower:
            return user
    return None


def group_users_by_domain(users: List[User]) -> Dict[str, List[User]]:
    """Group users by email domain."""
    groups = {}
    
    for user in users:
        domain = user.email.split('@')[1] if '@' in user.email else 'unknown'
        
        if domain not in groups:
            groups[domain] = []
        
        groups[domain].append(user)
    
    return groups


def calculate_user_stats(users: List[User]) -> Dict[str, Any]:
    """Calculate user statistics."""
    if not users:
        return {
            'total_users': 0,
            'active_users': 0,
            'inactive_users': 0,
            'domains': []
        }
    
    active_count = sum(1 for user in users if user.is_active)
    domains = set(user.email.split('@')[1] for user in users if '@' in user.email)
    
    return {
        'total_users': len(users),
        'active_users': active_count,
        'inactive_users': len(users) - active_count,
        'domains': sorted(list(domains))
    }


# This function has some code smells for SonarQube to detect
def poorly_written_function(data, flag, mode):
    """A poorly written function with various code issues."""
    # Too many parameters, poor naming, no type hints
    
    result = None
    temp = []
    
    # Deeply nested conditions
    if data is not None:
        if len(data) > 0:
            if flag == True:  # Should use 'if flag:'
                if mode == "process":
                    for i in range(len(data)):  # Should use enumerate
                        if data[i] is not None:
                            if isinstance(data[i], str):
                                if len(data[i]) > 0:
                                    temp.append(data[i].upper())
                                else:
                                    temp.append("")
                            else:
                                temp.append(str(data[i]))
                        else:
                            temp.append("NULL")
                    result = temp
                elif mode == "count":
                    count = 0
                    for item in data:
                        if item is not None:
                            count = count + 1  # Should use count += 1
                    result = count
                else:
                    result = "Invalid mode"
            else:
                result = data
        else:
            result = []
    else:
        result = None
    
    return result


if __name__ == "__main__":
    # Example usage
    processor = DataProcessor()
    
    sample_data = [
        {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
        {'id': 2, 'name': 'Jane Smith', 'email': 'jane@company.com', 'is_active': False},
        {'id': 3, 'name': 'Bob Johnson', 'email': 'invalid-email'},  # Invalid email
    ]
    
    users = processor.process_users_batch(sample_data)
    print(f"Processed {len(users)} valid users")
    print(f"Statistics: {processor.get_statistics()}")