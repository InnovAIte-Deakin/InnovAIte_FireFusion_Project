# Fire Occurrence Data Pipeline (NASA FIRMS)

## Overview

This project prepares a bushfire occurrence dataset using NASA FIRMS satellite data for Australia. The goal is to clean and structure fire detection data so it can be used for bushfire prediction and analysis.

---

## Dataset

**Source:** NASA FIRMS (Fire Information for Resource Management System)
**Data Type:** Satellite-detected fire events
**Region:** Australia

---

## What I Did

* Loaded raw FIRMS fire data
* Selected key features (latitude, longitude, acquisition date, confidence)
* Cleaned and filtered low-confidence or invalid records
* Created a fire occurrence label (`fire_occurred = 1`)
* Generated synthetic non-fire data (`fire_occurred = 0`) for modelling
* Combined and structured data into a final dataset

---

## Key Features

* Latitude and longitude of fire events
* Date of fire detection
* Confidence level of detection
* Binary fire occurrence label

---

## Why This Matters

Fire occurrence data is essential for understanding where and when bushfires happen. By structuring this data properly, it can be used in machine learning models to predict bushfire risk and support early warning systems.

---

## Tech Stack

* Python
* Pandas, NumPy

---

## Output

* Clean dataset generated locally (not stored in repository)
* Structured data ready for machine learning and analysis

---

## Important Note

* Raw and processed CSV files are not uploaded to GitHub
* Data is generated locally following project guidelines

---

## Future Work

* Integrate weather and climate datasets
* Improve feature engineering
* Use dataset for bushfire prediction modelling

---

## Author

Sonu Chaudhary
Data Engineering Stream – FireFusion Project
