# TEMPORARY FILE UNTIL CACHE INTEGRATED AND TESTS CAN BE WRITTEN #

import urllib.request
import urllib.parse
import blosc
import numpy as np

request = urllib.request.Request("http://52.90.247.23/v0.1/cutout/test/2/0:5/0:6/0:2")

# adding charset parameter to the Content-Type header.
request.add_header("Content-Type", "application/octet-stream")

a = np.random.randint(0, 100, (5, 6, 2))
h = a.tobytes()
bb = blosc.compress(h, typesize=8)

f = urllib.request.urlopen(request, bb)
print(f.read().decode('utf-8'))


request = urllib.request.Request("http://52.90.247.23/v0.1/cutout/col/exp/dataset/2/0:5/0:6/0:2")

# adding charset parameter to the Content-Type header.
request.add_header("Content-Type", "application/octet-stream")

a = np.random.randint(0, 100, (5, 6, 2))
h = a.tobytes()
bb = blosc.compress(h, typesize=8)

f = urllib.request.urlopen(request, bb)
print(f.read().decode('utf-8'))