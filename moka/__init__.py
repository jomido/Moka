import unittest
import string
import operator as op


class Blank:
    pass

_ = Blank


class List(list):
    """
    List is a wrapper around the builtin list.
    It provides a chainable interface and enhances it with
    these methods:

    do
    tee
    map
    keep
    rem
    some/has
    all
    count
    find
    empty
    attr
    item
    invoke

    Todo:
    reduce/fold
    """

    @staticmethod
    def _proxy(method_name):
        """
        Make builtin list methods return self instead of None.
        """
        def wrap(self, *args, **kwargs):
            inst = List(self)
            getattr(list, method_name)(inst, *args, **kwargs)
            return inst

        setattr(List, method_name, wrap)

    def _moka_assign(self, items):
        """
        Assign enumerable to the list and return
        self instead of None
        """
        self[:] = items
        return self

    def _f(self, f, *args, **kwargs):
        """
        Parse arguments and return a new function.

        If there's no argument, return a function that call f.
        If there are arguments, use the partial syntax and bind
          the parameters to f.
        """
        if not args and not kwargs:
            return lambda x: f(x)

        if Blank not in args:
            return lambda x: f(x, *args, **kwargs)

        args = list(args)
        pos = args.index(Blank)

        def tmp(x):
            args[pos] = x
            return f(*args, **kwargs)
        return tmp

    def clone(self):
        """
        Returns a copy of the List
        """
        return List(self)

    def tee(self, *args, **kwargs):
        """
        Like 'do', but return self instead of the result.
        """
        self.last_value = self._f(*args, **kwargs)(self)
        return self

    def do(self, *args, **kwargs):
        """
        Call a method and pass 'self' as first parameter.
        List(..).do(some_method) <=> some_method(List(...))
        """
        return self._f(*args, **kwargs)(self)

    def map(self, *args, **kwargs):
        """
        List([1,2]).map(fn) <=> map(fn, [1,2])
        """
        f = self._f(*args, **kwargs)
        return self._moka_assign(f(x) for x in self)

    def invoke(self, name, *args, **kwargs):
        """
        List([1,2]).invoke('__str__')
        <=>
        List([1,2]).map(lambda x: x.__str__())
        """
        return self.map(lambda x: getattr(x, name)(*args, **kwargs))

    def attr(self, attr):
        """
        List([obj]).attr('attr')
        <=>
        List([obj]).map(lambda x: x.attr)
        """
        return self.map(lambda x: getattr(x, attr))

    def item(self, item):
        """
        List([obj]).item('item')
        <=>
        List([obj]).map(lambda x: x[item])
        """
        return self.map(lambda x: x[item])

    def empty(self, *args, **kwargs):
        """
        Returns True if the list is empty.
        A predicate can be given to specify 'what is True'.
        List(..).empty(lambda x: x == None)
        """
        if not args and not kwargs:
            return not bool(self)
        else:
            f = self._f(*args, **kwargs)

            for x in self:
                if f(x):
                    continue
                return False
            return True

    def count(self, *args, **kwargs):
        """
        Returns the number of elements.
        Can take a function to specify 'what to count'.
        List(..).count(lambda x: x > 0)
        """
        if not args and not kwargs:
            return len(self)
        else:
            return (self
                     .clone()
                     .keep(*args, **kwargs)
                     .count())

    def find(self, *args, **kwargs):
        """
        Return the first element that matches 'predicate'
        or returns None.
        List(..).find(lambda x: x == 3)
        """
        f = self._f(*args, **kwargs)

        for x in self:
            if f(x):
                return x

    def keep(self, *args, **kwargs):
        """
        Select elements matching a predicate.
        filter(..., [1,2]) <=> List([1,2]).keep(...)
        """
        f = self._f(*args, **kwargs)
        return self._moka_assign(x for x in self if f(x))

    def rem(self, *args, **kwargs):
        """
        Like 'keep' but remove elements matching the predicate.
        """
        f = self._f(*args, **kwargs)
        return self._moka_assign(x for x in self if not f(x))

    def some(self, *args, **kwargs):
        """
        Return True if at least one item match a predicate.
        List([1,2]).some(lambda x == 2)
        <=>
        any(x == 2 for x in [1,2])
        """
        f = self._f(*args, **kwargs)

        for x in self:
            if f(x):
                return True

        return False

    def all(self, *args, **kwargs):
        """
        Return True if all items match a predicate.
        List([2,2]).all(lambda x == 2)
        <=>
        all(x == 2 for x in [2,2])
        """
        f = self._f(*args, **kwargs)

        for x in self:
            if not f(x):
                return False

        return True

    # aliases
    has = some

    def __getslice__(self, *args, **kwargs):
        """
        List(..)[2:4] returns moka.List instead of builtin list.
        """
        return List(list.__getslice__(self, *args, **kwargs))


