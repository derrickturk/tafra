"""
Tafra: the innards of a dataframe

Author
------
Derrick W. Turk
David S. Fulford

Notes
-----
Created on April 25, 2020
"""

import warnings
from collections import OrderedDict
import dataclasses as dc

import numpy as np
from pandas import DataFrame # just for mypy...

from typing import Any, Callable, Dict, List, Iterable, Tuple, Optional, Union
from typing import cast

InitAggregation = Dict[
    str,
    Union[
        Callable[[np.ndarray], Any],
        Tuple[Callable[[np.ndarray], Any], str]
    ]
]


TAFRA_TYPE = {
    'int': lambda x: x.astype(int),
    'float': lambda x: x.astype(float),
    'bool': lambda x: x.astype(bool),
    'str': lambda x: x.astype(str),
    'date': lambda x: x.astype('datetime64'),
    'object': lambda x: x.astype(object),
}

RECORD_TYPE = {
    'int': lambda x: int(x),
    'float': lambda x: float(x),
    'bool': lambda x: bool(x),
    'str': lambda x: str(x),
    'date': lambda x: x.strftime(r'%Y-%m-%d'),
    'object': lambda x: str(x),
}


def _real_has_attribute(obj: object, attr: str) -> bool:
    try:
        obj.__getattribute__(attr)
        return True
    except AttributeError:
        return False

