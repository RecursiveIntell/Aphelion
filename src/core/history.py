from abc import ABC, abstractmethod

class Command(ABC):
    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def undo(self):
        pass

class HistoryManager:
    def __init__(self, limit: int = 50):
        self.undo_stack: list[Command] = []
        self.redo_stack: list[Command] = []
        self.limit = limit
        
    def push(self, command: Command):
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        
    def undo(self):
        if self.can_undo():
            command = self.undo_stack.pop()
            command.undo()
            self.redo_stack.append(command)
            return True
        return False

    def redo(self):
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
        # Index refers to position in undo_stack.
        # 0 = First command ever.
        # len-1 = Current top.
        
        current_idx = len(self.undo_stack) - 1
        if index < 0 or index > current_idx:
            return
            
        steps = current_idx - index
        for _ in range(steps):
            self.undo()
