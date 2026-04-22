import asyncio
from typing import Callable, Dict, List, Any
import logging
from .events import Event, EventType

logger = logging.getLogger("EventBus")

class EventBus:
    """Async event bus for decoupled communication between modules."""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], Any]]] = {
            event_type: [] for event_type in EventType
        }
        self._queue: asyncio.Queue[Event] = asyncio.Queue()
        self._running = False
        self._task = None

    def subscribe(self, event_type: EventType, callback: Callable[[Event], Any]):
        """Subscribe a callback to a specific event type."""
        self._subscribers[event_type].append(callback)

    async def publish(self, event: Event):
        """Publish an event to the queue."""
        await self._queue.put(event)

    async def _process_events(self):
        """Background task to process events from the queue."""
        while self._running:
            try:
                event = await self._queue.get()
                subscribers = self._subscribers.get(event.type, [])
                for callback in subscribers:
                    try:
                        # If callback is async, await it
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event)
                        else:
                            callback(event)
                    except Exception as e:
                        logger.error(f"Error in callback for {event.type}: {e}")
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Event bus error: {e}")

    def start(self):
        """Start the event processing loop."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Stop the event processing loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