@dc.dataclass
class Tafra:
    """The innards of a dataframe.
    """
    _data: Dict[str, np.ndarray]
    _dtypes: Dict[str, str] = dc.field(default_factory=dict)

    def __post_init__(self):
        rows = None
        for column, values in self._data.items():
            if rows is None:
                rows = len(values)
            else:
                if rows != len(values):
                    raise ValueError('`Tafra` must have consistent row counts.')

        if self._dtypes:
            self.update_types()
        else:
            self._dtypes = {}
        self.coalesce_types()

    def update_types(self, dtypes: Optional[Dict[str, Any]] = None) -> None:
        """Apply new dtypes or update dtype `dict` for missing keys.
        """
        if dtypes is not None:
            dtypes = self._validate_types(dtypes)
            self._dtypes.update(dtypes)

        for column in self._dtypes.keys():
            if self._format_type(self._data[column].dtype) != self._dtypes[column]:
                self._data[column] = self._apply_type(self._dtypes[column], self._data[column])

    def coalesce_types(self) -> None:
        for column in self._data.keys():
            if column not in self._dtypes:
                self._dtypes[column] = self._format_type(self._data[column].dtype)

    def __getitem__(self, item: Union[str, slice, np.ndarray]):
        # type is actually Union[np.ndarray, 'Tafra'] but mypy goes insane
        if isinstance(item, str):
            return self._data[item]

        elif isinstance(item, slice):
            return self._slice(item)

        elif isinstance(item, np.ndarray):
            return self._index(item)

        else:
            raise ValueError(f'Type {type(item)} not supported.')

    def __getattr__(self, attr: str) -> np.ndarray:
        return self._data[attr]

    def __setitem__(self, item: str, value: Union[np.ndarray, Iterable]):
        value = self._validate(value)
        self._data[item] = value
        self._dtypes[item] = self._format_type(value.dtype)

    def __setattr__(self, attr: str, value: Union[np.ndarray, Iterable]):
        if not (_real_has_attribute(self, '_init') and self._init):
            object.__setattr__(self, attr, value)
            return

        value = self._validate(value)
        self._data[attr] = value
        self._dtypes[attr] = self._format_type(value.dtype)

    def _validate(self, value: Union[np.ndarray, Iterable]) -> np.ndarray:
        if not isinstance(value, np.ndarray):
            value = np.asarray(value)

        # is it an ndarray now?
        if not isinstance(value, np.ndarray):
            raise ValueError('`Tafra` only supports assigning `ndarray`.')

        if value.ndim > 1:
            sq_value = value.squeeze()
            if sq_value.ndim > 1:
                raise ValueError('`ndarray` or `np.squeeze(ndarray)` must have ndim == 1.')
            elif sq_value.ndim == 1:
                # if value was a single item, squeeze returns zero length item
                warnings.warn('`np.squeeze(ndarray)` applied to set ndim == 1.')
                warnings.resetwarnings()
                value = sq_value
            else:
                assert 0, 'ndim <= 0, unreachable'

        if len(value) != self.rows:
            raise ValueError(
                '`Tafra` must have consistent row counts.\n'
                f'This `Tafra` has {self.rows} rows. Assigned np.ndarray has {len(value)} rows.')

        return value

    def _validate_types(self, dtypes: Dict[str, Any]) -> Dict[str, str]:
        msg = ''
        _dtypes = {}
        for column, _dtype in dtypes.items():
            _dtypes[column] = self._format_type(_dtype)
            if _dtypes[column] not in TAFRA_TYPE:
                msg += f'`{_dtypes[column]}` is not a valid dtype for `{column}.`\n'

        if len(msg) > 0:
            # should be KeyError value Python 3.7.x has a bug with '\n'
            raise ValueError(msg)

        return _dtypes

    @staticmethod
    def _format_type(t: Any) -> str:
        _t = str(t)
        if 'int' in _t: _type = 'int'
        elif 'float' in _t: _type = 'float'
        elif 'bool' in _t: _type = 'bool'
        elif 'str' in _t: _type = 'str'
        elif '<U' in _t: _type = 'str'
        elif 'date' in _t: _type = 'date'
        elif '<M' in _t: _type = 'date'
        elif 'object' in _t: _type = 'object'
        elif 'O' in _t: _type = 'object'
        else: return _t
        return _type

    @staticmethod
    def _apply_type(t: str, array: np.ndarray) -> np.ndarray:
        return TAFRA_TYPE[t](array)

    @classmethod
    def from_dataframe(cls, df: DataFrame, dtypes: Optional[Dict[str, str]] = None) -> 'Tafra':
        if dtypes is None:
            dtypes = {c: t for c, t in zip(df.columns, df.dtypes)}
        dtypes = {c: cls._format_type(t) for c, t in dtypes.items()}

        return cls(
            {c: cls._apply_type(dtypes[c], df[c].values) for c in df.columns},
            {c: dtypes[c] for c in df.columns}
        )

    @property
    def columns(self) -> Tuple[str, ...]:
        """Get the names of the columns.
        Equivalent to `Tafra`.keys().
        """
        return tuple(self._data.keys())

    @property
    def rows(self) -> int:
        """Get the rows of the first item in the data `dict`.
        The `len()` of all values have been previously validated.
        """
        if not self._data:
            return 0
        return len(next(iter(self._data.values())))

    @property
    def data(self) -> Dict[str, np.ndarray]:
        """Return the data `dict` attribute.
        """
        return self._data

    @property
    def dtypes(self) -> Dict[str, str]:
        """Return the dtypes `dict`.
        """
        return self._dtypes

    def _slice(self, _slice: slice) -> 'Tafra':
        """Use slice object to slice np.ndarray.
        """
        return Tafra(
            {column: value[_slice]
                for column, value in self._data.items()},
            {column: value
                for column, value in self._dtypes.items()}
        )

    def _index(self, index: np.ndarray) -> 'Tafra':
        """Use numpy indexing to slice np.ndarray.
        """
        if index.ndim != 1:
            raise ValueError(f'Indexing np.ndarray must ndim == 1, got ndim == {index.ndim}')
        return Tafra(
            {column: value[index]
                for column, value in self._data.items()},
            {column: value
                for column, value in self._dtypes.items()}
        )

    def keys(self):
        """Return the keys of the data attribute, i.e. like a `dict.keys()`.
        """
        return self._data.keys()

    def values(self):
        """Return the values of the data attribute, i.e. like a `dict.values()`.
        """
        return self._data.values()

    def items(self):
        """Return the items of the data attribute, i.e. like a `dict.items()`.
        """
        return self._data.items()

    def update(self, other: 'Tafra'):
        """Update the data and dtypes of this `Tafra` with another `Tafra`.
        Length of rows must match, while data of different `dtype` will overwrite.
        """
        rows = self.rows
        for column, values in other._data.items():
            if len(values) != rows:
                raise ValueError(
                    'Other `Tafra` must have consistent row count. '
                    f'This `Tafra` has {rows} rows, other `Tafra` has {len(values)} rows.')
            self._data[column] = values

        self.update_types(other._dtypes)

    def delete(self, column: str):
        """Remove a column from the `Tafra` data and dtypes.
        """
        _ = self._data.pop(column, None)
        _ = self._dtypes.pop(column, None)

    def copy(self, order: str = 'C') -> 'Tafra':
        """Helper function to create a copy of a `Tafra`s data.
        """
        return Tafra(
            {column: value.copy(order=order)
                for column, value in self._data.items()},
            {column: value
                for column, value in self._dtypes.items()}
        )

    @staticmethod
    def _cast_records(dtype: str, data: np.ndarray, cast_null: bool) -> Any:
        """Cast np.nan to None. Requires changing `dtype` to `object`.
        """
        value: Any = RECORD_TYPE[dtype](data.item())
        if cast_null and dtype == 'float' and np.isnan(data.item()):
            return None
        return value

    def to_records(self, columns: Optional[Iterable[str]] = None,
                   cast_null: bool = True) -> Iterable[Tuple[Any, ...]]:
        """Return a generator of tuples, each tuple being a record (i.e. row)
        and allowing heterogeneous typing.
        Useful for e.g. sending records back to a database.
        """
        _columns: Iterable[str] = self.columns if columns is None else columns
        for row in range(self.rows):
            yield tuple(self._cast_records(
                self._dtypes[c], self._data[c][[row]],
                cast_null
            ) for c in _columns)
        return

    def to_list(self, columns: Optional[Iterable[str]] = None) -> List[np.ndarray]:
        """Return a list of homogeneously typed columns (as np.ndarrays) in the tafra.
        If a generator is needed, use `Tafra.values()`.
        """
        if columns is None:
            return list(self._data.values())
        return list(self._data[c] for c in columns)

    def group_by(self, group_by: Iterable[str],
                 aggregation: InitAggregation) -> 'Tafra':
        """Helper function to implement the `GroupBy` class.
        """
        return GroupBy(group_by, aggregation).apply(self)

    def transform(self, group_by: Iterable[str],
                  aggregation: InitAggregation) -> 'Tafra':
        """Helper function to implement the `Transform` class.
        """
        return Transform(group_by, aggregation).apply(self)

    def iterate_by(self, group_by: Iterable[str]) -> Iterable[Tuple[int, 'Tafra']]:
        """Helper function to implement the `IterateBy` class.
        """
        yield from IterateBy(group_by, {}).apply(self)


