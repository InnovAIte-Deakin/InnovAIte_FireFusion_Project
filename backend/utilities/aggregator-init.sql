--
-- PostgreSQL database dump
--

\restrict vmFrgWNggEkBY5gr2frrRGm2gWTK1nxb1FzqiiqAcAj02aWAw13P3Y08vbTp4kI

-- Dumped from database version 18.1 (Homebrew)
-- Dumped by pg_dump version 18.1 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: at_risk_infrastructure; Type: TABLE; Schema: public; Owner: darbata
--

CREATE TABLE public.at_risk_infrastructure (
    facility_id integer NOT NULL,
    facility_name text,
    category text,
    latitude real,
    longitude real,
    lga text
);


ALTER TABLE public.at_risk_infrastructure OWNER TO darbata;

--
-- Name: fire_events; Type: TABLE; Schema: public; Owner: darbata
--

CREATE TABLE public.fire_events (
    event_id integer NOT NULL,
    weather_id integer,
    topo_id integer,
    fuel_id integer,
    facility_id integer,
    latitude real,
    longitude real,
    event_date date,
    confidence_score integer,
    source_system text
);


ALTER TABLE public.fire_events OWNER TO darbata;

--
-- Name: fuel_and_vegetation; Type: TABLE; Schema: public; Owner: darbata
--

CREATE TABLE public.fuel_and_vegetation (
    fuel_id integer NOT NULL,
    latitude real,
    longitude real,
    record_date date,
    vegetation_class text,
    dyrness_index real,
    soil_moisture real
);


ALTER TABLE public.fuel_and_vegetation OWNER TO darbata;

--
-- Name: topography; Type: TABLE; Schema: public; Owner: darbata
--

CREATE TABLE public.topography (
    topo_id integer NOT NULL,
    latitude real,
    longitude real,
    elevation_meters real,
    slope_angle real
);


ALTER TABLE public.topography OWNER TO darbata;

--
-- Name: weather_conditions; Type: TABLE; Schema: public; Owner: darbata
--

CREATE TABLE public.weather_conditions (
    weather_id integer NOT NULL,
    latitude real,
    longitude real,
    record_date timestamp without time zone,
    temperature_c real,
    wind_speed_kmh real,
    relative_humidity real
);


ALTER TABLE public.weather_conditions OWNER TO darbata;

--
-- Name: at_risk_infrastructure at_risk_infrastructure_pkey; Type: CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.at_risk_infrastructure
    ADD CONSTRAINT at_risk_infrastructure_pkey PRIMARY KEY (facility_id);


--
-- Name: fire_events fire_events_pkey; Type: CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fire_events
    ADD CONSTRAINT fire_events_pkey PRIMARY KEY (event_id);


--
-- Name: fuel_and_vegetation fuel_and_vegetation_pkey; Type: CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fuel_and_vegetation
    ADD CONSTRAINT fuel_and_vegetation_pkey PRIMARY KEY (fuel_id);


--
-- Name: topography topography_pkey; Type: CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.topography
    ADD CONSTRAINT topography_pkey PRIMARY KEY (topo_id);


--
-- Name: weather_conditions weather_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.weather_conditions
    ADD CONSTRAINT weather_conditions_pkey PRIMARY KEY (weather_id);


--
-- Name: fire_events fire_events_facility_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fire_events
    ADD CONSTRAINT fire_events_facility_id_fkey FOREIGN KEY (facility_id) REFERENCES public.at_risk_infrastructure(facility_id);


--
-- Name: fire_events fire_events_fuel_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fire_events
    ADD CONSTRAINT fire_events_fuel_id_fkey FOREIGN KEY (fuel_id) REFERENCES public.fuel_and_vegetation(fuel_id);


--
-- Name: fire_events fire_events_topo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fire_events
    ADD CONSTRAINT fire_events_topo_id_fkey FOREIGN KEY (topo_id) REFERENCES public.topography(topo_id);


--
-- Name: fire_events fire_events_weather_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: darbata
--

ALTER TABLE ONLY public.fire_events
    ADD CONSTRAINT fire_events_weather_id_fkey FOREIGN KEY (weather_id) REFERENCES public.weather_conditions(weather_id);


--
-- PostgreSQL database dump complete
--

\unrestrict vmFrgWNggEkBY5gr2frrRGm2gWTK1nxb1FzqiiqAcAj02aWAw13P3Y08vbTp4kI

