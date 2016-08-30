from django.shortcuts import render


def render_for_problem(request, problem, revision, template_name, context=None, *args, **kwargs):
    if context is None:
        context = {}
    context["problem"] = problem
    context["revision"] = problem
    return render(request, template_name, context)
