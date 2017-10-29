# coding=utf-8
from django.contrib import messages

from problems.views.generics import RevisionObjectView, ProblemObjectView
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
import os
from ansi2html import Ansi2HTMLConverter



__all__ = ["AnalysisView", "AnalyzeView", "AnalysisGenerateView"]


class AnalysisView(ProblemObjectView):

    def get(self, request, *args, **kwargs):
        def get_content(path):
            if not os.path.exists(path):
                content = ""
            else:
                with open(path) as f:
                    content = '\n'.join(list(f.readlines()))
            converted = conv.convert(content, full=False)
            return converted

        conv = Ansi2HTMLConverter(inline=True)

        out_dir = self.revision.get_storage_path()
        verify_output_file = get_content(os.path.join(out_dir, 'verify_out.txt'))
        verify_error_file = get_content(os.path.join(out_dir, 'verify_err.txt'))
        generate_output_file = get_content(os.path.join(out_dir, 'gen_out.txt'))
        generate_error_file = get_content(os.path.join(out_dir, 'gen_err.txt'))

        return render(request, 'problems/analysis.html', context={
            'verify_out': verify_output_file,
            'verify_err': verify_error_file,
            'generate_out': generate_output_file,
            'generate_err': generate_error_file,
        })


class AnalyzeView(ProblemObjectView):
    def post(self, request, problem_code, revision_slug):
        self.revision.verify()

        messages.success(request, _("Verification started"))
        return HttpResponseRedirect(reverse("problems:analysis", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        }))


class AnalysisGenerateView(ProblemObjectView):

    def post(self, request, problem_code, revision_slug):
        self.revision.generate_testcases()

        messages.success(request, _("Generation started"))

        return HttpResponseRedirect(reverse("problems:analysis", kwargs={
            "problem_code": problem_code,
            "revision_slug": revision_slug
        }))
