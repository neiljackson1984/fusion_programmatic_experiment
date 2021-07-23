"""
This module defines a class named FusionMainThreadRunner, which can be used to run an arbitrary closure in the main 
Fusion thread.
"""

import adsk.core
import adsk
import adsk.fusion
import logging
import queue
import uuid
import sys

from typing import Optional, Callable, Any

class FusionMainThreadRunner(object):
    def __init__(self,
        logger: Optional[logging.Logger] = None
    ):
        self._app : adsk.core.Application = adsk.core.Application.get()
        self._logger = logger
        self._taskQueue : queue.Queue[Callable[[], Any]] = queue.Queue()
        self._processTasksRequestedEventId : str = "fusion_main_thread_runner_" + str(uuid.uuid4())
        self._processTasksRequestedEvent = self._app.registerCustomEvent(self._processTasksRequestedEventId)
        self._processTasksRequestedEventHandler = self.ProcessTasksRequestedEventHandler(owner=self)
        self._processTasksRequestedEvent.add(self._processTasksRequestedEventHandler)

    def __del__(self):
        # clean up _processTasksRequestedEvent and the associated handler:
        try:
            if self._processTasksRequestedEventHandler and self._processTasksRequestedEvent:
                self._processTasksRequestedEvent.remove(self._processTasksRequestedEventHandler)

            if self._processTasksRequestedEvent:
                self._app.unregisterCustomEvent(self._processTasksRequestedEventId)
        except Exception:
            self._logger and self._logger.error("Error while unregistering event handler.",
                         exc_info=sys.exc_info())
        self._processTasksRequestedEventHandler = None
        self._processTasksRequestedEvent = None

    def doTaskInMainFusionThread(self, task: Callable):
        self._taskQueue.put(task)
        result :bool = self._app.fireCustomEvent(self._processTasksRequestedEventId)


    class ProcessTasksRequestedEventHandler(adsk.core.CustomEventHandler):
        def __init__(self, owner: 'FusionMainThreadRunner'):
            super().__init__()
            self._owner = owner

        def notify(self, args: adsk.core.CustomEventArgs):
            try:
                while True:
                    try:
                        self._owner._logger and self._owner._logger.debug("getting from queue...")
                        task = self._owner._taskQueue.get_nowait()
                        self._owner._logger and self._owner._logger.debug("got from queue.")
                    except queue.Empty as e:
                        self._owner._logger and self._owner._logger.debug("tried to get from an empty queue... breaking.")
                        break
                    self._owner._logger and self._owner._logger.debug("running a task.")
                    task()
                    self._owner._taskQueue.task_done()

            except Exception:
                self._owner._logger and self._owner._logger.fatal("An error occurred while attempting to handle the processTasksRequested event", exc_info=sys.exc_info())
            finally:
                pass
