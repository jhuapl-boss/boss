import json

def setup_ingest(ingest_config_data):
    """

    Args:
        ingest_config_data:

    Returns:

    """

    # Validate schema ?


    config_dict = json.loads(ingest_config_data)
    print (config_dict)

def delete_ingest_job(ingest_job_id):
    """

    Args:
        ingest_job_id:

    Returns:

    """
    return ingest_job_id


