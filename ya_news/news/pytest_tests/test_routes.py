from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertRedirects
from pytest_lazyfixture import lazy_fixture


@pytest.mark.django_db
@pytest.mark.parametrize(
    'name, args',
    (
        ('news:home', None),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
        ('news:detail', lazy_fixture('news_id_for_args')),
    )
)
def test_pages_availability_for_anonymous_user(args, client, name):
    """
    Тест доступности страниц для анонимного пользователя.

    Главная страница доступна анонимному пользователю.
    Страницы отдельной новости, регистрации пользователей,
    входа в учётную запись и выхода из неё доступны всем пользователям.
    """
    url = reverse(name, args=args)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    (
        (lazy_fixture('author_client'), HTTPStatus.OK),
        (lazy_fixture('not_author_client'), HTTPStatus.NOT_FOUND),
    )
)
@pytest.mark.parametrize(
    'name',
    ('news:delete', 'news:edit'),
)
def test_comment_availability_for_different_users(
    parametrized_client, expected_status, name, comment_id_for_args
):
    """
    Тест страниц редактирования и удаления.

    Страницы удаления и редактирования комментария доступны автору комментария.
    Авторизованный пользователь не может зайти на страницы редактирования
    или удаления чужих комментариев (возвращается ошибка 404).
    """
    url = reverse(name, args=comment_id_for_args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    'name, args',
    (
        ('news:delete', lazy_fixture('comment_id_for_args')),
        ('news:edit', lazy_fixture('comment_id_for_args')),
    )
)
def test_redirects(client, name, args):
    """
    Тест перенаправления анонимного пользователя.

    При попытке перейти на страницу редактирования или удаления комментария
    анонимный пользователь перенаправляется на страницу авторизации.
    """
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
