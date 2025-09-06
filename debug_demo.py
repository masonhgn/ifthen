#!/usr/bin/env python3
"""
Demo script showing how to use the debug decorators.
"""

from debug_utils import debug_function, debug_method, set_debug, is_debug_enabled

# Example function with debug decorator
@debug_function
def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

# Example class with debug methods
class Calculator:
    def __init__(self, name):
        self.name = name
        self.history = []
    
    @debug_method
    def multiply(self, x, y):
        """Multiply two numbers."""
        result = x * y
        self.history.append(f"{x} * {y} = {result}")
        return result
    
    @debug_method
    def get_history(self):
        """Get calculation history."""
        return self.history.copy()

def main():
    print("=== Debug Decorator Demo ===\n")
    
    # Test with debug enabled
    print("1. Testing with debug ENABLED:")
    set_debug(True)
    print(f"Debug enabled: {is_debug_enabled()}")
    
    result1 = add_numbers(5, 3)
    calc = Calculator("MyCalc")
    result2 = calc.multiply(4, 7)
    history = calc.get_history()
    
    print(f"\nResults: {result1}, {result2}")
    print(f"History: {history}")
    
    print("\n" + "="*50 + "\n")
    
    # Test with debug disabled
    print("2. Testing with debug DISABLED:")
    set_debug(False)
    print(f"Debug enabled: {is_debug_enabled()}")
    
    result3 = add_numbers(10, 20)
    calc2 = Calculator("SilentCalc")
    result4 = calc2.multiply(6, 8)
    history2 = calc2.get_history()
    
    print(f"\nResults: {result3}, {result4}")
    print(f"History: {history2}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()
