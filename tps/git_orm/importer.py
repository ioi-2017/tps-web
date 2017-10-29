import imp
import sys

from git_orm import transaction, GitError


PATH_PREFIX = 'git-import:'


def with_transaction(fn):
    def _inner(*args, **kwargs):
        try:
            with transaction.wrap():
                return fn(*args, **kwargs)
        except GitError:
            raise ImportError()
    return _inner


# See PEP 302 for the importer protocol specification
class GitImporter:
    def __init__(self, path):
        if not path.startswith(PATH_PREFIX):
            raise ImportError()
        self.path = path[len(PATH_PREFIX):].rstrip('/')

    @with_transaction
    def get_filename(self, fullname, prefix=PATH_PREFIX):
        trans = transaction.current()
        shortname = fullname.rpartition('.')[2]
        base = '/'.join([self.path, shortname])
        for ext in ('/__init__.py', '.py'):
            filename = base + ext
            if trans.exists(filename.strip('/').split('/')):
                if prefix:
                    filename = prefix + filename
                return filename
        raise ImportError()

    def is_package(self, fullname):
        return self.get_filename(fullname).endswith('/__init__.py')

    @with_transaction
    def get_source(self, fullname):
        path = self.get_filename(fullname, prefix=None).strip('/').split('/')
        trans = transaction.current()
        return trans.get_blob(path).decode('utf-8') + '\n'

    @with_transaction
    def get_code(self, fullname):
        source = self.get_source(fullname)
        filename = self.get_filename(fullname)
        return compile(source, filename, 'exec')

    def find_module(self, fullname, path=True):
        try:
            self.get_filename(fullname)
        except ImportError:
            return None
        return self

    def load_module(self, fullname):
        with transaction.wrap():
            code = self.get_code(fullname)
            is_pkg = self.is_package(fullname)
        is_reload = fullname in sys.modules
        mod = sys.modules.setdefault(fullname, imp.new_module(fullname))
        mod.__file__ = code.co_filename
        mod.__loader__ = self
        if is_pkg:
            path = '/'.join(
                [PATH_PREFIX, self.path, fullname.rpartition('.')[2]])
            mod.__path__ = [path]
            mod.__package__ = fullname
        else:
            mod.__package__ = fullname.rpartition('.')[0]
        try:
            exec(code, mod.__dict__)
        except:
            if not is_reload:
                del sys.modules[fullname]
            raise
        return mod
