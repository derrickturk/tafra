import warnings
from decimal import Decimal

import numpy as np
from tafra import Tafra, object_formatter
import pandas as pd  # type: ignore

from typing import Dict, List, Any, Iterator

import pytest  # type: ignore
from unittest.mock import MagicMock


class TestClass:
    ...


class Series:
    name: str = 'x'
    values: np.ndarray = np.arange(5)
    dtype: str = 'int'


class DataFrame:
    _data: Dict[str, Series] = {'x': Series(), 'y': Series()}
    columns: List[str] = ['x', 'y']
    dtypes: List[str] = ['int', 'int']

    def __getitem__(self, column: str) -> Series:
        return self._data[column]

    def __setitem__(self, column: str, value: np.ndarray) -> None:
        self._data[column].values = value


print = MagicMock()

def build_tafra() -> Tafra:
    return Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })


def check_tafra(t: Tafra) -> bool:
    assert len(t._data) == len(t._dtypes)
    for c in t.columns:
        assert isinstance(t[c], np.ndarray)
        assert isinstance(t.data[c], np.ndarray)
        assert isinstance(t._data[c], np.ndarray)
        assert isinstance(t.dtypes[c], str)
        assert isinstance(t._dtypes[c], str)
        assert t._rows == len(t._data[c])
        pd.Series(t._data[c])

    _ = t.to_records()
    _ = t.to_list()
    _ = t.to_list()
    pd.DataFrame(t._data)

    return True

def test_constructions() -> None:
    with pytest.raises(TypeError) as e:
        t = Tafra()  # type: ignore # noqa

    with pytest.raises(ValueError) as e:
        t = Tafra({})  # type: ignore

    t = Tafra({'x': None})
    check_tafra(t)

    t = Tafra({'x': Decimal('1.23456')})
    check_tafra(t)

    t = Tafra({'x': np.array(1)})
    check_tafra(t)

    t = Tafra({'x': np.array([1])})
    check_tafra(t)

    t = Tafra({'x': [True, False]})
    check_tafra(t)

    t = Tafra({'x': 'test'})
    check_tafra(t)

    t.update_dtypes_inplace({'x': 'O'})
    check_tafra(t)

    t = Tafra(enumerate(np.arange(6)))
    check_tafra(t)

    with pytest.raises(ValueError) as e:
        t = Tafra({'x': np.array([1, 2]), 'y': np.array([3., 4., 5.])})

    def gen_values() -> Iterator[Dict[str, np.ndarray]]:
        yield {'x': np.arange(6)}
        yield {'y': np.arange(6)}

    t = Tafra(gen_values())
    check_tafra(t)

    t = build_tafra()
    t = t.update_dtypes({'x': 'float'})
    t.data['x'][2] = np.nan
    check_tafra(t)

    _ = tuple(t.to_records())
    _ = tuple(t.to_records(columns='x'))
    _ = tuple(t.to_records(columns=['x']))
    _ = tuple(t.to_records(columns=['x', 'y']))
    _ = tuple(t.to_records(cast_null=False))
    _ = tuple(t.to_records(columns='x', cast_null=False))
    _ = tuple(t.to_records(columns=['x'], cast_null=False))
    _ = tuple(t.to_records(columns=['x', 'y'], cast_null=False))

    _ = t.to_list()
    _ = t.to_list(columns='x')
    _ = t.to_list(columns=['x'])
    _ = t.to_list(columns=['x', 'y'])

    _ = t.to_list(inner=True)
    _ = t.to_list(columns='x', inner=True)
    _ = t.to_list(columns=['x'], inner=True)
    _ = t.to_list(columns=['x', 'y'], inner=True)

    _ = t.to_array()
    _ = t.to_array(columns='x')
    _ = t.to_array(columns=['x'])
    _ = t.to_array(columns=['x', 'y'])

    t = build_tafra()
    df = pd.DataFrame(t.data)
    _ = Tafra.from_series(df['x'])
    check_tafra(_)

    _ = Tafra.from_dataframe(df)
    check_tafra(_)

    _ = Tafra.as_tafra(df)
    check_tafra(_)

    _ = Tafra.as_tafra(df['x'])
    check_tafra(_)

    _ = Tafra.as_tafra(t)
    check_tafra(_)

    _ = Tafra.as_tafra({'x': np.array(1)})
    check_tafra(_)

    _ = Tafra.from_series(Series())
    check_tafra(_)

    _ = Tafra.as_tafra(Series())
    check_tafra(_)

    _ = Tafra.from_dataframe(DataFrame())  # type: ignore
    check_tafra(_)

    _ = Tafra.as_tafra(DataFrame())
    check_tafra(_)

    with pytest.raises(TypeError) as e:
        _ = Tafra(np.arange(6))

    with pytest.raises(TypeError) as e:
        _ = Tafra.as_tafra(np.arange(6))

