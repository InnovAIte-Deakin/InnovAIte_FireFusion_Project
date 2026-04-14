from psycopg import AsyncConnection
from ..models.fire_event import FireEvent
from ...config.config import environment

# view created in postgresql
RECENT_DATA_SQL_QUERY = """
    SELECT * FROM fire_events_full
    WHERE event_date >= CURRENT_DATE - make_interval(days => %s)
    ORDER BY event_date DESC
"""

class AggregatorRepository():
    def __init__(self):
        self.db_url = environment.relational_db_url

    async def get_recent_events(self, days=14) -> list[FireEvent]:

        # get events from last n days
        # start counting back from database CURRENT_DATE

        async with await AsyncConnection.connect(self.db_url) as connection:

            async with connection.cursor() as cursor: 

                # execute sql, passing number of days as parameter
                await cursor.execute(RECENT_DATA_SQL_QUERY, (days,))

                # if query SELECT nothing return no events
                if cursor.description is None:
                    return []

                # extract the column names, and place into list
                columns = [description[0] for description in cursor.description]


                # each SELECT row is given as tuple
                rows: list[tuple] = await cursor.fetchall()

                # convert each tuple into the model
                events = []

                for row in rows:
                    # match each column name with row value
                    row_dict = dict(zip(columns, row)) 

                    # append FireEvent mapping each row dict as field in model
                    events.append(FireEvent(**row_dict))

                return events