from buildcloth.utils import is_function
import inspect
import hashlib
import logging

logger = logging.getLogger(__name__)

def mtime_check(target, dependency):
    if os.stat(target).st_mtime < os.stat(dependency).st_mtime:
        return True
    else:
        return False

def md5_file_check(file, block_size=2**20):
    md5 = hashlib.md5()

    with open(file, 'rb') as f:
        for chunk in iter(lambda: f.read(128*md5.block_size), b''):
            md5.update(chunk)

    return md5.hexdigest()

def hash_check(target, dependency):
    if md5_file_check(target) != md5_file_check(dependency):
        return True
    else:
        return False

class DependencyChecks(object):
    def __init__(self, check=None):
        members = inspect.getmembers(self, inspect.ismethod)

        self.checks = {}

        for member in members:
            if is_function(member[1]):
                if member[1].__name__.startswith('_'):
                    pass
                else:
                    self.checks[member[0]] = member

        if check is None and 'mtime' in self.checks:
            self.check = 'mtime'
        else:
            self.check = members[0][0]

    @property
    def check_method(self):
        return self.check

    @check_method.setter
    def check_method(self, value):
        if self.check is None:
            self.check = 'mtime'
        elif self.check in self.checks:
            self.check = value
        else:
            raise Exception

    def force(self, target, dependency):
        return True

    def mtime(self, target, dependency):
        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if mtime_check(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return mtime_check(target, dependency)

    def hash(self, target, dependency):
        if not os.path.exists(target) and not os.path.islink(target):
            return True

        if isinstance(dependency, list):
            for dep in dependency:
                if hash_check(target, dep) is True:
                    return True
                else:
                    continue
        else:
            return hash_check(target, dependency)

    def check(self, target, dependency):
        logger.debug('running dependency check ({0}), of target {1} on dependency {2}'.format(self.check, target, dependency))
        test = self.checks[self.check](target, dependency)
        logger.info('rebuild check {0} result: {1} for target {2}'.format(self.check, test, tareget))

        return test
