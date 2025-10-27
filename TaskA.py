from typing import Union
import csv

# Series

class BooleanSeries:
    def __init__(self, items: list[Union[bool, None]]):
        for i in items:
            if i is not None and not isinstance(i, bool):
                raise ValueError(f"Item {i} is not a bool or None.")
        self._items = items

    def __len__(self):
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]

    # Flip all boolean values 
    def __invert__(self):
        return BooleanSeries([None if x is None else not x for x in self._items])

    def __and__(self, other):
        return BooleanSeries([
            a and b if a is not None and b is not None else None
            for a, b in zip(self._items, other._items)
        ])

    def __or__(self, other):
        return BooleanSeries([
            a or b if a is not None and b is not None else None
            for a, b in zip(self._items, other._items)
        ])

    def __str__(self):
        return str(self._items)


# Stores a list of strings
class StringSeries:
    def __init__(self, items: list[Union[str, None]]):
        # Ensure everything is either a string or None
        for i in items:
            if i is not None and not isinstance(i, str):
                raise ValueError(f"Item {i} is not a string or None.")
        self._items = items

    def __len__(self):
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]

    # Checks if two StringSeries (or a Series and a single value) are equal
    def __eq__(self, other):
        result = []
        if isinstance(other, StringSeries):
            for a, b in zip(self._items, other._items):
                result.append(None if a is None or b is None else a == b)
        else:
            for a in self._items:
                result.append(None if a is None else a == other)
        return BooleanSeries(result)

    # check for not equal
    def __ne__(self, other):
        result = []
        if isinstance(other, StringSeries):
            for a, b in zip(self._items, other._items):
                result.append(None if a is None or b is None else a != b)
        else:
            for a in self._items:
                result.append(None if a is None else a != other)
        return BooleanSeries(result)

    def __str__(self):
        return str(self._items)


# integer values
class IntSeries:
    def __init__(self, items: list[Union[int, None]]):
        for i in items:
            if i is not None and not isinstance(i, int):
                raise ValueError(f"Item {i} is not an int or None.")
        self._items = items

    def __len__(self):
        return len(self._items)

    def __getitem__(self, idx):
        return self._items[idx]

    # Equality comparisons
    def __eq__(self, other):
        if isinstance(other, IntSeries):
            return BooleanSeries([
                None if a is None or b is None else a == b
                for a, b in zip(self._items, other._items)
            ])
        return BooleanSeries([None if a is None else a == other for a in self._items])

    # Simple greater/less comparisons with numbers
    def __lt__(self, other):
        return BooleanSeries([None if a is None or other is None else a < other for a in self._items])

    def __gt__(self, other):
        return BooleanSeries([None if a is None or other is None else a > other for a in self._items])

    # Small utility methods for aggregation
    def sum(self):
        nums = [x for x in self._items if x is not None]
        return sum(nums)

    def mean(self):
        nums = [x for x in self._items if x is not None]
        return sum(nums) / len(nums) if nums else None

    def __str__(self):
        return str(self._items)

# DataFrame class

class DataFrame:
    def __init__(self, data: dict):
        # Check all columns look like Series (they should have _items)
        if not all(hasattr(v, "_items") for v in data.values()):
            raise ValueError("All columns must be Series objects.")

        # Make sure every column has the same number of rows
        lengths = {len(v) for v in data.values()}
        if len(lengths) > 1:
            raise ValueError("Columns must all be the same length.")

        self._columns = data

    def __getitem__(self, key):
        # Getting a column by name
        if isinstance(key, str):
            return self._columns[key]

        # Boolean mask filtering (like df[mask])
        elif isinstance(key, BooleanSeries):
            filtered = {}
            for name, series in self._columns.items():
                filtered_items = [v for v, keep in zip(series._items, key._items) if keep]
                filtered[name] = series.__class__(filtered_items)
            return DataFrame(filtered)

        else:
            raise ValueError("Invalid key type. Expected column name or BooleanSeries.")

    def __str__(self):
        # Basic text table — nothing fancy
        cols = list(self._columns.keys())
        header = " | ".join(cols)
        lines = [header, "-" * len(header)]
        rows = zip(*[v._items for v in self._columns.values()])
        for r in rows:
            line = " | ".join(str(x) for x in r)
            lines.append(line)
        return "\n".join(lines)

    def get_column_names(self):
        return list(self._columns.keys())

    @classmethod
    def from_csv(cls, file_path: str, delimiter: str = ","):
        # Load a CSV file and tries to guess what type each column is
        with open(file_path, newline="") as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = {col: [] for col in reader.fieldnames}
            for row in reader:
                for col in reader.fieldnames:
                    val = row[col].strip()
                    data[col].append(val if val != "" else None)

        final = {}
        for k, vals in data.items():
            lower = [v.lower() for v in vals if v is not None]

            if all(v in ("true", "false") for v in lower):
                final[k] = BooleanSeries([None if v is None else v.lower() == "true" for v in vals])

            elif all(v.isdigit() for v in vals if v is not None):
                final[k] = IntSeries([None if v is None else int(v) for v in vals])

            else:
                final[k] = StringSeries(vals)

        return cls(final)


# Demo

print("Creating a small demo DataFrame...\n")

data = {
    "name": StringSeries(["Alice", "Bob", "Charlie", "Dana"]),
    "age": IntSeries([25, 30, 19, None]),
    "student": BooleanSeries([False, False, True, True])
}

df = DataFrame(data)
print(df)

print("\nPeople older than 20:")
mask = df["age"] > 20
print(df[mask])

print("\nAverage age:", df["age"].mean())
