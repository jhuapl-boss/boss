from django.test import TestCase
from django.core.urlresolvers import resolve
from .views import CutoutView, Cutout


class CutoutInterfaceRoutingTests(TestCase):

    def test_full_token_cutout_resolves_to_cutout(self):
        """
        Test to make sure the cutout URL with all datamodel params resolves
        :return:
        """
        view_based_cutout = resolve('/v0.1/cutout/col1/exp1/data1/2/0:5/0:6/0:2')
        self.assertEqual(view_based_cutout.func, Cutout.as_view())
