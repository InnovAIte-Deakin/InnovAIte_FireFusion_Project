AI_FEATURE_NAMES = [
    "skin_temperature_c",
    "soil_temperature_level_1_c",
    "surface_solar_radiation_downwards",
    "surface_thermal_radiation_downwards",
    "temperature_2m_c",
    "u_component_of_wind_10m",
    "v_component_of_wind_10m",
]

AI_INPUT_STEPS = 60

# Deliberately incomplete until Data Engineering confirms the exact
# table/column mapping.
DE_TO_AI_FEATURE_MAPPING = {
    "temperature_2m_c": "temperature_c",

    # Still required from DE / AI confirmation:
    #
    # "skin_temperature_c": "...",
    # "soil_temperature_level_1_c": "...",
    # "surface_solar_radiation_downwards": "...",
    # "surface_thermal_radiation_downwards": "...",
    # "u_component_of_wind_10m": "...",
    # "v_component_of_wind_10m": "...",
}