from psycopg import AsyncConnection
from ..models.fire_event import FireEvent
from ...config.config import environment
from ..models.fire_incident_v2 import FireIncidentV2
from ..models.fire_risk_source import FireRiskSourceRecord


# Existing query used by the current Backend event pipeline.
# This reads from the older fire_events_full PostgreSQL view and is kept
# available while the newer Data Engineering schema is introduced.
RECENT_DATA_SQL_QUERY = """
    SELECT * FROM fire_events_full
    WHERE event_date >= CURRENT_DATE - make_interval(days => %s)
    ORDER BY event_date DESC
"""


# Query used to retrieve fire incidents from the newer Data Engineering schema.
# Fire_Incident_Record is joined with Location_Registry and Time_Registry so
# Backend receives the fire data together with its location and time information.
RECENT_FIRE_INCIDENTS_V2_SQL = """
    SELECT
        fir.incident_id,
        fir.location_id,
        fir.time_id,
        fir.original_latitude,
        fir.original_longitude,
        fir.record_type,
        fir.source,
        fir.satellite,
        fir.instrument,
        fir.acq_date,
        fir.acq_time,
        fir.brightness_ti4,
        fir.brightness_ti5,
        fir.frp,
        fir.confidence,
        fir.daynight,

        lr.grid_latitude,
        lr.grid_longitude,
        lr.region_name,

        tr.datetime_record,
        tr.season

    FROM Fire_Incident_Record fir

    JOIN Location_Registry lr
        ON fir.location_id = lr.location_id

    JOIN Time_Registry tr
        ON fir.time_id = tr.time_id

    WHERE tr.datetime_record >= NOW() - make_interval(days => %s)

    ORDER BY tr.datetime_record DESC
"""

FIRE_RISK_SOURCE_SQL = """
    SELECT
        wo.location_id,
        wo.time_id,

        tr.datetime_record,

        lr.grid_latitude,
        lr.grid_longitude,
        lr.region_name,

        wo.temperature_c,
        wo.wind_speed_kmh,
        wo.relative_humidity,

        vc.vegetation_class,
        vc.dryness_index,
        vc.soil_moisture,

        tp.elevation_meters,
        tp.slope_angle,

        en.oni_anomaly,
        en.enso_phase,
        en.oni_lag6m

    FROM weather_observation wo

    JOIN location_registry lr
        ON wo.location_id = lr.location_id

    JOIN time_registry tr
        ON wo.time_id = tr.time_id

    LEFT JOIN vegetation_condition vc
        ON wo.location_id = vc.location_id
        AND wo.time_id = vc.time_id

    LEFT JOIN topography_profile tp
        ON wo.location_id = tp.location_id

    LEFT JOIN el_nino en
        ON wo.time_id = en.time_id

    WHERE tr.datetime_record >= NOW() - make_interval(hours => %s)

    ORDER BY
        wo.location_id,
        tr.datetime_record ASC
"""


class AggregatorRepository():

    def __init__(self):
        # Database connection URL supplied through the Aggregator API
        # environment configuration.
        self.db_url = environment.relational_db_url

    async def get_recent_events(self, days=14) -> list[FireEvent]:

        # Get events from the last N days using the existing fire_events_full
        # database view.
        async with await AsyncConnection.connect(self.db_url) as connection:

            async with connection.cursor() as cursor:

                # Execute the existing query and pass the requested number
                # of days as a SQL parameter.
                await cursor.execute(
                    RECENT_DATA_SQL_QUERY,
                    (days,)
                )

                # Return an empty list if the query does not return
                # any column information.
                if cursor.description is None:
                    return []

                # Extract the returned column names so they can be matched
                # with the values from each database row.
                columns = [
                    description[0]
                    for description in cursor.description
                ]

                # Retrieve each SELECT row as a tuple.
                rows: list[tuple] = await cursor.fetchall()

                # Convert each returned row into the existing FireEvent model.
                events = []

                for row in rows:

                    # Match each column name with its corresponding row value.
                    row_dict = dict(zip(columns, row))

                    # Validate and convert the database row into FireEvent.
                    events.append(FireEvent(**row_dict))

                return events

    async def get_recent_fire_incidents_v2(
        self,
        days: int = 14
    ) -> list[FireIncidentV2]:

        # Retrieve fire incidents using the newer Data Engineering schema
        # while keeping the existing get_recent_events() pathway available.
        async with await AsyncConnection.connect(self.db_url) as connection:

            async with connection.cursor() as cursor:

                # Query Fire_Incident_Record and join the related location
                # and time registry information.
                await cursor.execute(
                    RECENT_FIRE_INCIDENTS_V2_SQL,
                    (days,)
                )

                # Return an empty list if no column information is available.
                if cursor.description is None:
                    return []

                # Extract the joined query column names for model conversion.
                columns = [
                    description[0]
                    for description in cursor.description
                ]

                # Retrieve all matching database rows.
                rows: list[tuple] = await cursor.fetchall()

                # Convert each joined row into the FireIncidentV2 model.
                return [
                    FireIncidentV2(
                        **dict(zip(columns, row))
                    )
                    for row in rows
                ]
    async def get_fire_risk_source_data(
        self,
         hours: int = 720
    ) -> list[FireRiskSourceRecord]:
        
        """
        Retrieve the currently available Data Engineering weather /
        environmental information that may be used to build the
        AI Modelling bushfire forecast request.

        The final DE -> AI field mapping is deliberately handled outside
        this repository.
        """

        async with await AsyncConnection.connect(self.db_url) as connection:

             async with connection.cursor() as cursor:

                await cursor.execute(
                    FIRE_RISK_SOURCE_SQL,
                    (hours,)
                )

                if cursor.description is None:
                    return []

                columns = [
                    description[0]
                    for description in cursor.description
                ]

                rows: list[tuple] = await cursor.fetchall()

                return [
                    FireRiskSourceRecord(
                        **dict(zip(columns, row))
                    )
                    for row in rows
                ]

