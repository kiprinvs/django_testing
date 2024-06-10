from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    """Тесты доступности страниц."""

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Вася Пупкин')
        cls.reader = User.objects.create(username='Петя Лупкин')
        cls.auth_client_author = Client()
        cls.auth_client_author.force_login(cls.author)
        cls.auth_client_reader = Client()
        cls.auth_client_reader.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='текст',
            author=cls.author
        )
        cls.note_id = (cls.note.id,)

    def test_pages_availability_for_anonymous_user(self):
        """
        Тест доступности страниц для анонимного пользователя.

        Главная страница доступна анонимному пользователю.
        Страницы регистрации пользователей,
        входа в учётную запись и выхода из неё доступны всем пользователям.
        """
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        )
        for name in urls:
            with self.subTest(name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """
        Тест доступности страниц для аутентифицированного пользователя.

        Аутентифицированному пользователю доступна
        страница со списком заметок notes/,
        страница успешного добавления заметки done/,
        страница добавления новой заметки add/.
        """
        urls = (
            ('notes:list'),
            ('notes:add'),
            ('notes:success'),
        )
        for name in urls:
            with self.subTest(name):
                url = reverse(name)
                response = self.auth_client_reader.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Тест доступности страниц заметки, удаления и редактирования.

        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки. Если на эти страницы
        попытается зайти другой пользователь — вернётся ошибка 404.
        """
        users_statuses = (
            (self.auth_client_author, HTTPStatus.OK),
            (self.auth_client_reader, HTTPStatus.NOT_FOUND)
        )
        for user, status in users_statuses:
            for name in ('notes:edit', 'notes:delete', 'notes:detail'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        Тест перенаправления анонимного пользователя.

        При попытке перейти на страницу списка заметок,
        страницу успешного добавления записи, страницу добавления заметки,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        urls = (
            ('notes:detail', self.note_id),
            ('notes:edit', self.note_id),
            ('notes:delete', self.note_id),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
