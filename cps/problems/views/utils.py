from django.shortcuts import render


def render_for_problem(request, problem, revision, template_name, context=None, *args, **kwargs):
    if context is None:
        context = {}
    context["problem"] = problem
    context["revision"] = revision
    context["revision_slug"] = request.resolver_match.kwargs["revision_slug"]
    return render(request, template_name, context)
