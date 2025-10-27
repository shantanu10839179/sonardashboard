"""
Calculator module with various mathematical operations.
This module demonstrates different code patterns for SonarQube analysis.
"""

import math
from typing import List, Optional


class Calculator:
    """A calculator class with various mathematical operations."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"divide({a}, {b}) = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate power of a number."""
        result = base ** exponent
        self.history.append(f"power({base}, {exponent}) = {result}")
        return result
    
    def square_root(self, number: float) -> float:
        """Calculate square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = math.sqrt(number)
        self.history.append(f"square_root({number}) = {result}")
        return result
    
    def get_history(self) -> List[str]:
        """Get calculation history."""
        return self.history.copy()
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.history.clear()


def factorial(n: int) -> int:
    """Calculate factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    return n * factorial(n - 1)


def fibonacci(n: int) -> int:
    """Calculate nth Fibonacci number."""
    if n < 0:
        raise ValueError("Fibonacci is not defined for negative numbers")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


def is_prime(number: int) -> bool:
    """Check if a number is prime."""
    if number < 2:
        return False
    if number == 2:
        return True
    if number % 2 == 0:
        return False
    
    for i in range(3, int(math.sqrt(number)) + 1, 2):
        if number % i == 0:
            return False
    return True


def find_primes_up_to(limit: int) -> List[int]:
    """Find all prime numbers up to a given limit."""
    if limit < 2:
        return []
    
    primes = []
    for num in range(2, limit + 1):
        if is_prime(num):
            primes.append(num)
    return primes


def gcd(a: int, b: int) -> int:
    """Calculate Greatest Common Divisor using Euclidean algorithm."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a: int, b: int) -> int:
    """Calculate Least Common Multiple."""
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def validate_positive_number(number: float) -> bool:
    """Validate if a number is positive."""
    return number > 0


def process_numbers(numbers: List[float]) -> dict:
    """Process a list of numbers and return statistics."""
    if not numbers:
        return {"count": 0, "sum": 0, "average": 0, "min": None, "max": None}
    
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers)
    }

# Add this to any Python file in the repo
def unused_function():
    pass

a = 1  # Unused variable (SonarCloud will flag this)


# This function intentionally has some code smells for SonarQube to detect
def problematic_function(data):
    """A function with intentional code issues for SonarQube analysis."""
    # Unused variable
    unused_var = "This variable is never used"
    
    # Complex condition that could be simplified
    if data is not None and len(data) > 0 and data != []:
        result = []
        for i in range(len(data)):  # Should use enumerate or direct iteration
            if data[i] > 0:
                result.append(data[i] * 2)
            else:
                result.append(data[i])
        return result
    else:
        return None


if __name__ == "__main__":
    # Example usage
    calc = Calculator()
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"Factorial of 5 = {factorial(5)}")
    print(f"5th Fibonacci number = {fibonacci(5)}")
    print(f"Is 17 prime? {is_prime(17)}")
    print(f"Primes up to 20: {find_primes_up_to(20)}")