@dc.dataclass
class AggMethod:
    """Basic methods for aggregations over a data table.
    """
    _group_by_cols: Iterable[str]
    # TODO: specify dtype of result?
    aggregation: dc.InitVar[InitAggregation]
    _aggregation: Dict[str, Tuple[Callable[[np.ndarray], Any], str]] = dc.field(
        default_factory=dict, init=False)

    def __post_init__(self, aggregation: InitAggregation):
        for rename, agg in aggregation.items():
            if callable(agg):
                self._aggregation[rename] = cast(
                    Tuple[Callable[[np.ndarray], Any], str],
                    (agg, rename))
            elif (isinstance(agg, Iterable) and len(agg) == 2
                  and callable(cast(Tuple, agg)[0])):
                self._aggregation[rename] = agg
            else:
                raise ValueError(f'{agg} is not a valid aggregation argument')

    def _validate(self, tafra: Tafra) -> None:
        cols = set(tafra.columns)
        for col in self._group_by_cols:
            if col not in cols:
                raise KeyError(f'{col} does not exist in tafra')
        for (_, col) in self._aggregation.values():
            if col not in cols:
                raise KeyError(f'{col} does not exist in tafra')
        # we don't have to use all the columns!

    def unique_groups(self, tafra: Tafra) -> List[Any]:
        """Construct a unique set of grouped values.
        Uses `OrderedDict` rather than `set` to maintain order.
        """
        return list(OrderedDict.fromkeys(zip(*(tafra[col] for col in self._group_by_cols))))

    def result_factory(self, fn: Callable[[str, str], np.ndarray]) -> Dict[str, np.ndarray]:
        """Factory function to generate the dict for the results set.
        A function to take the new column name and source column name
        and return an empty `np.ndarray` should be given.
        """
        return {
            rename: fn(rename, col) for rename, col in (
                *((col, col) for col in self._group_by_cols),
                *((rename, agg[1]) for rename, agg in self._aggregation.items())
            )
        }


