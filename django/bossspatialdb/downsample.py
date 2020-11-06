# Copyright 2020 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import boto3
from django.conf import settings
from django.http import HttpResponse
import json

from bosscore.error import BossError, BossHTTPError, BossParserError, ErrorCodes
from bosscore.models import Channel
import bossutils
from bossutils.aws import get_account_id, get_region, get_session
from bossutils.configuration import BossConfig

DOWNSAMPLE_CANNOT_BE_QUEUED_ERR_MSG = 'Downsample already queued or in progress'

def start(request, resource):
    """Main code to start a downsample

    Args:
        request: DRF Request object
        resource (BossResourceDjango): The channel to downsample

    Returns:
        (HttpResponse)
    """

    channel = resource.get_channel()
    chan_status = channel.downsample_status.upper()
    if chan_status == Channel.DownsampleStatus.IN_PROGRESS:
        return BossHTTPError("Channel is currently being downsampled. Invalid Request.", ErrorCodes.INVALID_STATE)
    elif chan_status == Channel.DownsampleStatus.QUEUED:
        return BossHTTPError("Channel is already waiting to be downsampled. Invalid Request.", ErrorCodes.INVALID_STATE)
    elif chan_status == Channel.DownsampleStatus.DOWNSAMPLED and not request.user.is_staff:
        return BossHTTPError("Channel is already downsampled. Invalid Request.", ErrorCodes.INVALID_STATE)

    if request.user.is_staff:
        # DP HACK: allow admin users to override the coordinate frame
        frame = request.data
    else:
        frame = {}

    boss_config = BossConfig()
    collection = resource.get_collection()
    experiment = resource.get_experiment()
    coord_frame = resource.get_coord_frame()
    lookup_key = resource.get_lookup_key()
    col_id, exp_id, ch_id = lookup_key.split("&")

    def get_frame(idx):
        return int(frame.get(idx, getattr(coord_frame, idx)))

    downsample_sfn = boss_config['sfn']['downsample_sfn']
    db_host = boss_config['aws']['db']

    args = {
        'lookup_key': lookup_key,
        'collection_id': int(col_id),
        'experiment_id': int(exp_id),
        'channel_id': int(ch_id),
        'annotation_channel': not channel.is_image(),
        'data_type': resource.get_data_type(),

        's3_bucket': boss_config["aws"]["cuboid_bucket"],
        's3_index': boss_config["aws"]["s3-index-table"],

        'x_start': get_frame('x_start'),
        'y_start': get_frame('y_start'),
        'z_start': get_frame('z_start'),

        'x_stop': get_frame('x_stop'),
        'y_stop': get_frame('y_stop'),
        'z_stop': get_frame('z_stop'),

        'resolution': int(channel.base_resolution),
        'resolution_max': int(experiment.num_hierarchy_levels),
        'res_lt_max': int(channel.base_resolution) + 1 < int(experiment.num_hierarchy_levels),

        'type': experiment.hierarchy_method,
        'iso_resolution': int(resource.get_isotropic_level()),

        # This step function executes: boss-tools/activities/resolution_hierarchy.py
        'downsample_volume_lambda': boss_config['lambda']['downsample_volume'],

        # Need to pass step function's ARN to itself, so it can start another
        # instance of itself after finishing a downsample.
        'sfn_arn': downsample_sfn,

        'db_host': db_host,
        'aws_region': get_region(),
    }

    # Check that only administrators are triggering extra large downsamples
    if ((not request.user.is_staff) and
       ((args['x_stop'] - args['x_start']) *\
        (args['y_stop'] - args['y_start']) *\
        (args['z_stop'] - args['z_start']) > settings.DOWNSAMPLE_MAX_SIZE)):
        return BossHTTPError("Large downsamples require admin permissions to trigger. Invalid Request.", ErrorCodes.INVALID_STATE)

    session = get_session()

    downsample_sqs = boss_config['aws']['downsample-queue']

    try:
        enqueue_job(session, args, downsample_sqs)
    except BossError as be:
        return BossHTTPError(be.message, be.error_code)

    compute_usage_metrics(session, args, boss_config['system']['fqdn'],
                          request.user.username,
                          collection.name, experiment.name, channel.name)

    region = get_region()
    account_id = get_account_id()
    downsample_sfn_arn = f'arn:aws:states:{region}:{account_id}:stateMachine:{downsample_sfn}'
    if not check_for_running_sfn(session, downsample_sfn_arn):
        bossutils.aws.sfn_run(session, downsample_sfn_arn,
                              {
                                  'queue_url': downsample_sqs,
                                  'sfn_arn': downsample_sfn_arn,
                              })

    return HttpResponse(status=201)

def enqueue_job(session, args, downsample_sqs):
    """Enqueue downsample job

    Args:
        session (boto3.session):
        args (dict): Arguments passed to the downsample step function via SQS
        downsample_sqs (str): URL of SQS queue

    Raises:
        (BossError): If failed to enqueue job.
    """
    rows_updated = (Channel.objects
        .filter(id=args['channel_id'])
        .exclude(downsample_status=Channel.DownsampleStatus.IN_PROGRESS)
        .exclude(downsample_status=Channel.DownsampleStatus.QUEUED)
        .update(downsample_status=Channel.DownsampleStatus.QUEUED)
        )
    if rows_updated == 0:
        raise BossError(DOWNSAMPLE_CANNOT_BE_QUEUED_ERR_MSG, ErrorCodes.BAD_REQUEST)

    _sqs_enqueue(session, args, downsample_sqs)

