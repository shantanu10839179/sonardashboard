"""
Test module for data_utils.py
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from data_utils import (
    User, DataProcessor, filter_active_users, sort_users_by_name,
    find_user_by_email, group_users_by_domain, calculate_user_stats,
    poorly_written_function
)


class TestUser:
    """Test cases for User dataclass."""
    
    def test_user_creation(self):
        """Test user creation with all fields."""
        now = datetime.now()
        user = User(
            id=1,
            name="John Doe",
            email="john@example.com",
            created_at=now,
            is_active=True
        )
        
        assert user.id == 1
        assert user.name == "John Doe"
        assert user.email == "john@example.com"
        assert user.created_at == now
        assert user.is_active is True
    
    def test_user_default_active(self):
        """Test user creation with default is_active value."""
        user = User(
            id=2,
            name="Jane Smith",
            email="jane@example.com",
            created_at=datetime.now()
        )
        
        assert user.is_active is True


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = DataProcessor()
    
    def test_validate_email_valid(self):
        """Test email validation with valid emails."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.org",
            "user+tag@example.co.uk",
            "123@numbers.com"
        ]
        
        for email in valid_emails:
            assert self.processor.validate_email(email) is True
    
    def test_validate_email_invalid(self):
        """Test email validation with invalid emails."""
        invalid_emails = [
            "not-an-email",
            "@domain.com",
            "user@",
            "user@domain",
            "user space@domain.com",
            ""
        ]
        
        for email in invalid_emails:
            assert self.processor.validate_email(email) is False
    
    def test_process_user_data_valid(self):
        """Test processing valid user data."""
        user_data = {
            'id': 1,
            'name': '  John Doe  ',
            'email': '  JOHN@EXAMPLE.COM  ',
            'is_active': True
        }
        
        user = self.processor.process_user_data(user_data)
        
        assert user is not None
        assert user.id == 1
        assert user.name == "John Doe"  # Trimmed
        assert user.email == "john@example.com"  # Lowercased and trimmed
        assert user.is_active is True
        assert self.processor.processed_count == 1
    
    def test_process_user_data_missing_field(self):
        """Test processing user data with missing required field."""
        user_data = {
            'id': 1,
            'name': 'John Doe'
            # Missing email
        }
        
        user = self.processor.process_user_data(user_data)
        
        assert user is None
        assert len(self.processor.errors) == 1
        assert "Missing required field: email" in self.processor.errors[0]
    
    def test_process_user_data_invalid_email(self):
        """Test processing user data with invalid email."""
        user_data = {
            'id': 1,
            'name': 'John Doe',
            'email': 'invalid-email'
        }
        
        user = self.processor.process_user_data(user_data)
        
        assert user is None
        assert len(self.processor.errors) == 1
        assert "Invalid email format" in self.processor.errors[0]
    
    def test_process_users_batch(self):
        """Test processing a batch of users."""
        users_data = [
            {'id': 1, 'name': 'John Doe', 'email': 'john@example.com'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@example.com'},
            {'id': 3, 'name': 'Invalid User', 'email': 'invalid'},  # Invalid
            {'name': 'Missing ID', 'email': 'missing@example.com'}  # Missing ID
        ]
        
        users = self.processor.process_users_batch(users_data)
        
        assert len(users) == 2  # Only 2 valid users
        assert self.processor.processed_count == 2
        assert len(self.processor.errors) == 2
    
    def test_export_users_to_json(self):
        """Test exporting users to JSON file."""
        users = [
            User(1, "John Doe", "john@example.com", datetime.now()),
            User(2, "Jane Smith", "jane@example.com", datetime.now(), False)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            filename = f.name
        
        try:
            result = self.processor.export_users_to_json(users, filename)
            assert result is True
            
            # Verify the file was created and contains correct data
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]['name'] == "John Doe"
            assert data[1]['is_active'] is False
            
        finally:
            if os.path.exists(filename):
                os.unlink(filename)
    
    def test_get_statistics(self):
        """Test getting processing statistics."""
        # Process some data to generate statistics
        valid_data = {'id': 1, 'name': 'John', 'email': 'john@example.com'}
        invalid_data = {'id': 2, 'name': 'Jane'}  # Missing email
        
        self.processor.process_user_data(valid_data)
        self.processor.process_user_data(invalid_data)
        
        stats = self.processor.get_statistics()
        
        assert stats['processed_count'] == 1
        assert stats['error_count'] == 1
        assert len(stats['errors']) == 1
    
    def test_reset_statistics(self):
        """Test resetting statistics."""
        # Generate some statistics first
        self.processor.process_user_data({'invalid': 'data'})
        
        assert self.processor.processed_count > 0 or len(self.processor.errors) > 0
        
        self.processor.reset_statistics()
        
        assert self.processor.processed_count == 0
        assert len(self.processor.errors) == 0


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.users = [
            User(1, "John Doe", "john@example.com", datetime.now(), True),
            User(2, "Jane Smith", "jane@company.com", datetime.now(), False),
            User(3, "Bob Johnson", "bob@example.com", datetime.now(), True),
            User(4, "Alice Brown", "alice@other.org", datetime.now(), True)
        ]
    
    def test_filter_active_users(self):
        """Test filtering active users."""
        active_users = filter_active_users(self.users)
        
        assert len(active_users) == 3
        assert all(user.is_active for user in active_users)
        assert not any(user.name == "Jane Smith" for user in active_users)
    
    def test_sort_users_by_name(self):
        """Test sorting users by name."""
        sorted_users = sort_users_by_name(self.users)
        
        names = [user.name for user in sorted_users]
        assert names == ["Alice Brown", "Bob Johnson", "Jane Smith", "John Doe"]
    
    def test_find_user_by_email(self):
        """Test finding user by email."""
        # Test existing user
        user = find_user_by_email(self.users, "john@example.com")
        assert user is not None
        assert user.name == "John Doe"
        
        # Test case insensitive search
        user = find_user_by_email(self.users, "JOHN@EXAMPLE.COM")
        assert user is not None
        assert user.name == "John Doe"
        
        # Test with whitespace
        user = find_user_by_email(self.users, "  john@example.com  ")
        assert user is not None
        assert user.name == "John Doe"
        
        # Test non-existing user
        user = find_user_by_email(self.users, "nonexistent@example.com")
        assert user is None
    
    def test_group_users_by_domain(self):
        """Test grouping users by email domain."""
        groups = group_users_by_domain(self.users)
        
        assert "example.com" in groups
        assert "company.com" in groups
        assert "other.org" in groups
        
        assert len(groups["example.com"]) == 2
        assert len(groups["company.com"]) == 1
        assert len(groups["other.org"]) == 1
    
    def test_calculate_user_stats(self):
        """Test calculating user statistics."""
        stats = calculate_user_stats(self.users)
        
        assert stats['total_users'] == 4
        assert stats['active_users'] == 3
        assert stats['inactive_users'] == 1
        assert "example.com" in stats['domains']
        assert "company.com" in stats['domains']
        assert "other.org" in stats['domains']
    
    def test_calculate_user_stats_empty(self):
        """Test calculating statistics for empty user list."""
        stats = calculate_user_stats([])
        
        assert stats['total_users'] == 0
        assert stats['active_users'] == 0
        assert stats['inactive_users'] == 0
        assert stats['domains'] == []


class TestProblematicFunction:
    """Test cases for the intentionally problematic function."""
    
    def test_poorly_written_function_process_mode(self):
        """Test the poorly written function in process mode."""
        data = ["hello", "world", None, 123]
        result = poorly_written_function(data, True, "process")
        
        expected = ["HELLO", "WORLD", "NULL", "123"]
        assert result == expected
    
    def test_poorly_written_function_count_mode(self):
        """Test the poorly written function in count mode."""
        data = ["hello", None, "world", None, 123]
        result = poorly_written_function(data, True, "count")
        
        assert result == 3  # Three non-None items
    
    def test_poorly_written_function_invalid_mode(self):
        """Test the poorly written function with invalid mode."""
        data = ["hello", "world"]
        result = poorly_written_function(data, True, "invalid")
        
        assert result == "Invalid mode"
    
    def test_poorly_written_function_flag_false(self):
        """Test the poorly written function with flag=False."""
        data = ["hello", "world"]
        result = poorly_written_function(data, False, "process")
        
        assert result == data
    
    def test_poorly_written_function_none_data(self):
        """Test the poorly written function with None data."""
        result = poorly_written_function(None, True, "process")
        assert result is None
    
    def test_poorly_written_function_empty_data(self):
        """Test the poorly written function with empty data."""
        result = poorly_written_function([], True, "process")
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__])