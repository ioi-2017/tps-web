# coding=utf-8

from problems.views.generics import RevisionObjectView
from django.shortcuts import render
from problems.tasks import AnalysisGeneration
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
import os


__all__ = ["AnalysisView", "AnalyzeView", "AnalysisGenerateView"]


class AnalysisView(RevisionObjectView):
    repo_dir = '/home/kiarash/Desktop/worktree_test/'
    commit_id = '59fb062'
    out_dir = '/home/kiarash/Desktop/fld'

    def get(self, request, *args, **kwargs):
        output_file = os.path.join(self.out_dir, 'out.txt')
        error_file = os.path.join(self.out_dir, 'err.txt')

        if not os.path.exists(output_file):
            output = None
        else:
            with open(output_file) as f:
                output = ''.join(list(f.readline()))

        if not os.path.exists(error_file):
            errors = None
        else:
            with open(error_file) as f:
                errors = ''.join(list(f.readline()))

        return render(request, 'problems/analysis.html', context={'output': output,
                                                                  'errors': errors})


class AnalyzeView(RevisionObjectView):
    def post(self, request, problem_id, revision_slug):
        # TODO: analyze
        return HttpResponseRedirect(reverse("problems:analysis", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        }))


class AnalysisGenerateView(RevisionObjectView):
    repo_dir = '/home/kiarash/Desktop/worktree_test/'
    commit_id = '59fb062'
    out_dir = '/home/kiarash/Desktop/fld'

    def post(self, request, problem_id, revision_slug):
        id = AnalysisGeneration().delay(self.repo_dir,
                                        self.commit_id,
                                        self.out_dir).id

        return HttpResponseRedirect(reverse("problems:analysis", kwargs={
            "problem_id": problem_id,
            "revision_slug": revision_slug
        }))
