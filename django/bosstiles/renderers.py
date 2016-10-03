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
import io
from rest_framework import renderers


class PNGRenderer(renderers.BaseRenderer):
    """ A DRF renderer for rendering an XY image as a png
    """
    media_type = 'image/png'
    format = 'png'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        file_obj = io.BytesIO()
        data.save(file_obj, "PNG")
        file_obj.seek(0)
        return file_obj.read()


class JPEGRenderer(renderers.BaseRenderer):
    """ A DRF renderer for rendering an XY image as a jpeg
    """
    media_type = 'image/jpeg'
    format = 'jpg'
    charset = None
    render_style = 'binary'

    def render(self, data, media_type=None, renderer_context=None):
        file_obj = io.BytesIO()
        data.save(file_obj, "JPEG")
        file_obj.seek(0)
        return file_obj.read()

