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

from django.db import models


class SystemNotice(models.Model):
    """
    Object representing a System Notice
    """
    NOTICE_TYPES = (
        ('alert-success', 'Success (green)'),
        ('alert-info', 'Info (blue)'),
        ('alert-warning', 'Warning (yellow)'),
        ('alert-danger', 'Danger (red)')
    )
    type = models.CharField(choices=NOTICE_TYPES, max_length=100)
    heading = models.CharField(max_length=48)
    message = models.CharField(max_length=1024)
    show_on = models.DateTimeField()
    hide_on = models.DateTimeField()

    def __str__(self):
        return self.heading


class BlogPost(models.Model):
    """
    Object representing an update/blog post
    """
    title = models.CharField(max_length=48)
    message = models.TextField()
    post_on = models.DateTimeField()

    def __str__(self):
        return self.title
