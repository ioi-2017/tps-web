from .utils import extract_revision_data


def revision_data(request):
    if "problem_id" not in request.resolver_match.kwargs:
        return {}
    problem_id = request.resolver_match.kwargs["problem_id"]
    revision_slug = request.resolver_match.kwargs["revision_slug"]
    problem, fork, revision = extract_revision_data(problem_id, revision_slug)
    revision_editable = revision.editable(request.user)
    return {
        "problem": problem,
        "revision": revision,
        "fork": fork,
        "revision_slug": revision_slug,
        "revision_editable": revision_editable,
    }