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


def diff_dict(dict1, dict2):
    keys = set(dict1.keys()).union(set(dict2.keys()))
    result = {}
    diff_lib = diff_match_patch()
    for key in keys:
        str1 = dict1.get(key, "")
        str2 = dict2.get(key, "")
        result[key] = diff_lib.diff_prettyHtml(diff_lib.diff_main(str1, str2))
    return result


def get_revision_difference(base, new):
    result = []
    for base_object, new_object in base.find_matching_pairs(new):
        not_none_obj = new_object if new_object is not None else base_object
        if not_none_obj.differ(base_object, new_object):
            if base_object is None:
                operation = "Added"
            elif new_object is None:
                operation = "Deleted"
            else:
                operation = "Changed"
            base_dict = base_object.get_value_as_dict() if base_object is not None else {}
            new_dict = new_object.get_value_as_dict() if new_object is not None else {}

            result.append((
                "{} {} - {}".format(operation, type(not_none_obj)._meta.verbose_name, str(new_object)),
                diff_dict(base_dict, new_dict)
            ))
    return result