(List(['append', 'extend', 'sort', 'reverse', 'insert'])
   .map(List._proxy))


class ListTest(unittest.TestCase):

    def setUp(self):
        self.seq = List(range(1, 6))

    def test_is_list(self):
        self.assertEqual(range(1, 6), self.seq)

    def test_map(self):
        self.assertEqual(self.seq.map(lambda x: x * 2), [2, 4, 6, 8, 10])

    def test_keep(self):
        self.assertEqual(self.seq.clone().keep(lambda x: x < 3), [1, 2])
        self.assertEqual(self.seq.clone().keep(op.eq, 3), [3])
        self.assertEqual(self.seq.keep(op.eq, 3), [3])

    def test_rem(self):
        self.assertEqual(self.seq.clone().rem(lambda x: x < 3), [3, 4, 5])
        self.assertEqual(self.seq.rem(op.eq, 3), [1, 2, 4, 5])

    def test_mix(self):
        r = (self.seq
                 .map(lambda x: x * 2)
                 .rem(lambda x: x < 5)
                 .keep(lambda x: x % 2 == 0)
                 .rem(op.eq, 6))

        self.assertEqual(r, [8, 10])

    def test_self(self):
        self.assertEqual(
            (self.seq
             .clone()
             .map(lambda x: x * 2)
             .rem(lambda x: x < 5)
             .keep(lambda x: x % 2 == 0)
             .rem(op.eq, 6)
             .tee(self.assertEqual, [8, 10])),
             [8, 10])

        (self.seq
              .keep(lambda x: x > 4)
              .tee(self.assertEqual, [5])
              .last_value) = [5]

    def test_some(self):
        self.assert_(self.seq.some(lambda x: x < 3))

        self.assert_(self.seq.some(op.eq, 4))

        self.assertFalse(List([1, 1, 1]).some(op.eq, 2))

        self.assertFalse(self.seq.some(lambda x: x < 1))

    def test_has(self):
        self.assert_(List(range(10)).has(op.eq, 5))
        self.assert_(List(range(10)).has(lambda x: x in [1, 2]))

    def test_find(self):
        self.assertEqual(self.seq.find(op.eq, 3), 3)

        self.assertEqual(self.seq.find(lambda x: x == 3), 3)

        self.assertEqual(self.seq.find(lambda x: x != 3), 1)

    def test_all(self):
        self.assertFalse(self.seq.all(lambda x: x < 3))

        self.assertFalse(self.seq.all(op.eq, 4))

        self.assert_(List([1, 1, 1]).all(op.eq, 1))

        self.assert_(self.seq.all(lambda x: x < 10))

    def test_append(self):
        self.assertEqual(self.seq.append(6), [1, 2, 3, 4, 5, 6])
        self.assertEqual(self.seq, [1, 2, 3, 4, 5])

    def test_extend(self):
        self.assertEqual(self.seq.extend([1, 2]), [1, 2, 3, 4, 5, 1, 2])
        self.assertEqual(self.seq, [1, 2, 3, 4, 5])

    def test_insert(self):
        self.assertEqual(self.seq.insert(0, 4), [4, 1, 2, 3, 4, 5])
        self.assertEqual(self.seq, [1, 2, 3, 4, 5])

    def test_getslice(self):
        self.assertEqual(self.seq[:2], [1, 2])
        self.assertEqual(type(self.seq[:1]), List)
        self.assertEqual(self.seq[:2].map(lambda x: x * 2), [2, 4])

    def test_setslice(self):
        self.seq[2:] = [9, 9]
        self.assertEqual(self.seq, [1, 2, 9, 9])
        self.assertEqual(type(self.seq), List)

    def test_reverse(self):
        self.assertEqual(self.seq.reverse(), [5, 4, 3, 2, 1])
        self.assertEqual(type(self.seq), List)

    def test_sort(self):
        self.seq = List([1, 4, 2, 5, 3])
        self.assertEqual(self.seq.sort(), [1, 2, 3, 4, 5])
        self.assertEqual(type(self.seq), List)

    def test_count(self):
        self.assertEqual(self.seq.count(), 5)
        self.assertEqual(self.seq.count(op.eq, 3), 1)
        self.assertEqual(self.seq.count(lambda x: x in [1, 3]), 2)

    def test_empty(self):
        self.assertFalse(self.seq.empty())
        self.assertTrue(List().empty())
        self.assertTrue(List([None, 0, 0]).empty(lambda x: x in [None, 0]))
        self.assertFalse(List([None, [], 0]).empty(lambda x: x in [None, 0]))

    def test_attr(self):
        self.assertEqual(self.seq.attr('real'), [1, 2, 3, 4, 5])
        self.assertEqual(self.seq.clone().attr('imag'), [0, 0, 0, 0, 0])
        self.assertEqual(self.seq.clone().map(op.attrgetter('real')),
                         [1, 2, 3, 4, 5])

    def test_item(self):
        self.assertEqual(List([dict(a=1), dict(a=2)]).item('a'), [1, 2])
        (List([dict(a=1), dict(a=2)])
           .map(op.itemgetter('a'))
           .do(self.assertEqual, [1, 2]))

    def test_invoke(self):
        self.assertEqual(self.seq.invoke('__str__'),
                         ['1', '2', '3', '4', '5'])
        (self.seq
             .map(op.methodcaller('__str__'))
             .do(self.assertEqual, ['1', '2', '3', '4', '5']))

    def test_partial(self):
        (List('7')
          .map(string.zfill, 3)
          .do(self.assertEqual, ['007']))

    def test_partial_blank(self):
        (List([3])
          .map(string.zfill, '7', _)
          .do(self.assertEqual, ['007']))

    def test_kw_in(self):
        (List([1, 2])
          .keep(op.contains, [2, 3, 4], _)
          .do(self.assertEqual, [2]))

    def test_kw_gt(self):
        (List([1, 2])
          .keep(op.gt, 1)
          .do(self.assertEqual, [2]))

    def test_kw_ge(self):
        (List([1, 2])
          .keep(op.ge, 1)
          .do(self.assertEqual, [1, 2]))

    def test_kw_lt(self):
        (List([1, 2])
          .keep(op.lt, 2)
          .do(self.assertEqual, [1]))

    def test_kw_le(self):
        (List([1, 2])
          .keep(op.le, 2)
          .do(self.assertEqual, [1, 2]))

    def test_savelist(self):
        x = List(range(1, 5))
        x.keep(op.gt, 2)
        x.keep(op.lt, 4)
        self.assertEqual(x, [3])


