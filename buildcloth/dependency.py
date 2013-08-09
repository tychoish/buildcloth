from buildcloth.utils import is_function
import inspect
import hashlib

class DependencyChecks(object):


    @property
    def check(self):
        return self._check

    @check.setter
    def check(self, value):
        if check is None:
            self._check = 'mtime'
        elif check in self.checks:
            self._check = check
        else:
            raise Exception

    def __init__(self, check=None):
        members = inspect.getmembers(self, inspect.ismethod)
        self.checks = {}

        for member in members:
            if is_function(member):
                if member[0].__name__.startswith('_'):
                    pass
                else:
                    self.checks[member.__name__] = member

        self.check = check

    @staticmethod
    def _mtime(target, dependency):
        if os.stat(target).st_mtime < os.stat(dependency).st_mtime:
            return True
        else:
            return False

    @staticmethod
    def mtime(target, dependency):
        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if self._mtime(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return self._mtime(target, dependency)

    @staticmethod
    def _md5_file(file, block_size=2**20):
        md5 = hashlib.md5()

        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(128*md5.block_size), b''):
                md5.update(chunk)

        return md5.hexdigest()

    @staticmethod
    def _hash(target, dependency):
        if self._md5_file(target) != self._md5_file(dependency):
            return True
        else:
            return False

    @staticmethod
    def force(target, dependency):
        pass

    @staticmethod
    def hash(target, dependency):
        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if self._hash(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return self._hash(target, dependency)

    def check(self, target, dependency):
        self.checks[self.check](target, dependency)
