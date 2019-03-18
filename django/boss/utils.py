# Copyright 2018 The Johns Hopkins University Applied Physics Laboratory
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

from bosscore.error import BossHTTPError, ErrorCodes

def get_access_mode(request):
    """
        Method to check the request parameters and define access_mode

        Args:
            request : url request

        Returns:
            access_mode (str) : Defines whether to use cache or not. Possible inputs are cache, no_cache or raw.
        
        Raises: 
            BossHTTPError if given invalid access-mode or no-cache values.

    """

    #Default access_mode to cache on the server side in case it is not explicitly defined in an API call. 
    access_mode = "cache"

    #Raise an error if both no-cache and access_mode are on the request URL
    if "no-cache" in request.query_params and "access-mode" in request.query_params:
        return BossHTTPError("access_mode and no-cache specified  in URL, please specify access_mode. no-cache will be deprecated.", ErrorCodes.INVALID_CUTOUT_ARGS)

    #Translation from no-cache boolean param to access_mode param for backwards compatability. 
    if "no-cache" in request.query_params:
        if request.query_params["no-cache"].lower() == "true":
            access_mode = "no_cache"
        elif request.query_params["no-cache"].lower() == "false":
            access_mode = "cache"
        else:
            return BossHTTPError("Incorrect no-cache value. Must be True or False.", ErrorCodes.INVALID_CUTOUT_ARGS)
            
    if "access-mode" in request.query_params:
        if request.query_params["access-mode"].lower() == "raw":
            access_mode = "raw"
        elif request.query_params["access-mode"].lower() == "no-cache":
            access_mode = "no_cache"
        elif request.query_params["access-mode"].lower() == "cache":
            access_mode = "cache"
        else:
            return BossHTTPError("Incorrect access_mode, possible values are [raw, no-cache, cache]", ErrorCodes.INVALID_CUTOUT_ARGS)
    return access_mode