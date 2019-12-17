# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from bosscore.error import ErrorCodes
from rest_framework.renderers import JSONRenderer

def extract_context(*args, **kwargs):
    """General method for extracting the renderer_context

    Used by decorators to extract the renderer_context from the
    arguments of the method they are wrapping.

    The renderer_context is the 4th argument if not specified by keyword
    """
    if len(args) < 4 and kwargs is None:
        return None

    renderer_context = None
    if len(args) >= 4:
        renderer_context = args[3]
    elif kwargs is not None and 'renderer_context' in kwargs:
        renderer_context = kwargs['renderer_context']

    if renderer_context is None:
        return None

    # Check for presense of a Response object.
    if 'response' not in renderer_context:
        return None

    return renderer_context

def check_for_403(fcn):
    """Decorator to check renderer_context for a 403 response.

    Args:
        fcn (function): A custom BaseRenderer.render() implementation..

    Returns:
        (function): Wraps given function with one that checks for a 403 status.
    """

    def wrapper(*args, **kwargs):
        """Return a JSON response if a 403 found.

        Executes the custom renderer if no 403 status code found.

        Args:

        Returns:
            (BaseRenderer)
        """

        renderer_context = extract_context(*args, **kwargs)
        if renderer_context is None:
            return fcn(*args, **kwargs)

        # Have a response, check for 403.
        if renderer_context['response'].status_code == 403:
            renderer_context['response']['Content-Type'] = 'application/json'
            obj = args[0]
            obj.media_type = 'application/json'
            obj.format = 'json'
            err_msg = {"status": 403, "message": "Access denied, are you logged in?",
                       "code": ErrorCodes.ACCESS_DENIED_UNKNOWN}
            jr = JSONRenderer()
            return jr.render(err_msg, 'application/json', renderer_context)

        return fcn(*args, **kwargs)

    return wrapper

def check_for_429(fcn):
    """Decorator to check renderer_context for a 429 (Throttled) response.

    Args:
        fcn (function): A custom BaseRenderer.render() implementation..

    Returns:
        (function): Wraps given function with one that checks for a 429 status.
    """

    def wrapper(*args, **kwargs):
        """Return a JSON response if a 429 found.

        Executes the custom renderer if no 429 status code found.

        Args:

        Returns:
            (BaseRenderer)
        """

        renderer_context = extract_context(*args, **kwargs)
        if renderer_context is None:
            return fcn(*args, **kwargs)

        # Have a response, check for 429.
        if renderer_context['response'].status_code == 429:
            renderer_context['response']['Content-Type'] = 'application/json'
            err_msg = {"status": 429, "message": args[1]['detail'],
                       "code": ErrorCodes.ACCESS_DENIED_UNKNOWN}
            jr = JSONRenderer()
            return jr.render(err_msg, 'application/json', renderer_context)

        return fcn(*args, **kwargs)

    return wrapper

