-- Distinct species-like OTUs
SELECT *
FROM public.palmdb

-- Distinct scientific_name
SELECT DISTINCT scientific_name
FROM public.srarun

-- Distinct SRA
SELECT DISTINCT run
FROM srarun

-- palm_id to scientific_name mapping
SELECT DISTINCT scientific_name, palm_sra.palm_id
FROM palm_sra INNER JOIN srarun ON palm_sra.run_id = srarun.run

-- palm_id to run_id mapping
SELECT srarun.run, palm_id
FROM palm_sra INNER JOIN srarun ON palm_sra.run_id = srarun.run