def test_properties() -> None:
    t = build_tafra()
    _ = t.columns
    _ = t.rows
    _ = t.data
    _ = t.dtypes
    _ = t.size
    _ = t.ndim
    _ = t.shape

    with pytest.raises(ValueError) as e:
        t.columns = ['x', 'a']  # type: ignore

    with pytest.raises(ValueError) as e:
        t.rows = 3

    with pytest.raises(ValueError) as e:
        t.data = {'x': np.arange(6)}

    with pytest.raises(ValueError) as e:
        t.dtypes = {'x': 'int'}

    with pytest.raises(ValueError) as e:
        t.size = 3

    with pytest.raises(ValueError) as e:
        t.ndim = 3

    with pytest.raises(ValueError) as e:
        t.shape = (10, 2)

def test_views() -> None:
    t = build_tafra()
    _ = t.keys()
    _ = t.values()
    _ = t.items()
    _ = t.get('x')

def test_assignment() -> None:
    t = build_tafra()
    t['x'] = np.arange(6)
    t['x'] = 3
    t['x'] = 6
    t['x'] = 'test'
    t['x'] = list(range(6))
    check_tafra(t)

    with pytest.raises(ValueError) as e:
        t['x'] = np.arange(3)

def test_select() -> None:
    t = build_tafra()
    _ = t.select('x')
    _ = t.select(['x'])
    _ = t.select(['x', 'y'])

    with pytest.raises(ValueError) as e:
        _ = t.select('a')

def test_formatter() -> None:
    _ = str(object_formatter)

    t = Tafra({'x': Decimal(1.2345)})
    assert t._dtypes['x'] == 'float'
    assert t['x'].dtype == np.dtype(float)

    object_formatter['Decimal'] = lambda x: x.astype(int)
    t = Tafra({'x': Decimal(1.2345)})
    assert t._dtypes['x'] == 'int'
    assert t['x'].dtype == np.dtype(int)

    _ = str(object_formatter)

    for fmt in object_formatter:
        pass

    _ = object_formatter.copy()

    del object_formatter['Decimal']

    with pytest.raises(ValueError) as e:
        object_formatter['Decimal'] = lambda x: 'int'  # type: ignore

    _ = str(object_formatter)

def test_prints() -> None:
    t = build_tafra()
    _ = t.pformat()
    t.pprint()
    t.head(5)

    mock = MagicMock()
    mock.text = print
    t._repr_pretty_(mock, True)
    t._repr_pretty_(mock, False)

    _ = t._repr_html_()

def test_dunder() -> None:
    t = build_tafra()
    l = len(t)
    s = str(t)

def test_update() -> None:
    t = build_tafra()
    t2 = build_tafra()
    _ = t2.union(t)
    check_tafra(_)

    t2.union_inplace(t)
    check_tafra(t2)
    assert len(t2) == 2 * len(t)

    t2 = build_tafra()
    _ = t2.union(t)
    check_tafra(_)
    assert len(_) == len(t) + len(t2)

def test_update_dtypes() -> None:
    t = build_tafra()
    t.update_dtypes_inplace({'x': float})
    check_tafra(t)
    assert t['x'].dtype == 'float'
    assert isinstance(t['x'][0], np.float)

    t = build_tafra()
    _ = t.update_dtypes({'x': float})
    check_tafra(_)
    assert _['x'].dtype == 'float'
    assert isinstance(_['x'][0], np.float)

