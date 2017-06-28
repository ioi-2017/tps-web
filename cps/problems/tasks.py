# coding=utf-8

from tasks.tasks import CeleryTask
import logging
import os
import tempfile
import shutil


logger = logging.getLogger(__name__)


class AnalysisGeneration(CeleryTask):
    def validate_dependencies(self, *args, **kwargs):
        return True

    def execute(self, repo_dir, commit_id, out_dir):
        git_dir = os.path.join(repo_dir, '.git')
        tempdir = tempfile.mkdtemp()
        logger.warning('temp directory at %s' % tempdir)

        os.system('git --git-dir="%s" ' % git_dir +
                  '--work-tree="%s" ' % repo_dir +
                  'worktree add %s %s' % (tempdir, commit_id))

        out_file = os.path.join(out_dir, 'out.txt')
        err_file = os.path.join(out_dir, 'err.txt')

        # TODO: run the generator; this is just for test:
        tests_src = os.path.join(tempdir, 'tests')
        os.system('mkdir {0}; echo hello > {1}; sleep 5; echo bye >> {1} 2> {2}'.format
                  (tests_src, out_file, err_file))

        tests_src = os.path.join(tempdir, 'tests')
        tests_dst = os.path.join(out_dir, 'tests')
        if os.path.exists(tests_dst):
            shutil.rmtree(tests_dst)
        shutil.copytree(tests_src, tests_dst)

        # TODO: remove the directory and then prune the worktree
        # shutil.rmtree(tempdir)
        # os.system('git --git-dir="%s" ' % git_dir +
        #           '--work-tree="%s" ' % repo_dir +
        #           'worktree prune')
