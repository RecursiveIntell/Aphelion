"""
Async rendering infrastructure for Aphelion.

Provides QRunnable-based background rendering to keep UI responsive.
"""
from typing import Optional, Callable
from PySide6.QtCore import QRunnable, QObject, Signal, Slot
from PySide6.QtGui import QImage


class RenderSignals(QObject):
    """
    Signals for render task completion.

    QRunnable doesn't inherit QObject, so we need a separate signals object.
    """
    finished = Signal(QImage)  # Emitted with rendered image
    error = Signal(str)  # Emitted with error message


class RenderTask(QRunnable):
    """
    Background rendering task.

    Renders a document on a worker thread and emits signal when complete.
    """

    def __init__(self, document, renderer, callback: Optional[Callable[[QImage], None]] = None):
        """
        Initialize render task.

        Args:
            document: Document to render
            renderer: CairoRenderer instance
            callback: Optional callback to invoke with result on main thread
        """
        super().__init__()
        self.document = document
        self.renderer = renderer
        self.callback = callback
        self.signals = RenderSignals()
        self.setAutoDelete(True)

        # Connect signals if callback provided
        if callback:
            self.signals.finished.connect(callback)

    @Slot()
    def run(self) -> None:
        """Run the render task on worker thread."""
        try:
            # Render the document
            rendered = self.renderer.render_to_qimage(self.document)
            self.signals.finished.emit(rendered)
        except Exception as e:
            self.signals.error.emit(str(e))


class AsyncRenderer:
    """
    Async rendering coordinator.

    Manages background rendering using QThreadPool.
    """

    def __init__(self, thread_pool):
        """
        Initialize async renderer.

        Args:
            thread_pool: QThreadPool instance for background tasks
        """
        self.thread_pool = thread_pool
        self._pending_task: Optional[RenderTask] = None

    def render_async(
        self,
        document,
        renderer,
        callback: Callable[[QImage], None]
    ) -> None:
        """
        Render document asynchronously.

        Args:
            document: Document to render
            renderer: CairoRenderer instance
            callback: Callback invoked with rendered image on main thread
        """
        # Cancel pending task if any
        if self._pending_task is not None:
            # Note: QThreadPool doesn't support cancellation directly
            # We'd need to implement a cancellation flag in RenderTask
            pass

        # Create and start new task
        task = RenderTask(document, renderer, callback)
        self._pending_task = task
        self.thread_pool.start(task)

    def has_pending(self) -> bool:
        """Check if there's a pending render task."""
        return self._pending_task is not None
