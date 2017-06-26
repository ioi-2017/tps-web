from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q

from problems.models import MergeRequest
from problems.models.enums import SolutionVerdict
from .utils import extract_revision_data


def revision_data(request):
    if "problem_id" not in request.resolver_match.kwargs:
        return {}
    problem_id = request.resolver_match.kwargs["problem_id"]
    revision_slug = request.resolver_match.kwargs["revision_slug"]
    problem, branch, revision = extract_revision_data(problem_id, revision_slug, request.user)
    revision_editable = revision.editable(request.user)

    errors = {}
    """
    errors["testcase"] = revision.testcase_set.all().count()
    if revision.solution_set.filter(verdict=SolutionVerdict.model_solution.name).exists():
        errors["solution"] = 0
    else:
        errors["solution"] = 1
    invocations = revision.solutionrun_set.all()
    failed_invocations = 0
    for invocation in invocations:
        if not invocation.validate():
            failed_invocations += 1
    errors["invocation"] = failed_invocations
    if revision.problem_data.checker is None:
        errors["checker"] = 1
    else:
        errors["checker"] = 0
    if not revision.validator_set.all().exists():
        errors["validator"] = 1
    else:
        errors["validator"] = 0
    errors["discussion"] = problem.discussions.filter(closed=False).count()
    errors["merge_requests"] = problem.merge_requests.filter(status=MergeRequest.OPEN).count()
    """
    branches = problem.branches.all()
    return {
        "problem": problem,
        "revision": revision,
        "branch": branch,
        "branches": branches,
        "revision_slug": revision_slug,
        "revision_editable": revision_editable,
        "branches_disabled": getattr(settings, "DISABLE_BRANCHES", False),
        "errors": errors
    }
