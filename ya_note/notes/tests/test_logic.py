from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreate(TestCase):
    """Тесты создания заметок."""

    CREATE_URL = reverse('notes:add')
    DONE_URL = reverse('notes:success')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Вася Пупкин')
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый Текст',
            'slug': 'new_slug'
        }

    def test_user_can_create_note(self):
        """Залогиненный пользователь может создать заметку."""
        Note.objects.all().delete()
        response = self.auth_client_author.post(
            self.CREATE_URL, data=self.form_data
        )
        self.assertRedirects(response, self.DONE_URL)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Не залогиненный пользователь не может создать заметку."""
        notes_count = Note.objects.count()
        response = self.client.post(self.CREATE_URL, data=self.form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.CREATE_URL}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), notes_count)

    def test_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        notes_count = Note.objects.count()
        new_note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='new_slug',
            author=self.author
        )
        self.assertEqual(Note.objects.count(), notes_count + 1)
        response = self.auth_client_author.post(
            self.CREATE_URL, data=self.form_data
        )
        self.assertFormError(response, 'form', 'slug',
                             errors=(new_note.slug + WARNING))
        self.assertEqual(Note.objects.count(), notes_count + 1)

    def test_empty_slug(self):
        """Не заполненный slug формируется автоматически."""
        Note.objects.all().delete()
        self.form_data.pop('slug')
        response = self.auth_client_author.post(
            self.CREATE_URL, data=self.form_data
        )
        self.assertRedirects(response, self.DONE_URL)
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestEditDelete(TestCase):
    """Тесты редактирования и удаления заметок."""

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Вася Пупкин')
        cls.reader = User.objects.create(username='Петя Лупкин')
        cls.auth_client_reader = Client()
        cls.auth_client_reader.force_login(cls.reader)
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок', text='Текст', slug='slug', author=cls.author
        )
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.form_data = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
            'slug': 'new_slug'
        }

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        response = self.auth_client_author.post(
            self.edit_url, data=self.form_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Пользователь не может редактировать чужие заметки."""
        response = self.auth_client_reader.post(
            self.edit_url, data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        notes_count = Note.objects.count()
        url = reverse('notes:delete', args=(self.note.slug,))
        response = self.auth_client_author.post(url)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), notes_count - 1)

    def test_other_user_cant_delete_note(self):
        """Пользователь не может удалять чужие заметки."""
        notes_count = Note.objects.count()
        response = self.auth_client_reader.post(
            self.edit_url, data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), notes_count)
