{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "27643925-3166-4175-a9ca-f184636884ae",
   "metadata": {},
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "Cleaning elevation cache...\n",
      "find cache -size 0 -name \"*.tif\" -delete\n",
      "rm -f SRTM1.*.vrt\n",
      "rm -f -r spool/*\n",
      "Downloading DEM...\n",
      "make: Nothing to be done for `download'.\n",
      "make: Nothing to be done for `all'.\n",
      "cp SRTM1.vrt SRTM1.37196b648b9f43e4879361dd521cdabb.vrt\n",
      "gdal_translate -q -co TILED=YES -co COMPRESS=DEFLATE -co ZLEVEL=9 -co PREDICTOR=2 -projwin 144.7 -37.5 145.3 -38.1 SRTM1.37196b648b9f43e4879361dd521cdabb.vrt /Users/mohammedabdulsuboor/Desktop/Topo_work/data/dem_sample.tif\n",
      "rm -f SRTM1.37196b648b9f43e4879361dd521cdabb.vrt\n",
      "DEM file created successfully.\n",
      "Saved to: data/dem_sample.tif\n"
     ]
    }
   ],
   "source": [
    "from pathlib import Path\n",
    "import shutil\n",
    "import subprocess\n",
    "\n",
    "# Change area here only if needed: (left, bottom, right, top)\n",
    "bounds = (144.7, -38.1, 145.3, -37.5)\n",
    "\n",
    "data_dir = Path(\"data\")\n",
    "data_dir.mkdir(exist_ok=True)\n",
    "\n",
    "dem_file = data_dir / \"dem_sample.tif\"\n",
    "\n",
    "if shutil.which(\"eio\") is None:\n",
    "    raise RuntimeError(\"eio command not found. Install elevation first.\")\n",
    "\n",
    "print(\"Cleaning elevation cache...\")\n",
    "subprocess.run([\"eio\", \"clean\"], check=False)\n",
    "\n",
    "print(\"Downloading DEM...\")\n",
    "subprocess.run(\n",
    "    [\n",
    "        \"eio\",\n",
    "        \"--product\", \"SRTM1\",\n",
    "        \"clip\",\n",
    "        \"-o\", str(dem_file),\n",
    "        \"--bounds\",\n",
    "        str(bounds[0]), str(bounds[1]), str(bounds[2]), str(bounds[3]),\n",
    "    ],\n",
    "    check=True\n",
    ")\n",
    "\n",
    "print(\"DEM file created successfully.\")\n",
    "print(\"Saved to:\", dem_file)"
   ]
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
