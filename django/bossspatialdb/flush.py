# Methods to perform asynchronous flush operations
# This was pulled from spdb itself since it is not needed in Lambda run functions, and currently lambda runs python 3.4

import asyncio
import operator


async def get_single_object_async(spdb_instance, key, version, idx):
    """ Method to get multiple objects in parallel using coroutines

    Args:
        key_list (list(str)): A list of cached-cuboid keys to retrieve from the object store
        version: TBD version of the cuboid

    Returns:
        (list(bytes)): A list of blosc compressed cuboid data

    """
    data = spdb_instance.get_single_object(key, version)
    return idx, data


def get_objects_async(spdb_instance, key_list, version=None):
    """ Method to get multiple objects asyncronously using coroutines

    Args:
        key_list (list(str)): A list of cached-cuboid keys to retrieve from the object store
        version: TBD version of the cuboid

    Returns:
        (list(bytes)): A list of blosc compressed cuboid data

    """
    loop = asyncio.get_event_loop()

    tasks = []
    for idx, key in enumerate(key_list):
        task = asyncio.ensure_future(get_single_object_async(key, version, idx))
        tasks.append(task)

    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

    # Sort and cleanup results
    data = [x.result() for x in tasks]
    data.sort(key=operator.itemgetter(0))
    _, data = zip(*data)
    return data