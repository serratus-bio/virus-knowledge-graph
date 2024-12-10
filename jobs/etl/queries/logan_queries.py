import os

from datasources.psql import (
    get_logan_connection,
    get_logan_write_connection,
)
from .serratus_queries import (
    get_query_results,
)


def get_biosample_df():
    query = """
        SELECT accession as biosample, title
        FROM public.biosample
    """
    return get_query_results(
        query=query,
        cache_filename="sql_biosample_nodes.csv",
        conn=get_logan_connection(),
    )


def get_bioproject_df():
    query = """
        SELECT accession as bioProject, name, title, description
        FROM public.bioproject
    """
    return get_query_results(
        query=query,
        cache_filename="sql_bioproject_nodes.csv",
        conn=get_logan_connection(),
    )


def get_biosample_sex_df():
    query = """
        SELECT biosample, sex
        FROM public.biosample_sex
    """
    return get_query_results(
        query=query,
        cache_filename="sql_biosample_sex.csv",
        conn=get_logan_connection(),
    )


def get_biosample_geo_df():
    query = """
        SELECT
            accession as biosample,
            attribute_name,
            attribute_value,
            gm4326_id,
            gp4326_wwf_tew_id
            CASE
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_01' THEN 'Tropical & Subtropical Moist Broadleaf Forests'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_02' THEN 'Tropical & Subtropical Dry Broadleaf Forests'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_03' THEN 'Tropical & Subtropical Coniferous Forests'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_04' THEN 'Temperate Broadleaf & Mixed Forests'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_05' THEN 'Temperate Conifer Forests'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_06' THEN 'Boreal Forests/Taiga'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_07' THEN 'Tropical & Subtropical Grasslands, Savannas & Shrublands'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_08' THEN 'Temperate Grasslands, Savannas & Shrublands'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_09' THEN 'Flooded Grasslands & Savannas'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_10' THEN 'Montane Grasslands & Shrublands'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_11' THEN 'Tundra'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_12' THEN 'Mediterranean Forests, Woodlands & Scrub'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_13' THEN 'Deserts & Xeric Shrublands'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_14' THEN 'Mangroves'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_98' THEN 'Ocean'
            WHEN gp4326_wwf_tew_id = 'WWF_TEW_BIOME_99' THEN 'Ocean'
            ELSE 'N/A'
            END AS biome_name
        FROM public.bgl_gm4326_gp4326
        WHERE palm_virome is TRUE
    """
    return get_query_results(
        query=query,
        cache_filename="sql_biosample_geo.csv",
        conn=get_logan_connection(),
    )


def write_biosample_disease():
    conn = get_logan_write_connection()
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS public.biosample_disease')
    cursor.execute('''
        CREATE TABLE public.biosample_disease (
            biosample VARCHAR,
            source VARCHAR,
            text VARCHAR,
            do_id VARCHAR,
            do_label VARCHAR
        )
    ''')
    conn.commit()

    filename = "/mnt/graphdata/ncbi-data/biosample_disease.csv"
    conn = get_logan_write_connection()

    cursor = conn.cursor()
    copy_sql = """
        COPY public.biosample_disease (biosample, source, text, do_id, do_label)
        FROM stdin WITH CSV HEADER
        DELIMITER as ','
    """
    with open(filename, 'r') as f:
        try:
            cursor.copy_expert(sql=copy_sql, file=f)
            conn.commit()
        except Exception as error:
            print("Error: %s" % error)
            conn.rollback()
            cursor.close()
            return error

    cursor.execute('''
        CREATE INDEX biosample_disease_biosample_idx
        ON public.biosample_disease (biosample)
    ''')
    conn.commit()

    conn.close()
    return True


def get_palm_virome_run_df():
    query = """
        SELECT DISTINCT run
        FROM public.palm_virome
    """
    return get_query_results(
        query=query,
        cache_filename="sql_palm_virome_run.csv",
        conn=get_logan_connection(),
    )


def get_palm_virome_sotu_df():
    query = """
        SELECT DISTINCT sotu
        FROM public.palm_virome
    """
    return get_query_results(
        query=query,
        cache_filename="sql_palm_virome_sotu.csv",
        conn=get_logan_connection(),
    )


def get_palm_virome_bioproject_df():
    query = """
        SELECT DISTINCT bio_project as bioproject
        FROM public.palm_virome
    """
    return get_query_results(
        query=query,
        cache_filename="sql_palm_virome_bioproject.csv",
        conn=get_logan_connection(),
    )