def test_rename() -> None:
    t = build_tafra()
    t.rename_inplace({'x': 'a'})
    assert 'a' in t.data
    assert 'a' in t.dtypes
    assert 'x' not in t.data
    assert 'x' not in t.dtypes
    check_tafra(t)

    t = build_tafra()
    _ = t.rename({'x': 'a'})
    assert 'a' in _.data
    assert 'a' in _.dtypes
    assert 'x' not in _.data
    assert 'x' not in _.dtypes
    check_tafra(_)

def test_delete() -> None:
    t = build_tafra()
    t.delete_inplace('x')
    assert 'x' not in t.data
    assert 'x' not in t.dtypes
    check_tafra(t)

    t = build_tafra()
    t.delete_inplace(['x'])
    assert 'x' not in t.data
    assert 'x' not in t.dtypes
    check_tafra(t)

    t = build_tafra()
    t.delete_inplace(['x', 'y'])
    assert 'x' not in t.data
    assert 'y' not in t.dtypes
    assert 'x' not in t.data
    assert 'y' not in t.dtypes
    check_tafra(t)

    t = build_tafra()
    _ = t.delete('x')
    assert 'x' not in _.data
    assert 'x' not in _.dtypes
    check_tafra(t)
    check_tafra(_)

    t = build_tafra()
    _ = t.delete(['x'])
    assert 'x' not in _.data
    assert 'x' not in _.dtypes
    check_tafra(t)
    check_tafra(_)

    t = build_tafra()
    _ = t.delete(['x', 'y'])
    assert 'x' not in _.data
    assert 'y' not in _.dtypes
    assert 'x' not in _.data
    assert 'y' not in _.dtypes
    check_tafra(t)
    check_tafra(_)

def test_iter_methods() -> None:
    t = build_tafra()
    for _ in t:
        pass

    for _ in t.iterrows():
        pass

    for _ in t.itercols():
        pass

    for _ in t.itertuples():
        pass

    for _ in t.itertuples(name='test'):
        pass

def test_groupby() -> None:
    t = build_tafra()
    gb = t.group_by(
        ['y', 'z'], {'x': sum}, {'count': len}
    )
    check_tafra(gb)

def test_groupby_iter_fn() -> None:
    t = build_tafra()
    gb = t.group_by(
        ['y', 'z'], {
            'x': sum,
            'new_x': (sum, 'x')
        }, {'count': len}
    )
    check_tafra(gb)

def test_transform() -> None:
    t = build_tafra()
    tr = t.transform(
        ['y', 'z'], {'x': sum}, {'id': max}
    )
    check_tafra(tr)

def test_iterate_by_attr() -> None:
    t = build_tafra()
    t.id = np.empty(t.rows, dtype=int)  # type: ignore
    t['id'] = np.empty(t.rows, dtype=int)
    for i, (u, ix, grouped) in enumerate(t.iterate_by(['y', 'z'])):
        t['x'][ix] = sum(grouped['x'])
        t.id[ix] = len(grouped['x'])  # type: ignore
        t['id'][ix] = max(grouped['x'])
    check_tafra(t)

def test_iterate_by() -> None:
    t = build_tafra()
    for u, ix, grouped in t.iterate_by(['y']):
        assert isinstance(grouped, Tafra)

def group_by_in_iterate_by() -> None:
    t = build_tafra()
    for u, ix, grouped in t.iterate_by(['y']):
        assert isinstance(grouped.group_by(['z'], {'x': sum}), Tafra)

def test_update_transform() -> None:
    t = build_tafra()
    t.update(t.transform(['y'], {}, {'id': max}))

    for u, ix, it in t.iterate_by(['y']):
        t['x'][ix] = it['x'] - np.mean(it['x'])
    check_tafra(t)

def test_transform_assignment() -> None:
    t = build_tafra()
    for u, ix, it in t.iterate_by(['y']):
        it['x'][0] = 9
    check_tafra(t)
    check_tafra(it)

