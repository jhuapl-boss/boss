from django.core.urlresolvers import resolve
from ..views import CutoutView, Cutout

from rest_framework.test import APITestCase

from django.conf import settings

version = settings.BOSS_VERSION


class CutoutInterfaceRoutingTests(APITestCase):
    """Test that Cutout interface endpoints route properly"""

    def setUp(self):
        """
        Initialize the database
        :return:
        """

    def test_full_token_cutout_resolves_to_cutout(self):
        """
        Test to make sure the cutout URL with all datamodel params resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/col1/exp1/ds1/2/0:5/0:6/0:2')
        self.assertEqual(view_based_cutout.func.__name__, Cutout.as_view().__name__)

    def test_view_token_cutout_resolves_to_cutoutview(self):
        """
        Test to make sure the cutout URL with just a view token resolves
        :return:
        """
        view_based_cutout = resolve('/' + version + '/cutout/2/0:5/0:6/0:2?view=token1')
        self.assertEqual(view_based_cutout.func.__name__, CutoutView.as_view().__name__)