def _sqs_enqueue(session, args, downsample_sqs):
    """Do the actual SQS enqueue.

    This is a separate function so it can be easily mocked out in tests.

    Args:
        session (boto3.session):
        args (dict): Arguments passed to the downsample step function via SQS
        downsample_sqs (str): URL of SQS queue

    Raises:
        (BossError): If failed to enqueue job.
    """
    client = session.client('sqs')
    client.send_message(QueueUrl=downsample_sqs, MessageBody=json.dumps(args))

def check_for_running_sfn(session, arn):
    """Check if a downsample step function already running

    Args:
        session (boto3.session):
        arn (str): Step function arn

    Returns:
        (bool)
    """
    client = session.client('stepfunctions')
    resp = client.list_executions(stateMachineArn=arn, statusFilter='RUNNING', maxResults=1)
    return 'executions' in resp and len(resp['executions']) > 0

def compute_usage_metrics(session, args, fqdn, user,
                          collection, experiment, channel):
    """Add metrics to cloudwatch

    Args:
        session (boto3.session):
        args (dict): contains [x|y|z]_[start|stop] for computing extents
        fqdn (str): fully qualified domain name of the endpoint
        user (str): name of user invoking downsample
        collection (str): name of collection
        experiment (str): name of experiment
        channel (str): name of channel
    """

    def get_cubes(axis, dim):
        extent = args['{}_stop'.format(axis)] - args['{}_start'.format(axis)]
        return -(-extent // dim) ## ceil div

    cost = (  get_cubes('x', 512)
            * get_cubes('y', 512)
            * get_cubes('z', 16)
            / 4 # number of cubes for a downsampled volume
            * 0.75 # assume the frame is only 75% filled
            * 2 # 1 for invoking a lambda
                # 1 for time it takes lambda to run
            * 1.33 # add 33% overhead for all other non-base resolution downsamples
           )

    dimensions = [
        {'Name': 'user', 'Value': user},
        {'Name': 'resource', 'Value': '{}/{}/{}'.format(collection, experiment, channel)},
        {'Name': 'stack', 'Value': fqdn},
    ]

    client = session.client('cloudwatch')
    client.put_metric_data(
        Namespace = "BOSS/Downsample",
        MetricData = [{
            'MetricName': 'InvokeCount',
            'Dimensions': dimensions,
            'Value': 1.0,
            'Unit': 'Count'
        }, {
            'MetricName': 'ComputeCost',
            'Dimensions': dimensions,
            'Value': cost,
            'Unit': 'Count'
        }]
    )

def delete_queued_job(session, chan_id):
    """Removed the given job from the downsample queue

    Args:
        session (boto3.session):
        chan_id (int): Channel id.

    Returns:
        (bool): True if job successfully removed from queue.
    """
    done = False
    ok = True

    # Put these messages back on the queue.
    msgs_to_return = []

    while not done:
        # Put these messages back on the queue.
        msgs = _get_messages_from_queue(session)
        if len(msgs) == 0:
            done = True
            ok = False
            break

        return_batch = []

        ind = 1
        for m in msgs:
            job = json.loads(m['Body'])
            if job['channel_id'] == chan_id:
                try:
                    _delete_message_from_queue(session, m['ReceiptHandle'])
                except Exception:
                    ok = False
                done = True
            else:
                return_batch.append({
                    f'ChangeMessageVisibilityBatchRequestEntry.{ind}.Id': m['MessageId'],
                    f'ChangeMessageVisibilityBatchRequestEntry.{ind}.ReceiptHandle': m['ReceiptHandle'],
                    f'ChangeMessageVisibilityBatchRequestEntry.{ind}.VisibilityTimeout': 0
                })
                ind += 1

        msgs_to_return.append(return_batch)

    # Return any messages we received while looking for the one to remove.
    for batch in msgs_to_return:
        try:
            if len(batch) > 0:
                _return_messages_to_queue(session, batch)
        except Exception:
            # Keep trying to return the rest of the messages and let the ones
            # that failed return when they time out, normally.
            pass

    return ok

def _return_messages_to_queue(session, batch):
    """Return given messages to the queue

    Args:
        session (boto3.session):
        batch (List[dict]): Message's receipt handle.

    Returns:

    Raises:
    """
    boss_config = BossConfig()
    downsample_sqs = boss_config['aws']['downsample-queue']
    client = session.client('sqs')
    # Don't check for failures because all messages will eventually be returned
    # automatically.
    client.change_message_visibility_batch(QueueUrl=downsample_sqs, Entries=batch)

def _delete_message_from_queue(session, msg_handle):
    """Delete given message from the queue

    Args:
        session (boto3.session):
        msg_handle (str): Message's receipt handle.

    Returns:

    Raises:
    """
    boss_config = BossConfig()
    downsample_sqs = boss_config['aws']['downsample-queue']
    client = session.client('sqs')
    client.delete_message(QueueUrl=downsample_sqs, ReceiptHandle=msg_handle)

def _get_messages_from_queue(session):
    """ Get up to 10 messages from the downsample queue

    Args:
        session (boto3.session):

    Returns:
        (List[dict]): List of messages from the queue.
    """
    boss_config = BossConfig()
    downsample_sqs = boss_config['aws']['downsample-queue']
    client = session.client('sqs')
    resp = client.receive_message(QueueUrl=downsample_sqs, WaitTimeSeconds=2, MaxNumberOfMessages=10)
    if 'Messages' in resp:
        return resp['Messages']
    return []