def test_invalid_agg() -> None:
    t = build_tafra()
    with pytest.raises(ValueError) as e:
        gb = t.group_by(
            ['y', 'z'], {sum: 'x'}  # type: ignore
        )

    with pytest.raises(ValueError) as e:
        gb = t.group_by(
            ['y', 'z'], {}, {len: 'count'}  # type: ignore
        )

def test_map() -> None:
    t = build_tafra()
    _ = list(t.row_map(np.repeat, 6))
    _ = Tafra(t.col_map(np.repeat, name=True, repeats=6))
    _ = list(t.col_map(np.repeat, name=False, repeats=6))

def test_union() -> None:
    t = build_tafra()
    t2 = build_tafra()
    t.union_inplace(t2)
    check_tafra(t)

    t = build_tafra()
    t2 = build_tafra()
    t._dtypes['a'] = 'int'
    with pytest.raises(Exception) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2._dtypes['a'] = 'int'
    with pytest.raises(Exception) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t['a'] = np.arange(6)
    with pytest.raises(ValueError) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t2['a'] = np.arange(6)
    with pytest.raises(ValueError) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t.rename_inplace({'x': 'a'})
    with pytest.raises(TypeError) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t2.rename_inplace({'x': 'a'})
    with pytest.raises(TypeError) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t.update_dtypes_inplace({'x': float})
    with pytest.raises(TypeError) as e:
        t.union_inplace(t2)

    t = build_tafra()
    t2 = build_tafra()
    t2._dtypes['x'] = 'float'
    with pytest.raises(TypeError) as e:
        t.union_inplace(t2)

def test_slice() -> None:
    t = build_tafra()
    _ = t[:3]
    _['x'][0] = 0
    check_tafra(_)

    t = build_tafra()
    _ = t[slice(0, 3)]
    _['x'][0] = 7
    check_tafra(_)
    check_tafra(t)

    t = build_tafra()
    _ = t[:3].copy()
    _['x'][0] = 9
    check_tafra(_)
    check_tafra(t)

    t = build_tafra()
    _ = t[t['x'] <= 4]
    _['x'][1] = 15
    check_tafra(_)
    check_tafra(t)

    t = build_tafra()
    _ = t[2]
    _ = t[[1, 3]]
    _ = t[np.array([2, 4])]
    _ = t[[True, False, True, True, False, True]]
    _ = t[np.array([True, False, True, True, False, True])]
    _ = t[['x', 'y']]
    _ = t[('x', 'y')]
    _ = t[[True, 2]]
    check_tafra(_)
    check_tafra(t)


    with pytest.raises(IndexError) as e:
        _ = t[np.array([[1, 2]])]

    with pytest.raises(IndexError) as e:
        _ = t[[True, False]]

    with pytest.raises(IndexError) as e:
        _ = t[np.array([True, False])]

    with pytest.raises(IndexError) as e:
        _ = t[(1, 2)]  # noqa

    with pytest.raises(IndexError) as e:
        _ = t[(1, 2.)]  # type: ignore # noqa

    with pytest.raises(ValueError) as e:
        _ = t[['x', 2]]

    with pytest.raises(TypeError) as e:
        _ = t[{'x': [1, 2]}]  # type: ignore

    with pytest.raises(TypeError) as e:
        _ = t[TestClass()]  # type: ignore # noqa

    with pytest.raises(IndexError) as e:
        _ = t[[1, 2.]]  # type: ignore

    with pytest.raises(IndexError) as e:
        _ = t[np.array([1, 2.])]


def test_invalid_dtypes() -> None:
    t = build_tafra()
    with pytest.raises(Exception) as e:
        t.update_dtypes({'x': 'flot', 'y': 'st'})

