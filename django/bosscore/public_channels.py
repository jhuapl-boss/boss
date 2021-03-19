# Copyright 2021 The Johns Hopkins University Applied Physics Laboratory
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

# TODO SH Hack added frozenset to load the list of channels that should be made public.

import os

channels_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'public_channels.txt')

pub_ch_list = []
with open(channels_path, 'r') as f:
    pub_ch_list = [int(line) for line in f]

PUBLIC_CHANNELS = frozenset(pub_ch_list)
