"""
History management with byte-based memory limits.

Evicts oldest entries when memory budget is exceeded.
"""
from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass
    
    def memory_bytes(self) -> int:
        """Return estimated memory usage in bytes. Override in subclasses."""
        return 0


class HistoryManager:
    """
    Manages undo/redo history with byte-based memory limits.
    
    Instead of limiting by action count (which doesn't account for
    varying command sizes), this tracks total memory usage and
    evicts oldest entries when over budget.
    """
    
    # Default 500MB limit - reasonable for most systems
    DEFAULT_MEMORY_LIMIT_MB = 500
    
    def __init__(self, limit: int = 100, memory_limit_mb: int = None):
        """
        Initialize history manager.
        
        Args:
            limit: Maximum number of commands (backup limit)
            memory_limit_mb: Memory budget in MB. If None, uses DEFAULT_MEMORY_LIMIT_MB.
        """
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []
        self.limit = limit
        self.memory_limit = (memory_limit_mb or self.DEFAULT_MEMORY_LIMIT_MB) * 1024 * 1024
        self._cached_memory = 0
    
    def push(self, command: Command):
        """Add a command to history."""
        self.undo_stack.append(command)
        self._cached_memory += command.memory_bytes()
        
        # Clear redo stack
        for cmd in self.redo_stack:
            self._cached_memory -= cmd.memory_bytes()
        self.redo_stack.clear()
        
        # Evict old commands if over memory budget
        self._evict_if_needed()
        
        # Also respect hard count limit as backup
        while len(self.undo_stack) > self.limit:
            evicted = self.undo_stack.pop(0)
            self._cached_memory -= evicted.memory_bytes()
    
    def _evict_if_needed(self):
        """Evict oldest entries until under memory budget."""
        while self._cached_memory > self.memory_limit and len(self.undo_stack) > 1:
            evicted = self.undo_stack.pop(0)
            self._cached_memory -= evicted.memory_bytes()
    
    def undo(self) -> bool:
        """Undo the last command."""
        if self.can_undo():
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone command."""
        if self.can_redo():
            command = self.redo_stack.pop()
            command.execute()
            self.undo_stack.append(command)
            return True
        return False

    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    def goto_index(self, index: int):
        """Navigate to a specific point in history."""
        current_idx = len(self.undo_stack) - 1
        if index < 0 or index > current_idx:
            return
            
        steps = current_idx - index
        for _ in range(steps):
            self.undo()
    
    def memory_usage_mb(self) -> float:
        """Return current memory usage in MB."""
        return self._cached_memory / (1024 * 1024)
    
    def memory_limit_mb(self) -> float:
        """Return memory limit in MB."""
        return self.memory_limit / (1024 * 1024)
    
    def clear(self):
        """Clear all history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._cached_memory = 0
