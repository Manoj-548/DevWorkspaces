from abc import ABC, abstractmethod

#!/usr/bin/env python3
from abc import ABC, abstractmethod

class Parent(ABC):
    def __init__(self):
        # Initial value set in the parent constructor
        self.value = "Original Parent Value"

    @abstractmethod
    def update_value(self):
        """Must be implemented by child classes."""
        pass

class Child(Parent):
    def update_value(self):
        # Appending/Changing the inherited value using child's logic
        self.value = "Updated by Child Logic"

# This block ensures the code runs when the script is executed
if __name__ == "__main__":
    # 1. Instantiate the child class
    obj = Child()
    
    # 2. Show the initial inherited value
    print(f"DEBUG: Inherited value before update: {obj.value}")
    
    # 3. Call the method to change the value
    obj.update_value()
    
    # 4. Show the final changed value
    print(f"SUCCESS: {obj.value}")

