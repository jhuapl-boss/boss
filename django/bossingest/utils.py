import boto3

def get_sqs_num_msgs(url, region):
    """
    Get the approximate number of messages in the sqs queue.

    Args:
        url (str): The URL of the SQS queue.
        region (str): AWS region the queue lives in.

    Returns:
        (int): Approximate number of messages in the queue.
    """
    sqs = boto3.client('sqs', region)
    resp = sqs.get_queue_attributes(QueueUrl=url, AttributeNames=['ApproximateNumberOfMessages'])
    return int(resp['Attributes']['ApproximateNumberOfMessages'])