class Dict(dict):
    """
    map x,y -> new y
    map()
    keep(),
    rem
    some/has
    all
    count () = len, (x|f)
    empty () == [], (f) -> x in [0, None]..
    Do do(lambda seq: ...)
    invoke

    wrapper: clear(), fromkeys()
       (and last_value = the result of the last operation)
       also do will pass extra arg. so do(self.assertTrue, ...)
       = do(lambda seq: self.assertTrue(seq, ...)
       = self.assertTrue(seq, ...)
    """

    @staticmethod
    def _proxy(method_name):
        def wrap(self, *args, **kwargs):
            inst = Dict(self)
            getattr(dict, method_name)(inst, *args, **kwargs)
            return inst

        setattr(Dict, method_name, wrap)

    def _f(self, *args, **kwargs):
        args = list(args)

        # shortcut to use operator module.
        if kwargs:
            k, v = kwargs.items()[0]
            fn = getattr(op, k)
            return lambda _, y: fn(y, v)

        f = args.pop(0)

        # if Blank in args:
        #     pos = args.index(Blank)
        # else:
        #     args.insert(0, None)
        #     pos = 0

        args.insert(0, None)
        args.insert(0, None)
        args = list(args)

        def tmp(x, y):
            args[0] = x
            args[1] = y
            return f(*args, **kwargs)

        return tmp

    def __init__(self, *args, **kwargs):
        self._moka_save = False
        dict.__init__(self, *args, **kwargs)

    def _moka_assign(self, items):
        if self._moka_save:
            pass
        else:
            return Dict(items)

    def map(self, *args, **kwargs):
        f = self._f(*args, **kwargs)
        return self._moka_assign(f(x, y) for x, y in self.items())

    def keep(self, *args, **kwargs):
        f = self._f(*args, **kwargs)
        return self._moka_assign((x, y) for x, y in self.items()
                                        if f(x, y))

    def rem(self, *args, **kwargs):
        f = self._f(*args, **kwargs)
        return self._moka_assign((x, y) for x, y in self.items()
                                        if not f(x, y))

    def all(self, *args, **kwargs):
        f = self._f(*args, **kwargs)

        for x, y in self.items():
            if not f(x, y):
                return False

        return True

    def some(self, *args, **kwargs):
        f = self._f(*args, **kwargs)

        for x, y in self.items():
            if f(x, y):
                return True

        return False

    def count(self, *args, **kwargs):
        if not args and not kwargs:
            return len(self)
        else:
            return len(Dict(self).keep(*args, **kwargs))

    def do(self, function, *args, **kwargs):
        self.last_value = function(self, *args, **kwargs)
        return self

    def copy(self):
        return Dict(self)

    @classmethod
    def fromkeys(cls, *args, **kwargs):
        return Dict(dict.fromkeys(*args, **kwargs))

    def empty(self, *args, **kwargs):
        if not args and not kwargs:
            return len(self) == 0
        else:
            return len(Dict(self).rem(*args, **kwargs)) == 0


