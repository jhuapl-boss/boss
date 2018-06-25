from bosscore.error import BossError, ErrorCodes, BossResourceNotFoundError
import boto3
import json
from ingestclient.core.backend import BossBackend
from ndingest.nddynamo.boss_tileindexdb import BossTileIndexDB, MAX_TASK_ID_SUFFIX, TASK_INDEX
from ndingest.ndingestproj.bossingestproj import BossIngestProj
from ndingest.ndqueue.uploadqueue import UploadQueue
import os
from tempfile import NamedTemporaryFile

# First value should be job id.
CSV_FORMAT_STR = 'tiles-{}&'

# SQS Hardlimit
SQS_BATCH_SIZE = 10
SQS_RETRY_TIMEOUT = 15

def query_tile_index(job_id, tile_index_name, region):
    """
    Find all chunks belonging to a job and output those that have more than
    10 tiles to a .csv file named by the job_id.

    Args:
        job_id (int): Id of ingest job.
        tile_index_name (str): Name of DynamoDB tile index table.

    Returns:
        (str|None): Filename of list of chunks that meet criteria or None.
    """
    client = boto3.client('dynamodb', region_name=region)

    paginator = client.get_paginator('query')
    work_to_do = False

    with NamedTemporaryFile(
        mode='wt',
        prefix=CSV_FORMAT_STR.format(job_id),
        suffix='.csv',
        delete=False
    ) as output_csv:
        output_file = output_csv.name
        for i in range(MAX_TASK_ID_SUFFIX):
            response_iterator = _query_tile_index(paginator, tile_index_name, job_id, i)

            for response in response_iterator:
                for item in response["Items"]:
                    if len(item["tile_uploaded_map"]["M"]) > 10:
                        # If more than 10 tiles were uploaded we'll assume it's a missing block and reupload it
                        record = "{},{},{}\n".format(
                            item["chunk_key"]["S"], item["task_id"]["N"],
                            len(item["tile_uploaded_map"]["M"]))
                        output_csv.write(record)
                        work_to_do = True

    if not work_to_do:
        os.remove(output_file)
        return None

    return output_file

def _query_tile_index(paginator, tile_index_name, job_id, i):
    """
    Query tile index table for chunks with the given job_id and suffix.

    Args:
        paginator (boto3.Paginator):
        tile_index_name (str): Name of DynamoDB tile index table.
        job_id (int): Id of ingest job.
        i (int): Suffix for job_id (which Dynamo partition to check).

    Returns:
        (list[response])
    """
    return paginator.paginate(
        TableName=tile_index_name, 
        IndexName=TASK_INDEX,
        KeyConditionExpression="appended_task_id = :task_id_val",
        ExpressionAttributeValues={
            ":task_id_val": {
                "S": BossTileIndexDB.generate_appended_task_id(job_id, i)
            }
        }
    )

def patch_upload_queue(upload_queue, msg_args, csv_file):
    """
    Populate the upload queue with tile info.

    Args:
        upload_queue (SQS.Queue): Tile upload queue.
        msg_args (dict): Arguments to put in queue message.
        csv_file (str): Name of csv file with tile info.
    """

    msgs = _create_messages(msg_args, csv_file)
    sent = 0

    # Implement a custom queue.sendBatchMessages so that more than 10
    # messages can be sent at once (hard limit in sendBatchMessages)
    while True:
        batch = []
        for i in range(SQS_BATCH_SIZE):
            try:
                batch.append({
                    'Id': str(i),
                    'MessageBody': next(msgs),
                    'DelaySeconds': 0
                })
            except StopIteration:
                break

        if len(batch) == 0:
            break

        retry = 3
        while retry > 0:
            resp = upload_queue.send_messages(Entries=batch)
            sent += len(resp['Successful'])

            if 'Failed' in resp and len(resp['Failed']) > 0:
                time.sleep(SQS_RETRY_TIMEOUT)

                ids = [f['Id'] for f in resp['Failed']]
                batch = [b for b in batch if b['Id'] in ids]
                retry -= 1
                if retry == 0:
                    raise BossError("Failed trying to repopulate tile queue")
                continue
            else:
                break

def _create_messages(args, index_csv):
    """
    Create all of the tile messages to be enqueued.

    Args:
        args (dict): Same arguments as patch_upload_queue().
        index_csv (str): CSV file with tile info.

    Generates:
        (list): List of strings containing Json data
    """

    # DP NOTE: configuration is not actually used by encode_*_key method
    backend = BossBackend(None)

    chunk_key_list = []
    with open(index_csv, "rt") as data:
        lines = data.readlines()
        for line in lines:
            parts = line.split(",")
            chunk_key_list.append(parts[0])

    msgs = []
    for base_chunk_key in chunk_key_list:
        parts = backend.decode_chunk_key(base_chunk_key)
        chunk_x = parts['x_index']
        chunk_y = parts['y_index']
        chunk_z = parts['z_index']
        t = parts['t_index']

        num_of_tiles = parts['num_tiles']

        chunk_key = base_chunk_key
        z_start = chunk_z * args['z_chunk_size']

        for tile in range(z_start, z_start + num_of_tiles):
            tile_key = backend.encode_tile_key(args['project_info'],
                                               args['resolution'],
                                               chunk_x,
                                               chunk_y,
                                               tile,
                                               t)

            msg = {
                'job_id': args['job_id'],
                'upload_queue_arn': args['upload_queue'],
                'ingest_queue_arn': args['ingest_queue'],
                'chunk_key': chunk_key,
                'tile_key': tile_key,
            }

            yield json.dumps(msg)
