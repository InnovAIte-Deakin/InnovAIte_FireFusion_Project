import pandas as pd
import pytest

from enrich_fire_climate import enrich_with_enso


def test_report_source_month_without_changing_fire_key_or_climate_values():
    fires = pd.DataFrame({"record_year_month": ["2027-01", "2026-05", "2026-07", "2026-04"]})
    enso = pd.DataFrame({
        "record_year_month": ["2026-08", "2026-05"],
        "oni_anomaly": [-0.8, 0.8], "enso_phase": ["La Nina", "El Nino"],
        "oni_lag6m": [0.1, None],
    })
    output = enrich_with_enso(fires, enso).set_index("record_year_month")
    assert output.index.tolist() == ["2026-04", "2026-05", "2026-07", "2027-01"]
    assert output.enso_match_date.dt.strftime("%Y-%m").tolist() == output.index.tolist()
    assert output.enso_match_status.tolist() == ["unmatched", "exact", "prior", "prior"]
    assert output.enso_source_month.iloc[1:].tolist() == ["2026-05", "2026-05", "2026-08"]
    assert output.enso_age_months.iloc[1:].tolist() == [0, 2, 5]
    assert output.oni_anomaly.iloc[1:].tolist() == [0.8, 0.8, -0.8]
    assert pd.isna(output.loc["2026-05", "oni_lag6m"])
    assert list(fires) == ["record_year_month"]
    assert "enso_source_month" not in enso


@pytest.mark.parametrize("months", [[], ["2026-08"]], ids=["empty", "future_only"])
def test_no_eligible_month_preserves_the_fire(months):
    fires = pd.DataFrame({"record_year_month": ["2026-07"]})
    enso = pd.DataFrame({"record_year_month": pd.Series(months, dtype="string"),
                         "oni_anomaly": [-0.8] * len(months), "enso_phase": ["La Nina"] * len(months),
                         "oni_lag6m": [0.1] * len(months)})
    output = enrich_with_enso(fires, enso)
    assert output.enso_match_status.tolist() == ["unmatched"]
    assert output[["oni_anomaly", "enso_phase", "oni_lag6m", "enso_source_month", "enso_age_months"]].isna().all().all()


def test_preprocessed_missing_anomaly_cannot_supply_a_neutral_phase():
    fires = pd.DataFrame({"record_year_month": ["2026-07", "2026-08"]})
    enso = pd.DataFrame({"record_year_month": ["2026-07"], "oni_anomaly": [float("nan")],
                         "enso_phase": ["Neutral"], "oni_lag6m": [0.1]})
    result = enrich_with_enso(fires, enso)
    assert result.enso_match_status.tolist() == ["exact", "prior"]
    assert result.enso_age_months.tolist() == [0, 1]
    assert result.enso_source_month.tolist() == ["2026-07", "2026-07"]
    assert result.enso_phase.isna().all()
    assert result.oni_lag6m.tolist() == [0.1, 0.1]
