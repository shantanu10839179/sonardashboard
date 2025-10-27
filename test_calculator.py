"""
Test module for calculator.py
This module contains comprehensive tests for SonarQube analysis.
"""

import pytest
import math
from calculator import (
    Calculator, factorial, fibonacci, is_prime, find_primes_up_to,
    gcd, lcm, validate_positive_number, process_numbers, problematic_function
)


class TestCalculator:
    """Test cases for Calculator class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.calc = Calculator()
    
    def test_add(self):
        """Test addition operation."""
        assert self.calc.add(2, 3) == 5
        assert self.calc.add(-1, 1) == 0
        assert self.calc.add(0, 0) == 0
        assert self.calc.add(1.5, 2.5) == 4.0
    
    def test_subtract(self):
        """Test subtraction operation."""
        assert self.calc.subtract(5, 3) == 2
        assert self.calc.subtract(0, 5) == -5
        assert self.calc.subtract(-3, -2) == -1
        assert self.calc.subtract(10.5, 5.5) == 5.0
    
    def test_multiply(self):
        """Test multiplication operation."""
        assert self.calc.multiply(3, 4) == 12
        assert self.calc.multiply(-2, 3) == -6
        assert self.calc.multiply(0, 100) == 0
        assert self.calc.multiply(2.5, 4) == 10.0
    
    def test_divide(self):
        """Test division operation."""
        assert self.calc.divide(10, 2) == 5
        assert self.calc.divide(7, 2) == 3.5
        assert self.calc.divide(-6, 3) == -2
        
        # Test division by zero
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            self.calc.divide(5, 0)
    
    def test_power(self):
        """Test power operation."""
        assert self.calc.power(2, 3) == 8
        assert self.calc.power(5, 0) == 1
        assert self.calc.power(4, 0.5) == 2
        assert self.calc.power(-2, 3) == -8
    
    def test_square_root(self):
        """Test square root operation."""
        assert self.calc.square_root(4) == 2
        assert self.calc.square_root(9) == 3
        assert abs(self.calc.square_root(2) - math.sqrt(2)) < 1e-10
        
        # Test negative input
        with pytest.raises(ValueError, match="Cannot calculate square root of negative number"):
            self.calc.square_root(-4)
    
    def test_history(self):
        """Test calculation history functionality."""
        # Initially empty
        assert self.calc.get_history() == []
        
        # Add some operations
        self.calc.add(2, 3)
        self.calc.multiply(4, 5)
        
        history = self.calc.get_history()
        assert len(history) == 2
        assert "add(2, 3) = 5" in history
        assert "multiply(4, 5) = 20" in history
        
        # Clear history
        self.calc.clear_history()
        assert self.calc.get_history() == []


class TestMathFunctions:
    """Test cases for standalone math functions."""
    
    def test_factorial(self):
        """Test factorial function."""
        assert factorial(0) == 1
        assert factorial(1) == 1
        assert factorial(5) == 120
        assert factorial(6) == 720
        
        # Test negative input
        with pytest.raises(ValueError, match="Factorial is not defined for negative numbers"):
            factorial(-1)
    
    def test_fibonacci(self):
        """Test Fibonacci function."""
        assert fibonacci(0) == 0
        assert fibonacci(1) == 1
        assert fibonacci(2) == 1
        assert fibonacci(3) == 2
        assert fibonacci(4) == 3
        assert fibonacci(5) == 5
        assert fibonacci(10) == 55
        
        # Test negative input
        with pytest.raises(ValueError, match="Fibonacci is not defined for negative numbers"):
            fibonacci(-1)
    
    def test_is_prime(self):
        """Test prime number checking."""
        # Test known primes
        assert is_prime(2) is True
        assert is_prime(3) is True
        assert is_prime(5) is True
        assert is_prime(7) is True
        assert is_prime(11) is True
        assert is_prime(17) is True
        
        # Test non-primes
        assert is_prime(1) is False
        assert is_prime(4) is False
        assert is_prime(6) is False
        assert is_prime(8) is False
        assert is_prime(9) is False
        assert is_prime(15) is False
        
        # Test edge cases
        assert is_prime(0) is False
        assert is_prime(-5) is False
    
    def test_find_primes_up_to(self):
        """Test finding primes up to a limit."""
        assert find_primes_up_to(1) == []
        assert find_primes_up_to(2) == [2]
        assert find_primes_up_to(10) == [2, 3, 5, 7]
        assert find_primes_up_to(20) == [2, 3, 5, 7, 11, 13, 17, 19]
        
        # Test negative limit
        assert find_primes_up_to(-5) == []
    
    def test_gcd(self):
        """Test Greatest Common Divisor function."""
        assert gcd(12, 8) == 4
        assert gcd(15, 10) == 5
        assert gcd(17, 13) == 1  # Coprime numbers
        assert gcd(0, 5) == 5
        assert gcd(21, 14) == 7
        
        # Test negative numbers
        assert gcd(-12, 8) == 4
        assert gcd(12, -8) == 4
    
    def test_lcm(self):
        """Test Least Common Multiple function."""
        assert lcm(12, 8) == 24
        assert lcm(15, 10) == 30
        assert lcm(17, 13) == 221  # Coprime numbers
        assert lcm(0, 5) == 0
        assert lcm(21, 14) == 42
        
        # Test negative numbers
        assert lcm(-12, 8) == 24
        assert lcm(12, -8) == 24


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    def test_validate_positive_number(self):
        """Test positive number validation."""
        assert validate_positive_number(5) is True
        assert validate_positive_number(0.1) is True
        assert validate_positive_number(1000) is True
        
        assert validate_positive_number(0) is False
        assert validate_positive_number(-5) is False
        assert validate_positive_number(-0.1) is False
    
    def test_process_numbers(self):
        """Test number processing function."""
        # Test empty list
        result = process_numbers([])
        expected = {"count": 0, "sum": 0, "average": 0, "min": None, "max": None}
        assert result == expected
        
        # Test single number
        result = process_numbers([5])
        expected = {"count": 1, "sum": 5, "average": 5, "min": 5, "max": 5}
        assert result == expected
        
        # Test multiple numbers
        result = process_numbers([1, 2, 3, 4, 5])
        expected = {"count": 5, "sum": 15, "average": 3, "min": 1, "max": 5}
        assert result == expected
        
        # Test with negative numbers
        result = process_numbers([-2, -1, 0, 1, 2])
        expected = {"count": 5, "sum": 0, "average": 0, "min": -2, "max": 2}
        assert result == expected
    
    def test_problematic_function(self):
        """Test the intentionally problematic function."""
        # Test with valid data
        result = problematic_function([1, -2, 3, -4, 5])
        expected = [2, -2, 6, -4, 10]
        assert result == expected
        
        # Test with empty list
        assert problematic_function([]) is None
        
        # Test with None input
        assert problematic_function(None) is None
        
        # Test with all negative numbers
        result = problematic_function([-1, -2, -3])
        expected = [-1, -2, -3]
        assert result == expected


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_large_numbers(self):
        """Test with large numbers."""
        calc = Calculator()
        large_num = 10**10
        
        assert calc.add(large_num, large_num) == 2 * large_num
        assert calc.multiply(large_num, 2) == 2 * large_num
    
    def test_floating_point_precision(self):
        """Test floating point precision issues."""
        calc = Calculator()
        
        # This might have precision issues
        result = calc.add(0.1, 0.2)
        assert abs(result - 0.3) < 1e-10
    
    def test_special_values(self):
        """Test with special floating point values."""
        calc = Calculator()
        
        # Test with infinity (if supported)
        try:
            result = calc.add(float('inf'), 1)
            assert result == float('inf')
        except:
            pass  # Skip if not supported
    

# Parametrized tests
@pytest.mark.parametrize("a,b,expected", [
    (1, 1, 2),
    (0, 0, 0),
    (-1, 1, 0),
    (100, -50, 50),
    (0.5, 0.5, 1.0)
])
def test_addition_parametrized(a, b, expected):
    """Parametrized test for addition."""
    calc = Calculator()
    assert calc.add(a, b) == expected


@pytest.mark.parametrize("number,expected", [
    (2, True),
    (3, True),
    (4, False),
    (17, True),
    (18, False),
    (97, True)
])
def test_is_prime_parametrized(number, expected):
    """Parametrized test for prime checking."""
    assert is_prime(number) == expected


# Performance test (marked to be skipped by default)
@pytest.mark.slow
def test_large_fibonacci():
    """Test Fibonacci with larger numbers (performance test)."""
    result = fibonacci(30)
    assert result == 832040


if __name__ == "__main__":
    pytest.main([__file__])