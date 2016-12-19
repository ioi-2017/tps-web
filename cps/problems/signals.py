from django.db.models.signals import post_save
from django.dispatch import receiver

from problems.models import Solution, Validator, InputGenerator


@receiver(post_save, sender=Solution, dispatch_uid="invalidate_testcase_solution")
def invalidate_testcase_on_solution_change(sender, instance, **kwargs):
    problem = instance.problem
    testcases = problem.testcase_set.all()
    for testcase in testcases:
        if testcase.solution == instance:
            testcase.invalidate()


@receiver(post_save, sender=Validator, dispatch_uid="invalidate_testcase_validator")
def invalidate_testcase_on_validator_change(sender, instance, **kwargs):
    testcases = instance.testcases
    for testcase in testcases:
        testcase.invalidate()
        # TODO: We can only invalidate validation results here. Should we?


@receiver(post_save, sender=InputGenerator, dispatch_uid="invalidate_testcase_generator")
def invalidate_testcase_on_generator_change(sender, instance, **kwargs):
    if not isinstance(instance, InputGenerator):
        return

    testcases = instance.problem.testcase_set.filter(
            _input_generator_name=instance.name
    )
    for testcase in testcases:
        testcase.invalidate()
