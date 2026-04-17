{
 "cells": [
  {
   "cell_type": "markdown",
   "id": "32408dc5-619d-4cb2-84e5-504d4e776c59",
   "metadata": {},
   "source": [
    "# ERA5 Data Processing for FireFusion\n",
    "\n",
    "## Objective\n",
    "The purpose of this notebook is to preprocess ERA5 weather data for Victoria during the Black Summer bushfires. The processed dataset will support downstream tasks such as bushfire risk modelling, feature engineering, and integration with other project components.\n",
    "\n",
    "## Variables Used\n",
    "The following ERA5 variables were selected:\n",
    "- 2m temperature\n",
    "- 10m u-component of wind\n",
    "- 10m v-component of wind\n",
    "- total precipitation\n",
    "\n",
    "## Output\n",
    "The final output is a cleaned CSV dataset saved in the processed data folder for future modelling and analysis."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "0f725429-1ae6-4613-93cc-29431be2ead7",
   "metadata": {},
   "source": [
    "## Data Coverage\n",
    "\n",
    "The dataset covers the Black Summer bushfire period:\n",
    "- Start date: 1 January 2020  \n",
    "- End date: 29 February 2020  \n",
    "- Region: Victoria, Australia  \n",
    "\n",
    "This period includes some of the most severe bushfire conditions, making it suitable for analysis and modelling."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d6d319f6-c7d5-4246-b62d-fbb4527a9394",
   "metadata": {},
   "source": [
    "## 1. Import Required Libraries\n",
    "\n",
    "This step imports the necessary Python libraries for:\n",
    "- handling NetCDF data (`xarray`)\n",
    "- data manipulation (`pandas`)\n",
    "- numerical computations (`numpy`)"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "c12f1c0d-1926-400f-a8ff-da3dd4dee14e",
   "metadata": {},
   "outputs": [],
   "source": [
    "import xarray as xr\n",
    "import pandas as pd\n",
    "import numpy as np"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "fd3fa3cc-2f40-484d-bbba-dd5252e2d096",
   "metadata": {},
   "source": [
    "## 2. Load ERA5 Raw Data\n",
    "\n",
    "Load the raw ERA5 NetCDF files:\n",
    "- Accumulated data (precipitation)\n",
    "- Instantaneous data (temperature and wind)\n",
    "\n",
    "These files were downloaded from the ECMWF Climate Data Store."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "1242c641-47ca-434c-a3b6-a78fc29729e2",
   "metadata": {},
   "outputs": [],
   "source": [
    "ds1 = xr.open_dataset(r\"C:\\Users\\shubham sharma\\Downloads\\capstone\\data\\raw\\data_stream-oper_stepType-accum.nc\")\n",
    "ds2 = xr.open_dataset(r\"C:\\Users\\shubham sharma\\Downloads\\capstone\\data\\raw\\data_stream-oper_stepType-instant.nc\")"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "8f63c052-9729-4098-9bf4-29df67440dd4",
   "metadata": {},
   "source": [
    "## 3. Merge Datasets\n",
    "\n",
    "Combine the accumulated and instantaneous datasets into a single dataset\n",
    "so that all required variables are available together."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "1e238ca3-3170-4ae3-9d49-2caeb02baaf3",
   "metadata": {},
   "outputs": [],
   "source": [
    "combined = xr.merge([ds1, ds2])"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d1ba8349-e5f0-4d1f-9e19-3664d794860c",
   "metadata": {},
   "source": [
    "## 4. Convert to Tabular Format\n",
    "\n",
    "Convert the multidimensional dataset (time, latitude, longitude)\n",
    "into a flat tabular structure suitable for analysis and modelling."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 4,
   "id": "7212da48-2bbb-46b5-ba30-c46079c4e3e1",
   "metadata": {},
   "outputs": [],
   "source": [
    "df = combined.to_dataframe().reset_index()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "aa1f1183-b41f-4024-97ac-dcf63009f203",
   "metadata": {},
   "source": [
    "## 5. Remove Unnecessary Columns\n",
    "\n",
    "Drop columns that are not required for analysis:\n",
    "- number\n",
    "- expver\n",
    "\n",
    "This simplifies the dataset."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 5,
   "id": "11069410-8f06-4910-80d4-0554a0668ea0",
   "metadata": {},
   "outputs": [],
   "source": [
    "df = df.drop(columns=[\"number\", \"expver\"])"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "3710dd4a-8b36-4314-8b80-0818af4c07cc",
   "metadata": {},
   "source": [
    "## 6. Rename Columns\n",
    "\n",
    "Rename columns to more intuitive and readable names for easier understanding and usage."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 6,
   "id": "3253e91d-b6ca-4b49-8425-30e1833876df",
   "metadata": {},
   "outputs": [],
   "source": [
    "df = df.rename(columns={\n",
    "    \"valid_time\": \"datetime\",\n",
    "    \"latitude\": \"lat\",\n",
    "    \"longitude\": \"lon\",\n",
    "    \"tp\": \"precipitation\",\n",
    "    \"u10\": \"wind_u\",\n",
    "    \"v10\": \"wind_v\",\n",
    "    \"t2m\": \"temperature\"\n",
    "})"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "57a98d12-f3e5-4930-a809-750ef61f2f59",
   "metadata": {},
   "source": [
    "## 7. Convert Units\n",
    "\n",
    "Convert raw ERA5 units into more interpretable units:\n",
    "- Temperature: Kelvin → Celsius\n",
    "- Precipitation: meters → millimeters"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 7,
   "id": "a375926a-b425-4931-8027-bfcb5cf46433",
   "metadata": {},
   "outputs": [],
   "source": [
    "df[\"temperature\"] = df[\"temperature\"] - 273.15\n",
    "df[\"precipitation\"] = df[\"precipitation\"] * 1000"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "97a17d0a-b403-4aef-af35-0bd89706e0da",
   "metadata": {},
   "source": [
    "## 8. Feature Engineering\n",
    "\n",
    "Create additional useful features:\n",
    "- Wind speed calculated from u and v wind components\n",
    "- Convert datetime column to proper datetime format"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 8,
   "id": "c49184e8-aecf-48fe-a93a-df8e3154995d",
   "metadata": {},
   "outputs": [],
   "source": [
    "df[\"wind_speed\"] = np.sqrt(df[\"wind_u\"]**2 + df[\"wind_v\"]**2)\n",
    "df[\"datetime\"] = pd.to_datetime(df[\"datetime\"])"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "caac1b6a-2a1e-4fc8-b895-610a68cc3610",
   "metadata": {},
   "source": [
    "## 9. Save Processed Data\n",
    "\n",
    "Save the cleaned and processed dataset as a CSV file\n",
    "for further analysis, modelling, or database storage."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 9,
   "id": "4407afa1-c079-47cb-a1ad-366320ae6cfd",
   "metadata": {},
   "outputs": [],
   "source": [
    "df.to_csv(r\"C:\\Users\\shubham sharma\\Downloads\\capstone\\data\\processed\\era5_victoria_jan2020_clean.csv\", index=False)"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "7d1b49b2-9972-42c3-8955-d7e3a266436c",
   "metadata": {},
   "source": [
    "## 10. Preview Final Dataset\n",
    "\n",
    "Display the first few rows of the processed dataset\n",
    "to verify the transformations."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 10,
   "id": "b7dec2a8-aa73-4b03-b9c9-12ddc3ac876e",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<div>\n",
       "<style scoped>\n",
       "    .dataframe tbody tr th:only-of-type {\n",
       "        vertical-align: middle;\n",
       "    }\n",
       "\n",
       "    .dataframe tbody tr th {\n",
       "        vertical-align: top;\n",
       "    }\n",
       "\n",
       "    .dataframe thead th {\n",
       "        text-align: right;\n",
       "    }\n",
       "</style>\n",
       "<table border=\"1\" class=\"dataframe\">\n",
       "  <thead>\n",
       "    <tr style=\"text-align: right;\">\n",
       "      <th></th>\n",
       "      <th>datetime</th>\n",
       "      <th>lat</th>\n",
       "      <th>lon</th>\n",
       "      <th>precipitation</th>\n",
       "      <th>wind_u</th>\n",
       "      <th>wind_v</th>\n",
       "      <th>temperature</th>\n",
       "      <th>wind_speed</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>0</th>\n",
       "      <td>2020-01-01</td>\n",
       "      <td>-33.0</td>\n",
       "      <td>140.00</td>\n",
       "      <td>0.0</td>\n",
       "      <td>-0.745239</td>\n",
       "      <td>3.549850</td>\n",
       "      <td>21.792389</td>\n",
       "      <td>3.627233</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>1</th>\n",
       "      <td>2020-01-01</td>\n",
       "      <td>-33.0</td>\n",
       "      <td>140.25</td>\n",
       "      <td>0.0</td>\n",
       "      <td>-0.502075</td>\n",
       "      <td>3.829147</td>\n",
       "      <td>21.979889</td>\n",
       "      <td>3.861923</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>2</th>\n",
       "      <td>2020-01-01</td>\n",
       "      <td>-33.0</td>\n",
       "      <td>140.50</td>\n",
       "      <td>0.0</td>\n",
       "      <td>-0.290161</td>\n",
       "      <td>3.915085</td>\n",
       "      <td>22.296295</td>\n",
       "      <td>3.925822</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>3</th>\n",
       "      <td>2020-01-01</td>\n",
       "      <td>-33.0</td>\n",
       "      <td>140.75</td>\n",
       "      <td>0.0</td>\n",
       "      <td>-0.254028</td>\n",
       "      <td>3.873093</td>\n",
       "      <td>22.716217</td>\n",
       "      <td>3.881414</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>4</th>\n",
       "      <td>2020-01-01</td>\n",
       "      <td>-33.0</td>\n",
       "      <td>141.00</td>\n",
       "      <td>0.0</td>\n",
       "      <td>-0.196411</td>\n",
       "      <td>3.851608</td>\n",
       "      <td>23.118561</td>\n",
       "      <td>3.856613</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "    datetime   lat     lon  precipitation    wind_u    wind_v  temperature  \\\n",
       "0 2020-01-01 -33.0  140.00            0.0 -0.745239  3.549850    21.792389   \n",
       "1 2020-01-01 -33.0  140.25            0.0 -0.502075  3.829147    21.979889   \n",
       "2 2020-01-01 -33.0  140.50            0.0 -0.290161  3.915085    22.296295   \n",
       "3 2020-01-01 -33.0  140.75            0.0 -0.254028  3.873093    22.716217   \n",
       "4 2020-01-01 -33.0  141.00            0.0 -0.196411  3.851608    23.118561   \n",
       "\n",
       "   wind_speed  \n",
       "0    3.627233  \n",
       "1    3.861923  \n",
       "2    3.925822  \n",
       "3    3.881414  \n",
       "4    3.856613  "
      ]
     },
     "execution_count": 10,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "df.head()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "ea6ee35c-61fa-4e0b-b238-16a5f8402a90",
   "metadata": {},
   "source": [
    "## Conclusion\n",
    "\n",
    "This notebook successfully transformed raw ERA5 NetCDF files into a clean tabular dataset. The processing included merging datasets, converting units, renaming variables, and deriving wind speed. The final dataset is ready for exploratory analysis, feature integration, and use by the AI Modelling and Backend streams in the FireFusion project."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "76ec474a-7423-40b2-980e-54fa3128d54f",
   "metadata": {},
   "source": [
    "## Data Validation and Exploration\n",
    "\n",
    "To ensure the processed dataset is reliable for downstream modelling,\n",
    "basic exploratory data analysis (EDA) was performed. This includes:\n",
    "\n",
    "- Checking statistical summaries\n",
    "- Inspecting distributions of key variables\n",
    "- Validating temporal trends\n",
    "\n",
    "These checks help confirm that the dataset is consistent and suitable for bushfire risk analysis."
   ]
  },
  {
   "cell_type": "markdown",
   "id": "509aa1fa-412c-4507-bc79-f8b455127663",
   "metadata": {},
   "source": [
    "### Summary Statistics\n",
    "\n",
    "The dataset contains approximately 762,600 observations covering multiple spatial grid points across Victoria.\n",
    "\n",
    "- Temperature ranges from ~4°C to ~46°C, with an average of ~22°C, which is consistent with summer conditions during the bushfire period.\n",
    "- Wind speed has a mean of ~4.08 m/s, with higher values indicating conditions that could contribute to fire spread.\n",
    "- Precipitation is highly skewed, with a median of 0 mm and most values at 0, reflecting predominantly dry conditions during the study period.\n",
    "\n",
    "Overall, the statistical summary indicates that the dataset is realistic and aligns with expected weather patterns during the Black Summer bushfires."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 11,
   "id": "a39ae2d9-32a7-4399-b049-d1fd4aa89720",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/html": [
       "<div>\n",
       "<style scoped>\n",
       "    .dataframe tbody tr th:only-of-type {\n",
       "        vertical-align: middle;\n",
       "    }\n",
       "\n",
       "    .dataframe tbody tr th {\n",
       "        vertical-align: top;\n",
       "    }\n",
       "\n",
       "    .dataframe thead th {\n",
       "        text-align: right;\n",
       "    }\n",
       "</style>\n",
       "<table border=\"1\" class=\"dataframe\">\n",
       "  <thead>\n",
       "    <tr style=\"text-align: right;\">\n",
       "      <th></th>\n",
       "      <th>lat</th>\n",
       "      <th>lon</th>\n",
       "      <th>precipitation</th>\n",
       "      <th>wind_u</th>\n",
       "      <th>wind_v</th>\n",
       "      <th>temperature</th>\n",
       "      <th>wind_speed</th>\n",
       "    </tr>\n",
       "  </thead>\n",
       "  <tbody>\n",
       "    <tr>\n",
       "      <th>count</th>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "      <td>762600.000000</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>mean</th>\n",
       "      <td>-36.000000</td>\n",
       "      <td>145.000000</td>\n",
       "      <td>0.061288</td>\n",
       "      <td>0.104339</td>\n",
       "      <td>1.047130</td>\n",
       "      <td>22.094734</td>\n",
       "      <td>4.089723</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>std</th>\n",
       "      <td>1.802777</td>\n",
       "      <td>2.958042</td>\n",
       "      <td>0.320122</td>\n",
       "      <td>3.221179</td>\n",
       "      <td>3.273957</td>\n",
       "      <td>7.310225</td>\n",
       "      <td>2.341145</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>min</th>\n",
       "      <td>-39.000000</td>\n",
       "      <td>140.000000</td>\n",
       "      <td>0.000000</td>\n",
       "      <td>-14.034378</td>\n",
       "      <td>-15.830994</td>\n",
       "      <td>4.293121</td>\n",
       "      <td>0.005544</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>25%</th>\n",
       "      <td>-37.500000</td>\n",
       "      <td>142.500000</td>\n",
       "      <td>0.000000</td>\n",
       "      <td>-1.819534</td>\n",
       "      <td>-1.085739</td>\n",
       "      <td>16.620026</td>\n",
       "      <td>2.426506</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>50%</th>\n",
       "      <td>-36.000000</td>\n",
       "      <td>145.000000</td>\n",
       "      <td>0.000000</td>\n",
       "      <td>-0.015900</td>\n",
       "      <td>1.234093</td>\n",
       "      <td>20.460602</td>\n",
       "      <td>3.611984</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>75%</th>\n",
       "      <td>-34.500000</td>\n",
       "      <td>147.500000</td>\n",
       "      <td>0.000000</td>\n",
       "      <td>1.941635</td>\n",
       "      <td>3.238987</td>\n",
       "      <td>26.899628</td>\n",
       "      <td>5.249406</td>\n",
       "    </tr>\n",
       "    <tr>\n",
       "      <th>max</th>\n",
       "      <td>-33.000000</td>\n",
       "      <td>150.000000</td>\n",
       "      <td>13.830662</td>\n",
       "      <td>15.708374</td>\n",
       "      <td>14.276657</td>\n",
       "      <td>46.320465</td>\n",
       "      <td>16.484665</td>\n",
       "    </tr>\n",
       "  </tbody>\n",
       "</table>\n",
       "</div>"
      ],
      "text/plain": [
       "                 lat            lon  precipitation         wind_u  \\\n",
       "count  762600.000000  762600.000000  762600.000000  762600.000000   \n",
       "mean      -36.000000     145.000000       0.061288       0.104339   \n",
       "std         1.802777       2.958042       0.320122       3.221179   \n",
       "min       -39.000000     140.000000       0.000000     -14.034378   \n",
       "25%       -37.500000     142.500000       0.000000      -1.819534   \n",
       "50%       -36.000000     145.000000       0.000000      -0.015900   \n",
       "75%       -34.500000     147.500000       0.000000       1.941635   \n",
       "max       -33.000000     150.000000      13.830662      15.708374   \n",
       "\n",
       "              wind_v    temperature     wind_speed  \n",
       "count  762600.000000  762600.000000  762600.000000  \n",
       "mean        1.047130      22.094734       4.089723  \n",
       "std         3.273957       7.310225       2.341145  \n",
       "min       -15.830994       4.293121       0.005544  \n",
       "25%        -1.085739      16.620026       2.426506  \n",
       "50%         1.234093      20.460602       3.611984  \n",
       "75%         3.238987      26.899628       5.249406  \n",
       "max        14.276657      46.320465      16.484665  "
      ]
     },
     "execution_count": 11,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "df.describe()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "d21994ed-dc14-460d-b8c6-5edb7b29cbb4",
   "metadata": {},
   "source": [
    "### Temperature Distribution\n",
    "\n",
    "The temperature distribution is right-skewed, with most values concentrated between 15°C and 30°C. \n",
    "\n",
    "This indicates that the majority of observations fall within typical summer temperature ranges in Victoria. However, the presence of higher temperatures (above 35°C) is significant, as such extreme heat conditions are strongly associated with increased bushfire risk and intensity."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 12,
   "id": "00553ea7-ee22-4c55-8a76-350a76a6746e",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "image/png": "iVBORw0KGgoAAAANSUhEUgAAAjoAAAGxCAYAAABr1xxGAAAAOXRFWHRTb2Z0d2FyZQBNYXRwbG90bGliIHZlcnNpb24zLjUuMiwgaHR0cHM6Ly9tYXRwbG90bGliLm9yZy8qNh9FAAAACXBIWXMAAA9hAAAPYQGoP6dpAAA6XklEQVR4nO3df1yV9f3/8ecJ4QgEJ34IRxaalSMNtT5aiK6JQyFDbHN92j40PtrK3DSNqWs5b5u4KZi/ctNZZqYudeyHWU2Ngat0DjRlH5aaHz/tO38uEFMERTuc8Pr+0Yfr0+EgchQELh73241bXe/rdc71vq43P56+rx/HZhiGIQAAAAu6qa07AAAA0FoIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOuh0bDZbs77ee++9tu5qm9m2bZuys7PbuhuNWrt2rcc4de3aVU6nU8OHD1dubq4qKiq8XpOdnS2bzebTdi5evKjs7Gyfvw8a29Ztt92m0aNH+/Q+V7Nx40YtXbq00XU2m61Nx+9nP/uZ+vbtq8uXL5ttJ0+eVEpKioKCgjR06FAdOnSo0df+8Y9/VHp6uqKjoxUQEKDw8HAlJydrw4YNcrvdkqTKykrdcssteuONN27E7qCDI+ig0ykuLvb4euihhxQYGOjV/m//9m9t3dU2s23bNs2ZM6etu9GkNWvWqLi4WIWFhfrVr36le+65R88//7z69Omj7du3e9Q++eSTKi4u9un9L168qDlz5vgcdK5lW9eiqaBTXFysJ598stX70JiPP/5YCxYs0M9+9jPddNP//YmZMGGCoqOj9fbbb2vw4MH693//d4/XGYahxx9/XGPGjNHly5e1ZMkSbd++XevWrdOAAQM0adIkrVixQpIUFhamH/zgB/rhD3+o2traG7p/6IAMoJMbN26cERwc3NbdaFU1NTU+1U+ePNlojV8PvvajMWvWrDEkGXv37vVad+zYMSM2NtYICQkxysvLr2s7p0+fNiQZs2fPblZ9U/vWs2dPIy0t7br601BaWprRs2fPFn3PlvDss88aX/rSl4y6ujqP9uDgYKOqqspcDgsLMz755BNz+fnnnzckGXPmzGn0fcvKyoy//OUv5nJ5ebnRpUsXY8OGDS28B7AaZnSARtTW1mru3Lm66667ZLfb1a1bNz3++OM6ffq0R139KYktW7bo3nvvVWBgoPr06aMtW7ZI+vw0S58+fRQcHKz7779f+/bt83j9+PHjdfPNN+vgwYNKTk5WcHCwunXrpqeffloXL170qDUMQytWrNA999yjwMBAhYWF6ZFHHtE///lPj7qkpCTFx8dr586dGjJkiIKCgvTd735XkvTb3/5WKSkp6t69u9nX5557TjU1NR59+tWvfiXJ8zTf0aNHdfToUdlsNq1du9brmDU8XVJ/Cudvf/ubHnnkEYWFhemOO+7waV981aNHDy1evFjnz5/XypUrvfryRe+8846SkpIUERGhwMBA9ejRQ9/85jd18eJFHT16VN26dZMkzZkzxzwG48ePv+q+NXWabPPmzerfv7+6du2q22+/Xb/85S891tefljt69KhH+3vvvedxOjUpKUlbt27VsWPHPMaoXmOnrg4cOKCHH35YYWFh6tq1q+655x6tW7eu0e385je/0axZsxQTE6PQ0FCNGDFChw8fvvKB/1+1tbVavXq1MjIyPGZzJOmOO+7QihUrVF1drfXr18vf31/h4eGSJLfbreeff1533XWXfvKTnzT63k6nU1/5ylfM5ejoaI0cOVIvvfTSVfuFzo2gAzRw+fJlPfzww5o/f74yMjK0detWzZ8/X4WFhUpKStKlS5c86v/+979r5syZ+tGPfqTXX39dDodDY8eO1ezZs/XKK68oJydHGzZsUFVVlUaPHu31erfbrYceekjJycl644039PTTT2vlypX61re+5VE3ceJEZWVlacSIEXrjjTe0YsUKHTx4UEOGDNGpU6c8asvKyvSd73xHGRkZ2rZtmyZNmiRJ+uijj/TQQw9p9erVys/PV1ZWln73u98pPT3dfO1PfvITPfLII5I8T/N17979mo7n2LFjdeedd+r3v/+9+UfJl33x1UMPPSQ/Pz/t3LnzijVHjx5VWlqaAgIC9Oqrryo/P1/z589XcHCwamtr1b17d+Xn50uSnnjiCfMYNPwj3Ni+XUlpaamysrL0gx/8QJs3b9aQIUP0zDPPaNGiRT7v44oVKzR06FA5nU6PMbqSw4cPa8iQITp48KB++ctf6vXXX1ffvn01fvx4LViwwKv+xz/+sY4dO6ZXXnlFL7/8sj766COlp6errq6uyX7t2bNHZ86c0fDhwxvt8wsvvCCHw6EpU6aYoU6S9u3bp7Nnz+rhhx/26VqqpKQk/fWvf9W5c+ea/Rp0Qm09pQS0tYanrn7zm98YkoxNmzZ51O3du9eQZKxYscJs69mzpxEYGGicPHnSbCstLTUkGd27d/c4nfHGG28Ykoy33nrLY9uSjF/84hce25o3b54hydi1a5dhGIZRXFxsSDIWL17sUXfixAkjMDDQePbZZ822YcOGGZKMP//5z03u9+XLlw23223s2LHDkGT8/e9/N9dd6dTVkSNHDEnGmjVrvNapwWme2bNnG5KMn/70px51vuxLY5o6dVUvOjra6NOnj1df6v3hD38wJBmlpaVXfI+mTl1dad8a25ZhfP59YrPZvLY3cuRIIzQ01Pw+qd+3I0eOeNS9++67hiTj3XffNduaOnXVsN/f/va3Dbvdbhw/ftyjbtSoUUZQUJBx7tw5j+089NBDHnW/+93vDElGcXFxo9urV3/66UqnDT/99FPj0KFDxsWLFz3a8/LyDEnGSy+91OT7N1RYWGhIMt5++22fXofOhRkdoIEtW7bolltuUXp6uj777DPz65577pHT6fS6OPWee+7Rl770JXO5T58+kj7/12ZQUJBX+7Fjx7y2+dhjj3ksZ2RkSJLeffdds082m03f+c53PPrkdDo1YMAArz6FhYXpa1/7mtd2/vnPfyojI0NOp1N+fn7y9/fXsGHDJOmKd8Fcr29+85sey77uy7UwDKPJ9ffcc48CAgL01FNPad26ddd8yqzhvjXl7rvv1oABAzzaMjIyVF1drb/97W/XtP3meuedd5ScnKzY2FiP9vHjx+vixYtes0FjxozxWO7fv7+kxr93v+jjjz+WzWZTZGRko+vtdrvuuusuBQYG+roLjYqKipIk/etf/2qR94M1dWnrDgDtzalTp3Tu3DkFBAQ0uv6TTz7xWK6/zqBe/euu1P7pp596tHfp0kUREREebU6nU5J05swZs0+GYSg6OrrRPt1+++0ey42dZrpw4YIeeOABde3aVXPnztWXv/xlBQUF6cSJExo7dqzXKbWW0rAvvu6Lr2pqanTmzBn169fvijV33HGHtm/frgULFmjy5MmqqanR7bffrqlTp+qZZ55p9rZ8OZ1XP6aNtdWPc2s5c+ZMo32NiYlpdPsNvx/tdrskXfV75NKlS/L395efn59P/evRo4ck6ciRIz69rmvXrs3qFzo3gg7QQGRkpCIiIsxrNBoKCQlp0e199tlnOnPmjMcfl/Lyckn/9wcnMjJSNptNf/nLX8w/Ol/UsK2x6xzeeecdffzxx3rvvffMWRxJPl3fUP+HxeVyebQ39Ye6YV983Rdfbd26VXV1dUpKSmqy7oEHHtADDzyguro67du3T8uWLVNWVpaio6P17W9/u1nb8uV6kvoxbaytfpyvdHwbhmtfRUREqKyszKv9448/lqQrzsD4KjIyUrW1taqpqVFwcHCzXzdo0CCFh4frzTffVG5ubrOP69mzZ83tAlfCqSuggdGjR+vMmTOqq6vToEGDvL7i4uJafJsbNmzwWN64caMkmX+sR48eLcMw9K9//avRPjU1e1Gv/o9HwyDxxbuT6l3pX/DR0dHq2rWrPvjgA4/2N99886rbr9cS+3Ilx48f14wZM+RwODRx4sRmvcbPz08JCQnmnWb1p5GaO4vRXAcPHtTf//53j7aNGzcqJCTEfGbTbbfdJklex/ett97yej+73d7sviUnJ5tB94t+/etfKygoSIMHD27ubjTprrvukiT9v//3/3x6nb+/v370ox/pv//7v/Xzn/+80ZqKigr99a9/9WirP+XYt2/fa+gtOgtmdIAGvv3tb2vDhg166KGH9Mwzz+j++++Xv7+/Tp48qXfffVcPP/ywvvGNb7TY9gICArR48WJduHBB9913n4qKijR37lyNGjXKvJ126NCheuqpp/T4449r3759+upXv6rg4GCVlZVp165d6tevn77//e83uZ0hQ4YoLCxM3/ve9zR79mz5+/trw4YNXn98JZlh4/nnn9eoUaPk5+en/v37KyAgQN/5znf06quv6o477tCAAQP0/vvvm8GsOVpiX6TPb5euv76noqJCf/nLX7RmzRr5+flp8+bN5u3hjXnppZf0zjvvKC0tTT169NCnn36qV199VZI0YsQISZ/P3PXs2VNvvvmmkpOTFR4ersjISDOM+ComJkZjxoxRdna2unfvrvXr16uwsFDPP/+8eS3Xfffdp7i4OM2YMUOfffaZwsLCtHnzZu3atcvr/fr166fXX39dL774ogYOHKibbrpJgwYNanTbs2fP1pYtWzR8+HD99Kc/VXh4uDZs2KCtW7dqwYIFcjgc17RPDdUH8927d5vX9TTXD3/4Qx06dEizZ8/W+++/r4yMDMXGxqqqqko7d+7Uyy+/rDlz5mjo0KHma3bv3q2IiIjrCsfoBNr0UmigHWjsgYFut9tYtGiRMWDAAKNr167GzTffbNx1113GxIkTjY8++sisu9KD4CQZkydP9mirv2Np4cKFXtv+4IMPjKSkJCMwMNAIDw83vv/97xsXLlzwet9XX33VSEhIMIKDg43AwEDjjjvuMP7zP//T2Ldvn1kzbNgw4+677250X4uKiozExEQjKCjI6Natm/Hkk08af/vb37zupHK5XMaTTz5pdOvWzbDZbB53AlVVVRlPPvmkER0dbQQHBxvp6enG0aNHr3jX1enTpxvtS3P2pTH1dybVfwUEBBhRUVHGsGHDjJycHKOiosLrNQ3vhCouLja+8Y1vGD179jTsdrsRERFhDBs2zOOOOMMwjO3btxv33nuvYbfbDUnGuHHjrrpvV7rrKi0tzfjDH/5g3H333UZAQIBx2223GUuWLPF6/f/8z/8YKSkpRmhoqNGtWzdjypQpxtatW73uujp79qzxyCOPGLfccos5RvUajoVhGMb+/fuN9PR0w+FwGAEBAcaAAQO87p6rv+vq97//vUd7U3fbNfTAAw943bXlizfffNNIS0szunXrZnTp0sUICwszhg8fbrz00kuGy+Uy6y5fvmz07NnTmDJlyjVvC52DzTCucnsCgFYzfvx4/eEPf9CFCxfauitAi9i0aZO+9a1v6dixYx53I7a0P//5z0pJSdHBgwfNU2ZAY7hGBwDQYsaOHav77rtPubm5rbqduXPn6rvf/S4hB1dF0AEAtBibzaZVq1YpJibG49PLW1JlZaWGDRumefPmtcr7w1o4dQUAACyLGR0AAGBZBB0AAGBZBB0AAGBZnfqBgZcvX9bHH3+skJAQnx7lDgAA2o5hGDp//rxiYmJ0001Nz9l06qDz8ccfe32aLwAA6BhOnDihW2+9tcmaTh106j+c8cSJEwoNDW3j3nR8brdbBQUFSklJkb+/f1t3B01grDoOxqpjYbxujOrqasXGxjbrQ5Y7ddCpP10VGhpK0GkBbrdbQUFBCg0N5Qe8nWOsOg7GqmNhvG6s5lx2wsXIAADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsrq0dQeAzui257Zetebo/LQb0BMAsDZmdAAAgGX5FHSys7Nls9k8vpxOp7neMAxlZ2crJiZGgYGBSkpK0sGDBz3ew+VyacqUKYqMjFRwcLDGjBmjkydPetRUVlYqMzNTDodDDodDmZmZOnfunEfN8ePHlZ6eruDgYEVGRmrq1Kmqra31cfcBAICV+Tyjc/fdd6usrMz82r9/v7luwYIFWrJkiZYvX669e/fK6XRq5MiROn/+vFmTlZWlzZs3Ky8vT7t27dKFCxc0evRo1dXVmTUZGRkqLS1Vfn6+8vPzVVpaqszMTHN9XV2d0tLSVFNTo127dikvL0+bNm3S9OnTr/U4AAAAC/L5Gp0uXbp4zOLUMwxDS5cu1axZszR27FhJ0rp16xQdHa2NGzdq4sSJqqqq0urVq/Xaa69pxIgRkqT169crNjZW27dvV2pqqg4dOqT8/Hzt3r1bCQkJkqRVq1YpMTFRhw8fVlxcnAoKCvThhx/qxIkTiomJkSQtXrxY48eP17x58xQaGnrNBwQAAFiHz0Hno48+UkxMjOx2uxISEpSTk6Pbb79dR44cUXl5uVJSUsxau92uYcOGqaioSBMnTlRJSYncbrdHTUxMjOLj41VUVKTU1FQVFxfL4XCYIUeSBg8eLIfDoaKiIsXFxam4uFjx8fFmyJGk1NRUuVwulZSUaPjw4Y323eVyyeVymcvV1dWSJLfbLbfb7euhQAP1x5BjeXV2P+OqNa15HBmrjoOx6lgYrxvDl+PrU9BJSEjQr3/9a335y1/WqVOnNHfuXA0ZMkQHDx5UeXm5JCk6OtrjNdHR0Tp27Jgkqby8XAEBAQoLC/OqqX99eXm5oqKivLYdFRXlUdNwO2FhYQoICDBrGpObm6s5c+Z4tRcUFCgoKOhqu49mKiwsbOsutHsL7r96zbZt21q9H4xVx8FYdSyMV+u6ePFis2t9CjqjRo0y/79fv35KTEzUHXfcoXXr1mnw4MGSJJvN5vEawzC82hpqWNNY/bXUNDRz5kxNmzbNXK6urlZsbKxSUlI43dUC3G63CgsLNXLkSPn7+7d1d9pMfPafWuR9DmSntsj7NIax6jgYq46F8box6s/INMd1PUcnODhY/fr100cffaSvf/3rkj6fbenevbtZU1FRYc6+OJ1O1dbWqrKy0mNWp6KiQkOGDDFrTp065bWt06dPe7zPnj17PNZXVlbK7XZ7zfR8kd1ul91u92r39/fnG7IFdfbj6aprOtg31404hp19rDoSxqpjYbxaly/H9rqeo+NyuXTo0CF1795dvXr1ktPp9Jiuq62t1Y4dO8wQM3DgQPn7+3vUlJWV6cCBA2ZNYmKiqqqq9P7775s1e/bsUVVVlUfNgQMHVFZWZtYUFBTIbrdr4MCB17NLAADAQnya0ZkxY4bS09PVo0cPVVRUaO7cuaqurta4ceNks9mUlZWlnJwc9e7dW71791ZOTo6CgoKUkZEhSXI4HHriiSc0ffp0RUREKDw8XDNmzFC/fv3Mu7D69OmjBx98UBMmTNDKlSslSU899ZRGjx6tuLg4SVJKSor69u2rzMxMLVy4UGfPntWMGTM0YcIETkEBAACTT0Hn5MmT+o//+A998skn6tatmwYPHqzdu3erZ8+ekqRnn31Wly5d0qRJk1RZWamEhAQVFBQoJCTEfI8XXnhBXbp00aOPPqpLly4pOTlZa9eulZ+fn1mzYcMGTZ061bw7a8yYMVq+fLm53s/PT1u3btWkSZM0dOhQBQYGKiMjQ4sWLbqugwEAAKzFp6CTl5fX5Hqbzabs7GxlZ2dfsaZr165atmyZli1bdsWa8PBwrV+/vslt9ejRQ1u2bGmyBgAAdG581hUAALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALCsLm3dAQCNu+25rVetOTo/7Qb0BAA6LmZ0AACAZRF0AACAZRF0AACAZRF0AACAZRF0AACAZV1X0MnNzZXNZlNWVpbZZhiGsrOzFRMTo8DAQCUlJengwYMer3O5XJoyZYoiIyMVHBysMWPG6OTJkx41lZWVyszMlMPhkMPhUGZmps6dO+dRc/z4caWnpys4OFiRkZGaOnWqamtrr2eXAACAhVxz0Nm7d69efvll9e/f36N9wYIFWrJkiZYvX669e/fK6XRq5MiROn/+vFmTlZWlzZs3Ky8vT7t27dKFCxc0evRo1dXVmTUZGRkqLS1Vfn6+8vPzVVpaqszMTHN9XV2d0tLSVFNTo127dikvL0+bNm3S9OnTr3WXAACAxVxT0Llw4YIee+wxrVq1SmFhYWa7YRhaunSpZs2apbFjxyo+Pl7r1q3TxYsXtXHjRklSVVWVVq9ercWLF2vEiBG69957tX79eu3fv1/bt2+XJB06dEj5+fl65ZVXlJiYqMTERK1atUpbtmzR4cOHJUkFBQX68MMPtX79et17770aMWKEFi9erFWrVqm6uvp6jwsAALCAa3pg4OTJk5WWlqYRI0Zo7ty5ZvuRI0dUXl6ulJQUs81ut2vYsGEqKirSxIkTVVJSIrfb7VETExOj+Ph4FRUVKTU1VcXFxXI4HEpISDBrBg8eLIfDoaKiIsXFxam4uFjx8fGKiYkxa1JTU+VyuVRSUqLhw4d79dvlcsnlcpnL9YHI7XbL7XZfy6HAF9Qfw85+LO1+xg3b1rUea8aq42CsOhbG68bw5fj6HHTy8vJUUlKiffv2ea0rLy+XJEVHR3u0R0dH69ixY2ZNQECAx0xQfU3968vLyxUVFeX1/lFRUR41DbcTFhamgIAAs6ah3NxczZkzx6u9oKBAQUFBjb4GvissLGzrLrSpBfffuG1t27btul7f2ceqI2GsOhbGq3VdvHix2bU+BZ0TJ07omWeeUUFBgbp27XrFOpvN5rFsGIZXW0MNaxqrv5aaL5o5c6amTZtmLldXVys2NlYpKSkKDQ1tsn+4OrfbrcLCQo0cOVL+/v5t3Z1WEZ/9p7bugocD2anX9LrOMFZWwVh1LIzXjeHLJSo+BZ2SkhJVVFRo4MCBZltdXZ127typ5cuXm9fPlJeXq3v37mZNRUWFOfvidDpVW1uryspKj1mdiooKDRkyxKw5deqU1/ZPnz7t8T579uzxWF9ZWSm32+0101PPbrfLbrd7tfv7+/MN2YKsfDxddU0H9hvteo+zlcfKahirjoXxal2+HFufLkZOTk7W/v37VVpaan4NGjRIjz32mEpLS3X77bfL6XR6TNnV1tZqx44dZogZOHCg/P39PWrKysp04MABsyYxMVFVVVV6//33zZo9e/aoqqrKo+bAgQMqKyszawoKCmS32z2CGAAA6Lx8mtEJCQlRfHy8R1twcLAiIiLM9qysLOXk5Kh3797q3bu3cnJyFBQUpIyMDEmSw+HQE088oenTpysiIkLh4eGaMWOG+vXrpxEjRkiS+vTpowcffFATJkzQypUrJUlPPfWURo8erbi4OElSSkqK+vbtq8zMTC1cuFBnz57VjBkzNGHCBE5DAQAASdd411VTnn32WV26dEmTJk1SZWWlEhISVFBQoJCQELPmhRdeUJcuXfToo4/q0qVLSk5O1tq1a+Xn52fWbNiwQVOnTjXvzhozZoyWL19urvfz89PWrVs1adIkDR06VIGBgcrIyNCiRYtaepcAAEAHdd1B57333vNYttlsys7OVnZ29hVf07VrVy1btkzLli27Yk14eLjWr1/f5LZ79OihLVu2+NJdAADQifBZVwAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLIIOgAAwLJa/Dk6AG6c257betWao/PTbkBPAKB9YkYHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYVpe27gCA1nXbc1u92ux+hhbcL8Vn/0muOpuOzk9rg54BQOtjRgcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWQQcAAFgWT0YG/ldjTxAGAHRszOgAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADL4rOuADTrc76Ozk+7AT0BgJbFjA4AALAsgg4AALAsgg4AALAsgg4AALAsn4LOiy++qP79+ys0NFShoaFKTEzU22+/ba43DEPZ2dmKiYlRYGCgkpKSdPDgQY/3cLlcmjJliiIjIxUcHKwxY8bo5MmTHjWVlZXKzMyUw+GQw+FQZmamzp0751Fz/PhxpaenKzg4WJGRkZo6dapqa2t93H0AAGBlPgWdW2+9VfPnz9e+ffu0b98+fe1rX9PDDz9shpkFCxZoyZIlWr58ufbu3Sun06mRI0fq/Pnz5ntkZWVp8+bNysvL065du3ThwgWNHj1adXV1Zk1GRoZKS0uVn5+v/Px8lZaWKjMz01xfV1entLQ01dTUaNeuXcrLy9OmTZs0ffr06z0eAADAQny6vTw9Pd1jed68eXrxxRe1e/du9e3bV0uXLtWsWbM0duxYSdK6desUHR2tjRs3auLEiaqqqtLq1av12muvacSIEZKk9evXKzY2Vtu3b1dqaqoOHTqk/Px87d69WwkJCZKkVatWKTExUYcPH1ZcXJwKCgr04Ycf6sSJE4qJiZEkLV68WOPHj9e8efMUGhp63QcGAAB0fNf8HJ26ujr9/ve/V01NjRITE3XkyBGVl5crJSXFrLHb7Ro2bJiKioo0ceJElZSUyO12e9TExMQoPj5eRUVFSk1NVXFxsRwOhxlyJGnw4MFyOBwqKipSXFyciouLFR8fb4YcSUpNTZXL5VJJSYmGDx/eaJ9dLpdcLpe5XF1dLUlyu91yu93Xeijwv+qPYUc9lnY/o627cMPYbzI8/tscHXVcO7qO/nPV2TBeN4Yvx9fnoLN//34lJibq008/1c0336zNmzerb9++KioqkiRFR0d71EdHR+vYsWOSpPLycgUEBCgsLMyrpry83KyJiory2m5UVJRHTcPthIWFKSAgwKxpTG5urubMmePVXlBQoKCgoKvtOpqpsLCwrbtwTRbc39Y9uPF+Puhys2u3bdvWij3B1XTUn6vOivFqXRcvXmx2rc9BJy4uTqWlpTp37pw2bdqkcePGaceOHeZ6m83mUW8YhldbQw1rGqu/lpqGZs6cqWnTppnL1dXVio2NVUpKCqe7WoDb7VZhYaFGjhwpf3//tu6Oz+Kz/9TWXbhh7DcZ+vmgy/rJvpvkutz0z2e9A9mprdwrNKaj/1x1NozXjVF/RqY5fA46AQEBuvPOOyVJgwYN0t69e/WLX/xCP/rRjyR9PtvSvXt3s76iosKcfXE6naqtrVVlZaXHrE5FRYWGDBli1pw6dcpru6dPn/Z4nz179nisr6yslNvt9prp+SK73S673e7V7u/vzzdkC+qox9NV17w/+Fbiumxr9n53xDG1ko76c9VZMV6ty5dje93P0TEMQy6XS7169ZLT6fSYrqutrdWOHTvMEDNw4ED5+/t71JSVlenAgQNmTWJioqqqqvT++++bNXv27FFVVZVHzYEDB1RWVmbWFBQUyG63a+DAgde7SwAAwCJ8mtH58Y9/rFGjRik2Nlbnz59XXl6e3nvvPeXn58tmsykrK0s5OTnq3bu3evfurZycHAUFBSkjI0OS5HA49MQTT2j69OmKiIhQeHi4ZsyYoX79+pl3YfXp00cPPvigJkyYoJUrV0qSnnrqKY0ePVpxcXGSpJSUFPXt21eZmZlauHChzp49qxkzZmjChAmcggIAACafgs6pU6eUmZmpsrIyORwO9e/fX/n5+Ro5cqQk6dlnn9WlS5c0adIkVVZWKiEhQQUFBQoJCTHf44UXXlCXLl306KOP6tKlS0pOTtbatWvl5+dn1mzYsEFTp041784aM2aMli9fbq738/PT1q1bNWnSJA0dOlSBgYHKyMjQokWLrutgAAAAa/Ep6KxevbrJ9TabTdnZ2crOzr5iTdeuXbVs2TItW7bsijXh4eFav359k9vq0aOHtmzZ0mQNAADo3PisKwAAYFnX/MBAAJ3Lbc9tvWrN0flpN6AnANB8zOgAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADLIugAAADL4rOuALQYPg8LQHvDjA4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsgg4AALAsPtQTwA3FB38CuJGY0QEAAJZF0AEAAJZF0AEAAJZF0AEAAJZF0AEAAJbFXVfoFJpzpw8AwHqY0QEAAJZF0AEAAJZF0AEAAJbFNToA2h2engygpTCjAwAALIugAwAALIugAwAALIugAwAALIugAwAALIugAwAALIugAwAALIugAwAALIsHBgLokHioIIDmYEYHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFkEHAABYFs/RAWBZPGsHADM6AADAsgg6AADAsgg6AADAsgg6AADAsgg6AADAsnwKOrm5ubrvvvsUEhKiqKgoff3rX9fhw4c9agzDUHZ2tmJiYhQYGKikpCQdPHjQo8blcmnKlCmKjIxUcHCwxowZo5MnT3rUVFZWKjMzUw6HQw6HQ5mZmTp37pxHzfHjx5Wenq7g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\n",
      "text/plain": [
       "<Figure size 640x480 with 1 Axes>"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "import matplotlib.pyplot as plt\n",
    "\n",
    "df[\"temperature\"].hist(bins=50)\n",
    "plt.title(\"Temperature Distribution (°C)\")\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "6baacaad-3581-4662-afa4-365415814d0e",
   "metadata": {},
   "source": [
    "### Wind Speed Distribution\n",
    "\n",
    "The wind speed distribution is right-skewed, with most values concentrated between 2 m/s and 6 m/s.\n",
    "\n",
    "While moderate wind speeds dominate the dataset, the presence of higher wind speeds (above 8 m/s) is important, as strong winds can significantly accelerate bushfire spread and increase fire intensity."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 13,
   "id": "1119d140-63bd-490c-a25c-1c76484b6811",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "image/png": "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/vrr3l4EBASYsWPHWuouXLhgoqKizNChQ40xxhQVFZmYmBjToUMHU1xc7K07cuSICQwMNC1atCj3HEvGfuedd5a5/i9/+YuRZH73u995l7Vo0cIMGzbM+3rgwIHmJz/5SbnHefXVV40kc/jwYZ91LVq0MP7+/ubgwYOlrvvhsUquibLO+emnn7acW/fu3X32OWzYMEtvTp8+bSSZl156yad26dKllnHn5+ebkJAQ079/f0vdsWPHjNPpNElJSZbjVORaBWoSMzpAFWrYsKHuvvtu74zOli1b5O/vr27dukmSunfv7r0v58r7c8rjcDg0aNAgy7K77rrL8vbKpk2bFBYWpsGDB1vqkpKSKjR2p9OpNWvWaP/+/Zo/f74effRRnT59Wq+88oratGmjgwcPWurLOlZxcbE+//xzSdLatWt18803a9CgQfruu++8Xz/5yU8UFRXl7dOGDRv03Xff6YknnrDUBQcHq3v37t66gwcP6uTJk0pKSrK8ldaiRQt17dq1Qud5NaYC9yLde++9+vvf/64xY8Zow4YN1/RE2l133aXbb7+9wvVlnfOV931VtaysLF2+fNnn7bRmzZrpZz/7mf73f//Xsrwi1ypQkwg6QBXr2bOnvvzyS508eVKbNm1Sx44dvfe9lNxXUVBQoE2bNikgIEA//elPr7rPBg0aKDg42LLM6XTq22+/9b4+c+aMIiMjfbaNioqq1PjbtGmjlJQUrVixQseOHdO8efN05swZn7c2yjvWmTNnJEmnTp3SuXPnFBQUpMDAQMtXbm6uvv76a2+dJN1zzz0+de+//763rmS/pZ1TZc+zLCX/IMfExJRZM2XKFM2ZM0fbtm1Tv3791LhxY/Xq1UtffPFFhY9T2aeayjrnkp5Ul5L9lzbemJgYn+NX5FoFahJPXQFVrGfPnpo3b542b96szZs3q3///t51JaHm888/996kXNbNv5XVuHFj7dixw2d5RW9GLo3D4dCvf/1r/fa3v9XevXst60rCSWnHaty4saTvn0Rr3Lix956QK5U83RURESHp+88iatGiRZnjKdlvaed0Pef5Q5988okcDofuv//+MmsCAgI0fvx4jR8/XufOndPGjRv1wgsvKDExUcePH1eDBg2uepwfzs5URFnnXNITSQoODvZ5NF6SNyhei5L9//AG+xInT570/t0BNypmdIAqdv/9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\n",
      "text/plain": [
       "<Figure size 640x480 with 1 Axes>"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "df[\"wind_speed\"].hist(bins=50)\n",
    "plt.title(\"Wind Speed Distribution\")\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "3e4d056e-e0ea-4c35-b1cb-8359bc92aeca",
   "metadata": {},
   "source": [
    "### Precipitation Summary\n",
    "\n",
    "Precipitation values are highly skewed, with the majority of observations being 0 mm, as indicated by the median and lower quartiles.\n",
    "\n",
    "This reflects predominantly dry conditions during the study period, which is typical during bushfire seasons. Occasional higher precipitation values are present, representing isolated rainfall events that may temporarily reduce fire risk."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 14,
   "id": "0536aafb-d2b4-4928-b8f7-8c2cbda88db5",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "text/plain": [
       "count    762600.000000\n",
       "mean          0.061288\n",
       "std           0.320122\n",
       "min           0.000000\n",
       "25%           0.000000\n",
       "50%           0.000000\n",
       "75%           0.000000\n",
       "max          13.830662\n",
       "Name: precipitation, dtype: float64"
      ]
     },
     "execution_count": 14,
     "metadata": {},
     "output_type": "execute_result"
    }
   ],
   "source": [
    "df[\"precipitation\"].describe()"
   ]
  },
  {
   "cell_type": "markdown",
   "id": "f59463a5-1400-4af6-9956-8db6688168a7",
   "metadata": {},
   "source": [
    "### Temperature Trend Over Time\n",
    "\n",
    "The temperature trend shows clear daily fluctuations, reflecting typical diurnal patterns with warmer daytime and cooler nighttime temperatures.\n",
    "\n",
    "An overall increase in temperature can be observed towards the end of the month, with peaks exceeding 35°C. Such sustained high-temperature periods are critical factors contributing to heightened bushfire risk during the Black Summer."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 15,
   "id": "b1cf43a0-1df7-440c-9e49-cd4a1c87e6b2",
   "metadata": {},
   "outputs": [
    {
     "data": {
      "image/png": "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+MEP4pprrvF8zMqVKw/wq2IYhtGDAxuGYRhFLr30UvzgBz9AsVjEaaeddkCe8/bbb8cnP/lJ8e877rgDgCVno9f0la98BTt37sQf//Efaz0HbcIrA4dvf/vbMx5Lj5mcnER9fb34+cKFC1FXV1fmIgYAP//5z6VfR9T3cv311+Pee+/FJz7xCdx9991lwUuxWMTHP/5xmKaJv/u7vyv7f3/yJ3+CT33qU7jtttuwadMmLF68GBdddJH4/eGHH47DDjsML774Ir785S8rv65apKGhAeeffz6ef/55HHvssb5VSIZhmLkABzYMwzCKvO9978Ptt9+Oiy++GH/1V3+FU089Fel0Gjt27MBDDz2Eyy+/HO9+97tje75MJoObbroJY2NjOOWUU/DEE0/gi1/8It75znfi7LPPBgCcddZZ+NjHPoarr74aa9euxbnnnovGxkbs3r0bjz32GI455hh8/OMfD3yeM888E+3t7fiLv/gLfP7zn0c6ncbtt9+OF198ccZjjznmGADAv/zLv+Cd73wnksmk2Bh/4AMfwH//939j1apVOO644/D000+LQEyGqO/lrLPOwte+9jVcd911OPvss3Httddi2bJlYkDn73//e3zta1/DmWeeWfb/2tra8O53vxu33XYbhoaG8OlPfxqJRHkr6re//W28853vxNvf/nZcddVVWLx4MQYGBvDaa6/hueeew49+9CPp91krfP3rX8fZZ5+Nc845Bx//+MexYsUKjI6OYuPGjfjlL385YzAtwzBMrcKBDcMwjCLJZBK/+MUv8PWvfx3f+973cOONNyKVSmHJkiV4y1veIjb9cZFOp3HPPffgk5/8JL74xS+ivr4eH/3oR/H//X//X9njvv3tb+P000/Ht7/9bdx8880olUpYtGgRzjrrLJx66qmhz9PZ2Ylf/epX+Ou//mt84AMfQGNjIy6//HLcddddOPHEE8see+WVV+Lxxx/HzTffjC984QswTRObN2/GihUrcNNNNwEAvvrVr2JsbAwXXHAB7rnnHqxYsUL6PUd9L3/5l3+JU045BTfddBP++q//Gv39/ejo6MDZZ5+Nxx57DGeccYbn/7v66qtx5513ArDm9VRy/vnn4+mnn8aXvvQlXHfddRgcHERnZyfWrFmjXSmbbdasWYPnnnsO//zP/4zPfe5z2Lt3L9ra2nDYYYfh4osv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jJCQEPz1r3/F7NmzERkZiZKSErz44ov4+eefcdtttzlx1NTTLVu2DO+88w4++OAD6PV6JTNjMBjg5+cHQRCwatUqPPHEE0hMTERiYiKeeOIJ9OrVCwsXLnTy6Kkn6+izK6uoqMD777+PZ555xllDJVciEjnYCy+8IMbGxore3t7isGHDxOzsbJvnt23bJiYkJIi+vr5iamqquGvXLieNlMjiwIEDIoAWX3fffbdYW1srzps3T4yKihK9vb3FyMhIcfbs2eLXX3/t7GFTD9faZxaAuH37duU1JpNJfOyxx8SIiAjRx8dHTE9PF0+cOOG8QROJnfvsiqIobt26VfTz8xPLysqcM1ByKexjQ0REREREmsc9NkREREREpHkMbIiIiIiISPMY2BARERERkeYxsCEiIiIiIs1jYENERERERJrHwIaIiIiIiDSPgQ0REREREWkeAxsiIiIiItI8BjZERERERKR5DGyIiIiIiEjzGNgQEREREZHmMbAhIiIiIiLNY2BDRERERESax8CGiIiIiIg0j4ENERERERFpHgMbIiIiIiLSPAY2RERERESkeQxsiIiIiIhI8xjYEBERERGR5jGwISIiIiIizWNgQ0REREREmsfAhoiIiIiINI+BDRERERERaZ7DA5slS5Zg7ty5jj4tERERERG5MWZsiIiIiIhI85wa2OzduxcTJkxA7969ERISgltuuQUXLlxQnr948SIEQcCOHTuQkZGBXr16ITU1FYcPH3biqImIiIiIyNU4NbCprq7GmjVrkJOTg88//xw6nQ7z5s2DyWSyed3DDz+MtWvXIjc3F0lJSfjNb36DpqYmJ42aiIiIiIhcjaczT37rrbfa/H3btm0wGo344YcfkJKSojy+du1azJw5EwDw+OOPY9CgQTh//jwGDBjg0PESEREREZFrcmrG5sKFC1i4cCH69euHwMBAxMfHAwDy8/NtXjdkyBDlz5GRkQCAoqIixw2UiIiIiIhcmlMzNrNmzUJ0dDReeeUVREVFwWQyISUlBQ0NDTav8/LyUv4sCAIAtFiuRkREREREPZfTApuSkhKcOnUKW7duxcSJEwEABw8edNZwiIiIiIhIw5wW2AQFBSEkJAQvv/wyIiMjkZ+fj4ceeshZwyEiIiIiIg1z+B4bk8kET09P6HQ6vPvuuzh69ChSUlKwevVqPPXUU44eDhER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\n",
      "text/plain": [
       "<Figure size 1000x400 with 1 Axes>"
      ]
     },
     "metadata": {},
     "output_type": "display_data"
    }
   ],
   "source": [
    "daily = df.groupby(\"datetime\")[\"temperature\"].mean()\n",
    "\n",
    "daily.plot(figsize=(10,4), title=\"Temperature Over Time\")\n",
    "plt.show()"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "474837a5-e81a-4050-ac73-98306bda5865",
   "metadata": {},
   "outputs": [],
   "source": []
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3 (ipykernel)",
   "language": "python",
   "name": "python3"
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
   "version": "3.9.13"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
