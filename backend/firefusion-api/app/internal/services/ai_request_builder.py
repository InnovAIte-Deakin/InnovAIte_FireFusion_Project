from collections import defaultdict
from datetime import datetime


# AI Modelling's current working request uses 30 historical
# timesteps per grid cell.
#
# The overall request structure is expected to remain stable,
# although the number of input features may expand later if
# live Data Engineering fire-event data is added to the model.
DEFAULT_INPUT_STEPS = 30


class AIRequestBuilder:

    def build(
        self,
        source_records: list[dict],
        feature_names: list[str],
        feature_mapping: dict[str, str],
        input_steps: int = DEFAULT_INPUT_STEPS
    ) -> dict:
        """
        Convert prepared Data Engineering records into the GeoJSON
        request structure expected by:

            POST /predict/bushfire/forecast

        feature_mapping maps each AI Modelling feature name to the
        corresponding field supplied by Data Engineering.

        Example:

            {
                "era5land_temperature_2m_c": "temperature_c"
            }

        The order of values in each observation row follows
        feature_names exactly. AI Modelling checks these feature names
        during inference and will flag the request if they do not match
        the model's expected inputs.

        Missing mappings or missing DE values raise an error rather
        than silently creating incomplete or incorrect model inputs.
        """

        if not source_records:
            raise ValueError(
                "No Data Engineering source records were supplied"
            )

        # Group time-series records by location so each location/grid
        # cell becomes one GeoJSON Feature in the AI request.
        grouped: dict[int, list[dict]] = defaultdict(list)

        for record in source_records:
            grouped[record["location_id"]].append(record)

        features = []

        for location_id, records in grouped.items():

            # AI expects observations in chronological order.
            records.sort(
                key=lambda item: item["datetime_record"]
            )

            # Use the most recent 30 observations for the current
            # AI Modelling request contract.
            records = records[-input_steps:]

            if len(records) < input_steps:
                # A model request should only contain cells with enough
                # historical observations to satisfy the AI input shape.
                continue

            observations = []
            timestamps = []

            for record in records:

                row = []

                # Build each observation row in the exact same order
                # as feature_names. This ordering is important because
                # AI Modelling validates it during inference.
                for ai_feature in feature_names:

                    de_field = feature_mapping.get(ai_feature)

                    if de_field is None:
                        raise ValueError(
                            f"No Data Engineering mapping has been "
                            f"defined for AI feature '{ai_feature}'"
                        )

                    value = record.get(de_field)

                    if value is None:
                        raise ValueError(
                            f"Missing DE value '{de_field}' for "
                            f"AI feature '{ai_feature}'"
                        )

                    row.append(float(value))

                observations.append(row)

                # Convert Python datetime values into the ISO timestamp
                # format used by the AI Modelling request payload.
                timestamp = record["datetime_record"]

                if isinstance(timestamp, datetime):
                    timestamp = timestamp.isoformat()

                timestamps.append(timestamp)

            latest = records[-1]

            # Build a temporary polygon around the DE grid location.
            # The final grid geometry/index mapping should be updated
            # once Data Engineering confirms how their locations map
            # to AI Modelling's grid_row/grid_col values.
            geometry = self._build_grid_polygon(
                latitude=float(latest["grid_latitude"]),
                longitude=float(latest["grid_longitude"])
            )

            features.append(
                {
                    "type": "Feature",
                    "geometry": geometry,
                    "properties": {
                        "id": str(location_id),
                        "observations": observations,
                        "timestamps": timestamps,

                        # AI Modelling's working request includes these
                        # fields. Backend still needs the confirmed
                        # Data Engineering -> AI grid index mapping
                        # before they can be populated correctly.
                        "grid_row": None,
                        "grid_col": None
                    }
                }
            )

        if not features:
            raise ValueError(
                "No locations contained enough observations to build "
                f"the required {input_steps}-step AI request"
            )

        # feature_names is included explicitly because it defines the
        # meaning and order of every value in the observations arrays.
        #
        # The feature list may expand in future without changing the
        # overall GeoJSON request structure.
        return {
            "type": "FeatureCollection",
            "features": features,
            "feature_names": feature_names,
            "schema_version": "1.0"
        }

    @staticmethod
    def _build_grid_polygon(
        latitude: float,
        longitude: float
    ) -> dict:
        """
        Build a temporary polygon around a Data Engineering grid centre.

        The current assumption uses an approximately 0.05-degree grid.
        This should be replaced or confirmed once the canonical
        Data Engineering -> AI Modelling grid mapping is agreed.
        """

        half = 0.025

        return {
            "type": "Polygon",
            "coordinates": [[
                [longitude - half, latitude - half],
                [longitude + half, latitude - half],
                [longitude + half, latitude + half],
                [longitude - half, latitude + half],
                [longitude - half, latitude - half]
            ]]
        }