"""Australian meteorological seasons (Victoria). Matches time_registry.ipynb."""


def get_australian_meteorological_season(month: int) -> str:
    if month in (12, 1, 2):
        return "Summer"
    if month in (3, 4, 5):
        return "Autumn"
    if month in (6, 7, 8):
        return "Winter"
    return "Spring"
