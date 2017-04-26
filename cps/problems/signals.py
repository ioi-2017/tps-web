from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver

from problems.models import Solution, Validator, InputGenerator, Resource, ProblemBranch


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
def invalidate_compiled_on_resource_change(sender, instance, **kwargs):
    revision = instance.problem
    revision.validator_set.update(compiled_file=None, compilation_task_id=None, compilation_finished=False)
    revision.checker_set.update(compiled_file=None, compilation_task_id=None, compilation_finished=False)
    revision.inputgenerator_set.update(compiled_file=None, compilation_task_id=None, compilation_finished=False)


@receiver(post_delete, sender=ProblemBranch, dispatch_uid="delete_branch_working_copy")
def delete_working_copy_on_branch_delete(sender, instance, **kwargs):
    if instance.has_working_copy():
        instance.working_copy.delete()