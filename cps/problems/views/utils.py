from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from problems.utils.diff_match_patch import diff_match_patch
from problems.models import Problem, ProblemRevision


def extract_revision_data(problem_id, revision_slug, user):
    problem = get_object_or_404(Problem, id=problem_id)
    try:
        revision = ProblemRevision.objects.get(revision_id=revision_slug,
                                               problem=problem)
        branch = None
    except ProblemRevision.DoesNotExist:
        try:
            branch = problem.branches.get(name=revision_slug)
            revision = branch.get_working_copy_or_head(user)
        except ObjectDoesNotExist:
            raise Http404
    return problem, branch, revision


def get_revision_difference(base, new):
    result = []
    diff_lib = diff_match_patch()
    for base_object, new_object in base.find_matching_pairs(new):
        not_none_obj = new_object if new_object is not None else base_object
        if not_none_obj.differ(base_object, new_object):
            if base_object is None:
                operation = "Added"
            elif new_object is None:
                operation = "Deleted"
            else:
                operation = "Changed"
            base_str = base_object.get_value_as_string() if base_object is not None else ""
            new_str = new_object.get_value_as_string() if new_object is not None else ""

            result.append((
                "{} {} - {}".format(operation, type(new_object)._meta.verbose_name, str(new_object)),
                diff_lib.diff_prettyHtml(diff_lib.diff_main(base_str, new_str))
            ))
    return result