List(['update', 'clear']).map(Dict._proxy)


class DictTest(unittest.TestCase):

    def setUp(self):
        self.seq = Dict(a=1, b=2, c=3)

    def test_is_dict(self):
        self.assertEqual(self.seq, dict(a=1, b=2, c=3))

    def test_map(self):
        self.assertEqual(self.seq.map(lambda x, y: (x, x)),
                         dict(a='a', b='b', c='c'))

        self.assertEqual(self.seq.map(lambda x, y: (x, y * 2)),
                         dict(a=2, b=4, c=6))

    def test_keep(self):
        self.assertEqual(self.seq.keep(eq=3), dict(c=3))
        self.assertEqual(self.seq.keep(lambda x, y: y > 2), dict(c=3))

    def test_rem(self):
        self.assertEqual(self.seq.rem(eq=3), dict(a=1, b=2))
        self.assertEqual(self.seq.rem(lambda x, y: y > 2), dict(a=1, b=2))

    def test_update(self):
        self.assertEqual(self.seq.update(dict(a=5, d=1)),
                         dict(a=5, b=2, c=3, d=1))
        self.assertTrue(isinstance(self.seq.update(dict(a=5, d=1)), Dict))

    def test_clear(self):
        self.assertEqual(self.seq.clear(), {})
        self.assertTrue(isinstance(self.seq.clear(), Dict))

    def test_copy(self):
        a = []

        self.assertEqual(id(Dict(a=a).copy()['a']), id(a))
        self.assertEqual(self.seq.copy(), self.seq)
        self.assertTrue(isinstance(self.seq.copy(), Dict))

    def test_fromkeys(self):
        self.assertTrue(isinstance(Dict.fromkeys([1, 2, 3]), Dict))
        self.assertEqual(Dict.fromkeys([1, 2, 3]),
                         {1: None, 2: None, 3: None})

    def test_all(self):
        self.assertTrue(self.seq.all(lambda x, y: y in [1, 2, 3]))
        self.assertTrue(self.seq.update(a=2, c=2).all(eq=2))
        self.assertFalse(self.seq.all(eq=4))

    def test_some(self):
        self.assertTrue(self.seq.some(eq=2))
        self.assertFalse(self.seq.some(eq=4))
        self.assertTrue(self.seq.some(lambda x, y: y == 3))

    def test_count(self):
        self.assertEqual(self.seq.count(), 3)
        self.assertEqual(self.seq.count(eq=3), 1)
        self.assertEqual(self.seq.count(lambda x, y: y in [1, 3]), 2)

    def test_empty(self):
        self.assertFalse(self.seq.empty())
        self.assertTrue(Dict().empty())
        self.assertTrue(Dict(zip([1, 2, 3], [None, 0, 0]))
                          .empty(lambda x, y: y in [None, 0]))

        self.assertFalse(Dict(zip([1, 2, 3], [None, [], 0]))
                          .empty(lambda x, y: y in [None, 0]))

    def test_do(self):
        self.assertEqual(
            (self.seq
             .map(lambda x, y: (x, y * 2))
             .rem(eq=4)
             .do(self.assertEqual, dict(a=2, c=6))),
             dict(a=2, c=6))

        self.assertEqual(self.seq.do(lambda self: 1 + 1).last_value, 2)



if __name__ == '__main__':
    unittest.main()
