from rest_framework.test import APITestCase
from django.core.urlresolvers import resolve
from ..views import BossMeta

from django.conf import settings
version  = settings.BOSS_VERSION

class BossCoreMetaServiceRoutingTests(APITestCase):

    def test_meta_urls_resolves_to_BossMeta_views(self):
        """
        Test to make sure the meta URL for get, post, delete and update with all datamodel\
 params resolves to the meta view
        :return:
        """
        match = resolve('/' + version + '/meta/col1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)

        match = resolve('/' + version + '/meta/col1/exp1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)

        match = resolve('/' + version + '/meta/col1/exp1/ch1/')
        self.assertEqual(match.func.__name__, BossMeta.as_view().__name__)
