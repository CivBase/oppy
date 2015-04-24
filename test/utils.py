import unittest
from mock import patch


DATA_BASE = 'abcdefghijklmnopqrstuvwxyz'


patch_object = lambda *args, **kwargs: patch.object(
    *args, autospec=True, **kwargs)


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.addCleanup(patch.stopall)

    def gen_data(self, size):
        return (DATA_BASE * (size / len(DATA_BASE)) +
                DATA_BASE[:(size % len(DATA_BASE))])


# this code gleefully stolen from jsbueno on stack overflow
# http://stackoverflow.com/questions/9757299/python-testing-an-abstract-base-class
def concrete(abclass):
    """
    >>> import abc
    >>> class Abstract(metaclass=abc.ABCMeta):
    ...     @abc.abstractmethod
    ...     def bar(self):
    ...        return None

    >>> c = concrete(Abstract)
    >>> c.__name__
    'dummy_concrete_Abstract'
    >>> c().bar() # doctest: +ELLIPSIS
    (<abc_utils.Abstract object at 0x...>, (), {})
    """
    if '__abstractmethods__' not in abclass.__dict__:
        return abclass

    new_dict = abclass.__dict__.copy()
    for abstractmethod in abclass.__abstractmethods__:
        # replace each abc method or property with an identity function:
        new_dict[abstractmethod] = lambda x, *args, **kw: (x, args, kw)

    # create a new class, with the overridden ABCs
    return type('concrete_%s' % abclass.__name__, (abclass,), new_dict)
