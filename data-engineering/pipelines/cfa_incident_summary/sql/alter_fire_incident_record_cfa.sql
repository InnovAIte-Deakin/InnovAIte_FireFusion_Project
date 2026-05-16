-- Extend Fire_Incident_Record for CFA Incident Summary historical load.
-- Preserves hub FKs (location_id, time_id) and adds CFA-specific attributes.

ALTER TABLE Fire_Incident_Record
    ADD COLUMN IF NOT EXISTS district_no INTEGER,
    ADD COLUMN IF NOT EXISTS incident_type_code REAL,
    ADD COLUMN IF NOT EXISTS incident_type TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fire_incident_record_district_no_fkey'
    ) THEN
        ALTER TABLE Fire_Incident_Record
            ADD CONSTRAINT fire_incident_record_district_no_fkey
            FOREIGN KEY (district_no) REFERENCES CFA_District_Registry(district_no);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_fire_incident_record_district_no
    ON Fire_Incident_Record(district_no);

CREATE INDEX IF NOT EXISTS idx_fire_incident_record_time_location
    ON Fire_Incident_Record(time_id, location_id);
