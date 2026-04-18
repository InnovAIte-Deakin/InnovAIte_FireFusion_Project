# FireFusion: Fire Events Data Pipeline and Analysis

## Overview

This project focuses on processing and analyzing satellite-detected fire events using NASA FIRMS data for the Black Summer bushfires (2019–2020) in Australia.

The pipeline extracts, transforms, and loads fire event data into a structured format following the FireFusion database architecture. The processed data is then analyzed to identify temporal and spatial fire patterns.

---

## Project Objectives

- Extract raw fire data from NASA FIRMS
- Transform and clean the dataset
- Structure data according to the FireFusion schema
- Perform exploratory data analysis (EDA)
- Store processed data in a PostgreSQL database
- Enable integration with other project datasets (weather, vegetation, topography)

---

## Dataset

Source: NASA FIRMS (Fire Information for Resource Management System)

### Raw Data Fields

- latitude  
- longitude  
- brightness  
- scan  
- track  
- acq_date  
- acq_time  
- satellite  
- instrument  
- confidence  
- version  
- bright_t31  
- frp  
- daynight  
- type  

---

## Project Structure
data-engineering/
│
├── data/
│ ├── raw/
│ │ └── firms_data.csv
│ └── processed/
│ └── fire_events.csv
│
├── pipelines/
│ └── nasa_firms/
│ ├── extract_firms.py
│ ├── transform_firms.py
│ └── load_to_postgres.py
│
├── notebooks/
│ └── fire_analysis.ipynb
│
├── requirements.txt
├── .env
└── README.md


---

## Data Pipeline

### 1. Extraction

- Raw FIRMS data is loaded from `data/raw/firms_data.csv`
- Data is validated for structure and completeness

### 2. Transformation

- Duplicate or invalid rows are removed
- Data types are standardized
- Date fields are converted to datetime format
- Dataset is filtered for the Black Summer period (2019–2020)
- Final structure matches the FireFusion schema

Output:
data/processed/fire_events.csv


---

### 3. Loading into PostgreSQL

The processed dataset is loaded into a PostgreSQL database for structured storage and integration.

#### Table: Fire_Events

event_id (Primary Key)
weather_id (Foreign Key - NULL)
topo_id (Foreign Key - NULL)
fuel_id (Foreign Key - NULL)
facility_id (Foreign Key - NULL)
latitude
longitude
event_date
confidence_score
source_system


Foreign keys are intentionally left NULL at this stage, as dimension tables are populated independently.

---

## PostgreSQL Setup

### 1. Install Dependencies

pip install psycopg2-binary sqlalchemy python-dotenv
---

### 2. Create Database

CREATE DATABASE firefusion_db;

---

### 3. Configure Environment Variables

Create a `.env` file in the project root:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=firefusion_db
DB_USER=postgres
DB_PASSWORD=your_password


---

### 4. Load Data into PostgreSQL

Run the script:
cd pipelines/nasa_firms
python load_to_postgres.py

This will:

- Create the `Fire_Events` table (if not exists)
- Clear existing data
- Insert processed records from CSV

---

### 5. Verify Data

In PostgreSQL:
SELECT COUNT(*) FROM "Fire_Events";
SELECT * FROM "Fire_Events" LIMIT 10;

---

## Data Analysis

The notebook `fire_analysis.ipynb` performs:

### Temporal Analysis
- Monthly fire trends
- Daily fire activity patterns

### Spatial Analysis
- Geographic distribution of fire events

### Intensity Analysis
- Fire intensity using brightness values
- Peak fire severity periods

---

## Key Results

- Fire activity peaked in December 2019
- Gradual increase observed from mid-2019
- High concentration of fires in southeastern Australia
- Satellite detections show consistent confidence levels

---

## How to Run the Project

### 1. Install Dependencies
pip install -r requirements.txt

---

### 2. Run Data Transformation
python pipelines/nasa_firms/transform_firms.py

---

### 3. Load into PostgreSQL
python pipelines/nasa_firms/load_to_postgres.py

---

### 4. Run Analysis Notebook
jupyter notebook notebooks/fire_analysis.ipynb

---

## Tools and Technologies

- Python
- Pandas
- Matplotlib
- PostgreSQL
- SQLAlchemy
- Jupyter Notebook

---

## Future Improvements

- Integrate weather, vegetation, and topography datasets
- Build predictive fire risk models
- Develop interactive dashboards
- Apply geospatial analysis techniques

---

## Author

Data Engineering Project – FireFusion

---

## License

This project is for educational purposes.