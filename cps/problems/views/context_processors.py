from django.core.urlresolvers import reverse

from problems.models.enums import SolutionVerdict
from .utils import extract_revision_data




def revision_data(request):
    if "problem_id" not in request.resolver_match.kwargs:
        return {}
    problem_id = request.resolver_match.kwargs["problem_id"]
    revision_slug = request.resolver_match.kwargs["revision_slug"]
    problem, branch, revision = extract_revision_data(problem_id, revision_slug, request.user)
    revision_editable = revision.editable(request.user)
    master = revision.problem.get_master_branch()
    if revision.committed and branch is not None and branch != master:
        can_be_merged_with_master = revision.child_of(master.head)
        should_be_updated_from_master = not can_be_merged_with_master
    else:
        can_be_merged_with_master = False
        should_be_updated_from_master = False

    errors = {}
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


    def get_url_for_slug(view_name, slug, problem_id, revision_slug, *args, **kwargs):
        kwargs["revision_slug"] = slug
        kwargs["problem_id"] = problem_id
        return reverse(view_name, args=args, kwargs=kwargs)

    branches = problem.branches.all()
    return {
        "problem": problem,
        "revision": revision,
        "branch": branch,
        "branches": branches,
        "revision_slug": revision_slug,
        "revision_editable": revision_editable,
        "branch_editable": branch is not None and branch.editable(request.user),
        "errors": errors
    }