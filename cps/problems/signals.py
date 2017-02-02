from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from problems.models import Solution, Validator, InputGenerator, Resource


@receiver(post_save, sender=Solution, dispatch_uid="invalidate_testcase_solution")
@receiver(pre_delete, sender=Solution, dispatch_uid="invalidate_testcase_solution_delete")
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
@receiver(pre_delete, sender=InputGenerator, dispatch_uid="invalidate_testcase_generator_delete")
def invalidate_testcase_on_generator_change(sender, instance, **kwargs):

    testcases = instance.problem.testcase_set.filter(
            _input_generator_name=instance.name
    )
    for testcase in testcases:
        testcase.invalidate()


@receiver(post_save, sender=Resource, dispatch_uid="invalidate_file_compilation_resource")
@receiver(pre_delete, sender=Resource, dispatch_uid="invalidate_file_compilation_resource")
def invalidate_testcase_on_validator_change(sender, instance, **kwargs):
    revision = instance.problem
    revision.validator_set.update(_compiled_file=None)
    revision.checker_set.update(_compiled_file=None)
    revision.inputgenerator_set.update(_compiled_file=None)