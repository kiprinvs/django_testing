from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Вася Пупкин')
        cls.reader = User.objects.create(username='Петя Лупкин')
        cls.auth_client_reader = Client()
        cls.auth_client_reader.force_login(cls.reader)
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', author=cls.author
        )

    def test_notes_list_for_author(self):
        url = reverse('notes:list')
        response = self.auth_client_author.get(url)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)

    def test_notes_list_for_reader(self):
        url = reverse('notes:list')
        response = self.auth_client_reader.get(url)
        object_list = response.context['object_list']
        self.assertNotIn(self.note, object_list)

    def test_create_and_edit_note_contains_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.auth_client_author.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
