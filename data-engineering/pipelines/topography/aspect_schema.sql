{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "0e1d41a4-4301-4e83-98a7-83019e204883",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Folders ready\n"
     ]
    }
   ],
   "source": [
    "from pathlib import Path\n",
    "\n",
    "project_dir = Path(\".\")\n",
    "data_dir = project_dir / \"data\"\n",
    "reports_dir = project_dir / \"reports\"\n",
    "schema_dir = project_dir / \"schema\"\n",
    "\n",
    "reports_dir.mkdir(exist_ok=True)\n",
    "schema_dir.mkdir(exist_ok=True)\n",
    "\n",
    "print(\"Folders ready\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "913dcbdf-07d8-4374-95f2-8f04f6a37313",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Created: schema/aspect_schema.sql\n",
      "CREATE TABLE IF NOT EXISTS aspect_points (\n",
      "    id SERIAL PRIMARY KEY,\n",
      "    longitude DOUBLE PRECISION NOT NULL,\n",
      "    latitude DOUBLE PRECISION NOT NULL,\n",
      "    aspect_deg DOUBLE PRECISION NOT NULL,\n",
      "    source_dataset TEXT,\n",
      "    raster_name TEXT,\n",
      "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n",
      ");\n",
      "\n",
      "CREATE INDEX IF NOT EXISTS idx_aspect_points_lat_lon\n",
      "ON aspect_points (latitude, longitude);\n"
     ]
    }
   ],
   "source": [
    "from pathlib import Path\n",
    "\n",
    "project_dir = Path(\".\")\n",
    "schema_dir = project_dir / \"schema\"\n",
    "schema_dir.mkdir(exist_ok=True)\n",
    "\n",
    "schema_file = schema_dir / \"aspect_schema.sql\"\n",
    "\n",
    "schema_sql = \"\"\"\n",
    "CREATE TABLE IF NOT EXISTS aspect_points (\n",
    "    id SERIAL PRIMARY KEY,\n",
    "    longitude DOUBLE PRECISION NOT NULL,\n",
    "    latitude DOUBLE PRECISION NOT NULL,\n",
    "    aspect_deg DOUBLE PRECISION NOT NULL,\n",
    "    source_dataset TEXT,\n",
    "    raster_name TEXT,\n",
    "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP\n",
    ");\n",
    "\n",
    "CREATE INDEX IF NOT EXISTS idx_aspect_points_lat_lon\n",
    "ON aspect_points (latitude, longitude);\n",
    "\"\"\".strip()\n",
    "\n",
    "with open(schema_file, \"w\") as f:\n",
    "    f.write(schema_sql)\n",
    "\n",
    "print(\"Created:\", schema_file)\n",
    "print(schema_sql)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "60098d26-2f18-4a14-9d4f-4426ed2e8212",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python [conda env:base] *",
   "language": "python",
   "name": "conda-base-py"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.13"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
