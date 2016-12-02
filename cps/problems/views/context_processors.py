from .utils import extract_revision_data


def revision_data(request):
    if "problem_id" not in request.resolver_match.kwargs:
        return {}
    problem_id = request.resolver_match.kwargs["problem_id"]
    revision_slug = request.resolver_match.kwargs["revision_slug"]
    problem, fork, revision = extract_revision_data(problem_id, revision_slug)
    revision_editable = revision.editable(request.user)
    master = revision.problem.get_upstream_fork()
    if revision.committed and fork is not None and fork != master:
        can_be_merged_with_master = revision.child_of(master.head)
        should_be_updated_from_master = not can_be_merged_with_master
    else:
        can_be_merged_with_master = False
        should_be_updated_from_master = False
    return {
        "problem": problem,
        "revision": revision,
        "fork": fork,
        "revision_slug": revision_slug,
        "revision_editable": revision_editable,
        "can_be_merged_with_master": can_be_merged_with_master,
        "should_be_updated_from_master": should_be_updated_from_master
    }