@dc.dataclass
class GroupBy(AggMethod):
    """Analogy to SQL `GROUP BY`, not `pandas.DataFrame.groupby()`. A `reduce` operation.
    """

    def apply(self, tafra: Tafra) -> Tafra:
        self._validate(tafra)
        unique = self.unique_groups(tafra)
        result = self.result_factory(
            lambda rename, col: np.empty(len(unique), dtype=tafra[col].dtype))

        for i, u in enumerate(unique):
            which_rows = np.full(tafra.rows, True)

            for val, col in zip(u, self._group_by_cols):
                which_rows &= tafra[col] == val
                result[col][i] = val

            for rename, agg in self._aggregation.items():
                fn, col = agg
                result[rename][i] = fn(tafra[col][which_rows])

        return Tafra(result)


@dc.dataclass
class Transform(AggMethod):
    """Analogy to `pandas.DataFrame.transform()`,
    i.e. a SQL `GROUP BY` and `LEFT JOIN` back to the original table.
    """

    def apply(self, tafra: Tafra) -> Tafra:
        self._validate(tafra)
        unique = self.unique_groups(tafra)
        result = self.result_factory(
            lambda rename, col: np.empty_like(tafra[col]))

        for i, u in enumerate(unique):
            which_rows = np.full(tafra.rows, True)

            for val, col in zip(u, self._group_by_cols):
                which_rows &= tafra[col] == val
                result[col][which_rows] = tafra[col][which_rows]

            for rename, agg in self._aggregation.items():
                fn, col = agg
                result[rename][which_rows] = fn(tafra[col][which_rows])

        return Tafra(result)


# TODO: it's probably better for this to return (UniqueTuple, Tafra) than
#   to enumerate - the caller can enumerate but doesn't have easy access
#   to the unique tuple
@dc.dataclass
class IterateBy(AggMethod):
    """Analogy to `pandas.DataFrame.groupby()`, i.e. an Iterable of `Tafra` objects.
    """
    def apply(self, tafra: Tafra) -> Iterable[Tuple[int, Tafra]]:
        self._validate(tafra)
        unique = self.unique_groups(tafra)

        for i, u in enumerate(unique):
            which_rows = np.full(tafra.rows, True)
            result = self.result_factory(
                lambda rename, col: np.empty(np.sum(which_rows)))

            for val, col in zip(u, self._group_by_cols):
                which_rows &= tafra[col] == val

            yield (i, tafra[which_rows])


Tafra.copy.__doc__ += '\n\nnumpy doc string:\n' + np.ndarray.copy.__doc__  # type: ignore
Tafra.group_by.__doc__ += GroupBy.__doc__  # type: ignore
Tafra.transform.__doc__ += Transform.__doc__  # type: ignore
Tafra.iterate_by.__doc__ += IterateBy.__doc__  # type: ignore


if __name__ == '__main__':
    t = Tafra({
        'x': np.array([1, 2, 3, 4, 5, 6]),
        'y': np.array(['one', 'two', 'one', 'two', 'one', 'two'], dtype='object'),
        'z': np.array([0, 0, 0, 1, 1, 1])
    })

    print('List:\t\t', t.to_list())
    print('Record:\t\t', list(t.to_records()))

    gb = t.group_by(
        ['y', 'z'], {'x': sum}
    )

    print('Group By:\t', gb)

    # transform example

    print('Iterate by y, z:')
    for grp in gb.iterate_by(('y', 'z')):
        print(grp)