def test_invalid_assignment() -> None:
    t = build_tafra()
    _ = build_tafra()
    _._data['x'] = np.arange(5)

    with pytest.raises(Exception) as e:
        _._update_rows()

    with pytest.raises(Exception) as e:
        _ = t.update(_)

    with pytest.raises(Exception) as e:
        t.update_inplace(_)

    with warnings.catch_warnings(record=True) as w:
        t['x'] = np.arange(6)[:, None]
        assert str(w[0].message) == '`np.squeeze(ndarray)` applied to set ndim == 1.'

    # with warnings.catch_warnings(record=True) as w:
    with warnings.catch_warnings(record=True) as w:
        t['x'] = np.atleast_2d(np.arange(6))
        assert str(w[0].message) == '`np.squeeze(ndarray)` applied to set ndim == 1.'

    with warnings.catch_warnings(record=True) as w:
        t['x'] = np.atleast_2d(np.arange(6)).T
        assert str(w[0].message) == '`np.squeeze(ndarray)` applied to set ndim == 1.'

    with warnings.catch_warnings(record=True) as w:
        t['x'] = np.atleast_2d(np.arange(6))
        assert str(w[0].message) == '`np.squeeze(ndarray)` applied to set ndim == 1.'

    with pytest.raises(Exception) as e:
        t['x'] = np.repeat(np.arange(6)[:, None], repeats=2, axis=1)

def test_datetime() -> None:
    t = build_tafra()
    t['d'] = np.array([np.datetime64(_, 'D') for _ in range(6)])
    t.update_dtypes({'d': '<M8[D]'})
    check_tafra(t)

    _ = tuple(t.to_records())

    _ = t.to_list()

def test_coalesce() -> None:
    t = Tafra({'x': np.array([1, 2, None, 4, None])})
    t['x'] = t.coalesce('x', [[1, 2, 3, None, 5], [None, None, None, None, 'five']])  # type: ignore
    t['y'] = t.coalesce('y', [[1, 2, 3, None, 5], [None, None, None, None, 'five']])  # type: ignore
    assert np.all(t['x'] != np.array(None))
    assert t['y'][3] == np.array(None)
    check_tafra(t)

    t = Tafra({'x': np.array([1, 2, None, 4, None])})
    t.coalesce_inplace('x', [[1, 2, 3, None, 5], [None, None, None, None, 'five']])  # type: ignore
    t.coalesce_inplace('y', [[1, 2, 3, None, 5], [None, None, None, None, 'five']])  # type: ignore
    assert np.all(t['x'] != np.array(None))
    assert t['y'][3] == np.array(None)
    check_tafra(t)

    t = Tafra({'x': np.array([None])})
    t.coalesce('x', [[1], [None]])  # type: ignore
    check_tafra(t)

def test_left_join_equi() -> None:
    l = Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.left_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([2, 2, 2, 3, 3, 3])
    })
    t = l.left_join(r, [('x', 'a', '=='), ('z', 'c', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        '_a': np.array([1, 1, 2, 2, 3, 3]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.left_join(r, [('x', 'a', '=='), ('x', '_a', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 2, 2, 3, 3]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.left_join(r, [('x', 'a', '<')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

def test_inner_join() -> None:
    l = Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.inner_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 2, 2, 3, 3]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.inner_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.inner_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })

    t = l.inner_join(r, [('x', 'a', '<=')], ['x', 'y', 'a', 'b'])
    check_tafra(t)


def test_cross_join() -> None:
    l = Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.cross_join(r)
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 2, 2, 3, 3]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.cross_join(r)
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })
    t = l.cross_join(r)
    check_tafra(t)

    r = Tafra({
        'a': np.array([1, 1, 1, 2, 2, 2]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })

    t = l.cross_join(r, select=['x', 'z', 'a', 'c'])
    check_tafra(t)

    with pytest.raises(IndexError) as e:
        t = l.cross_join(r, select=['x', 'z'])

    with pytest.raises(IndexError) as e:
        t = l.cross_join(r, select=['a', 'c'])

def test_left_join_invalid() -> None:
    l = Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })

    with pytest.raises(TypeError) as e:
        t = l.left_join(r, [('x', 'a', '===')], ['x', 'y', 'a', 'b'])

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6], dtype='float'),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })

    with pytest.raises(TypeError) as e:
        t = l.left_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])

    r = Tafra({
        'a': np.array([1, 2, 3, 4, 5, 6]),
        'b': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'c': np.array([0, 0, 0, 1, 1, 1])
    })

    l._dtypes['x'] = 'float'
    with pytest.raises(TypeError) as e:
        t = l.left_join(r, [('x', 'a', '==')], ['x', 'y', 'a', 'b'])
