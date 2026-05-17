import pandas as pd
from typing import Literal


_DTYPE_MAP: dict[str, str] = {
    "int":      "int64",
    "integer":  "int64",
    "float":    "float64",
    "double":   "float64",
    "str":      "object",
    "string":   "object",
    "bool":     "bool",
    "boolean":  "bool",
    "datetime": "datetime",
    "date":     "datetime",
    "timedelta":"timedelta",
    "category":    "category",
    "categorical": "category",
}


class DataCleaner:
    def __init__(self, df: pd.DataFrame, schema: dict[str, str] | None = None) -> None:
        self._original_shape = df.shape
        self.df = df.copy()
        self.schema = schema or {}
        self._log: list[str] = []

    def remove_missing(
        self,
        strategy: Literal["drop", "fill"] = "drop",
        fill_value: object = None,
        subset: list[str] | None = None,
    ) -> "DataCleaner":
        before = len(self.df)

        if strategy == "drop":
            self.df = self.df.dropna(subset=subset)
            self._log.append(f"[missing] dropped {before - len(self.df)} row(s)")

        elif strategy == "fill":
            if fill_value is None:
                raise ValueError("fill_value must be provided when strategy='fill'.")
            self.df = self.df.fillna(fill_value)
            self._log.append(f"[missing] filled NaN with {fill_value!r}")

        else:
            raise ValueError(f"Unknown strategy '{strategy}'. Use 'drop' or 'fill'.")

        return self

    def remove_duplicates(
        self,
        subset: list[str] | None = None,
        keep: Literal["first", "last", False] = "first",
    ) -> "DataCleaner":
        before = len(self.df)
        self.df = self.df.drop_duplicates(subset=subset, keep=keep)
        self._log.append(f"[duplicates] removed {before - len(self.df)} row(s)")
        return self

    def cast_types(self) -> "DataCleaner":
        if not self.schema:
            self._log.append("[types] skipped — no schema provided")
            return self

        for col, raw_dtype in self.schema.items():
            dtype = _DTYPE_MAP.get(raw_dtype.lower(), raw_dtype.lower())

            if col not in self.df.columns:
                self._log.append(f"[types] WARNING: '{col}' not found — skipped")
                continue

            try:
                if dtype == "datetime":
                    self.df[col] = pd.to_datetime(self.df[col])
                elif dtype == "timedelta":
                    self.df[col] = pd.to_timedelta(self.df[col])
                elif dtype == "category":
                    self.df[col] = self.df[col].astype("category")
                else:
                    self.df[col] = self.df[col].astype(dtype)
                self._log.append(f"[types] '{col}' → {dtype}")

            except Exception as exc:
                self._log.append(f"[types] ERROR '{col}' → {dtype}: {exc}")

        return self

    def clean(
        self,
        missing_strategy: Literal["drop", "fill"] = "drop",
        fill_value: object = None,
        missing_subset: list[str] | None = None,
        dup_subset: list[str] | None = None,
    ) -> pd.DataFrame:
        self.remove_missing(strategy=missing_strategy, fill_value=fill_value, subset=missing_subset)
        self.remove_duplicates(subset=dup_subset)
        self.cast_types()
        return self.df

    def report(self) -> str:
        rows_removed = self._original_shape[0] - self.df.shape[0]
        lines = [
            f"original: {self._original_shape} → final: {self.df.shape} ({rows_removed} rows removed)",
        ] + self._log
        return "\n".join(lines)
