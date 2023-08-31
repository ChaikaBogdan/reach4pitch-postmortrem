from django.test import TestCase
from django.urls import reverse
from django_rq import get_worker

from backend.models import Pitch, Publisher, User


class PitchModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        not_publisher_user = User.objects.create(
            username="pitcher",
            publisher=None,
        )
        cls.pitch = Pitch.objects.create(
            name="Everglow The Lost Days",
            created_by=not_publisher_user,
        )

    def test_str(self):
        self.assertEqual(str(self.pitch), "Everglow The Lost Days")


class PublisherViewsTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        publisher = Publisher.objects.create(name="7CoreLoops")
        not_publisher_user = User.objects.create(
            username="pitcher",
            email="pitcher@reach4pitch.com",
            publisher=None,
        )
        for pitch_name in "Everglow The Lost Days", "Glow":
            pitch = Pitch.objects.create(
                name=pitch_name,
                created_by=not_publisher_user,
                is_published=True,
            )
            publisher.pitches.add(pitch)
        cls.details_url = reverse("backend:publisher_details", args=[publisher.slug])
        cls.pitches_url = reverse("backend:pitches_list")
        cls.publisher = publisher
        cls.not_publisher_user = not_publisher_user

    def test_details_page_context(self):
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, 200)
        publisher = response.context["publisher"]
        self.assertEqual(publisher.id, self.publisher.id)

    def test_pitches_page_context(self):
        publisher_user = User.objects.create(
            username=self.publisher.name,
            publisher=self.publisher,
        )
        self.client.force_login(publisher_user)
        response = self.client.get(self.pitches_url)
        self.assertEqual(response.status_code, 200)
        pitches = response.context["page_obj"].object_list
        self.assertEqual(len(pitches), 2)
        self.client.logout()

    def test_pitches_page_not_logged(self):
        self.client.logout()
        response = self.client.get(self.pitches_url)
        self.assertEqual(response.status_code, 302)

    def test_pitches_page_not_publisher(self):
        self.client.force_login(self.not_publisher_user)
        response = self.client.get(self.pitches_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()


class EmailCollectViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.email_collect_url = reverse("collect_email")

    def test_collect_email_ok(self):
        expected_email = "sample@mail.com"
        response = self.client.post(
            self.email_collect_url,
            {"email": expected_email},
        )
        get_worker().work(burst=True)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email=expected_email).exists())
