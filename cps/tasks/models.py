from enum import Enum

from django.db import models
from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from tasks.decorators import allow_async_method


class State(Enum):
    created = "created"
    queued = "queued",
    running = "running",
    finished = "finished"


class Task(models.Model):
    STATES = (
        (State.created.value, _("Created")),
        (State.queued.value, _("Queued")),
        (State.running.value, _("Running")),
        (State.finished.value, _("Finished")),
    )
    queue_reference_key = models.CharField(null=True, max_length=256, verbose_name=_("queue reference key"))
    state = models.CharField(max_length=20, verbose_name=_("state"), choices=STATES, default=State.created.value)

    def run(self, *args, **kwargs):
        raise NotImplementedError

    @allow_async_method
    def apply(self, *args, **kwargs):
        # TODO: Try to acquire a lock with a specific name
        # to avoid simultaneous execution of some tasks.
        # If not successful retry after some time
        self.state = State.running.value
        self.save()
        # TODO: Handle the case where run might fail with an exception
        self.run(*args, **kwargs)
        self.state = State.finished.value
        self.save()

    def apply_async(self, *args, **kwargs):
        sig = self.apply.s(*args, **kwargs)
        result = sig.freeze()
        with transaction.atomic():
            self.queue_reference_key = result.id
            self.state = State.queued.value
            self.save()
            result = sig.apply() # FIXME: Make this async
            result.wait(propagate = True)

    def abort(self):
        """
        Marks this task as aborted
        Note that abort doesn't guarantee that the task won't be executed.
        """
        pass
        # TODO: Implement it.
