from http import HTTPStatus

import pytest
from django.urls import reverse
from pytest_django.asserts import assertFormError, assertRedirects

from news.models import Comment
from news.forms import BAD_WORDS, WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, news_id_for_args, form_data
):
    """Анонимный пользователь не может отправить комментарий."""
    url = reverse('news:detail', args=news_id_for_args)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    response = client.post(url, data=form_data)
    assertRedirects(response, expected_url)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_user_can_create_comment(
    author_client, news_id_for_args, form_data, author, news
):
    """Авторизованный пользователь может отправить комментарий."""
    url = reverse('news:detail', args=news_id_for_args)
    response = author_client.post(url, data=form_data)
    comments_count = Comment.objects.count()
    comment = Comment.objects.get()
    assertRedirects(response, f'{url}#comments')
    assert comments_count == 1
    assert comment.text == form_data['text']
    assert comment.author == author
    assert comment.news == news


@pytest.mark.parametrize(
    'bad_word',
    BAD_WORDS,
)
def test_user_cant_use_bad_words(
    not_author_client, news_id_for_args, bad_word
):
    """
    Тест отправки запрещенных слов в комментарий.

    Если комментарий содержит запрещённые слова, он не будет опубликован,
    а форма вернёт ошибку.
    """
    url = reverse('news:detail', args=news_id_for_args)
    bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}
    response = not_author_client.post(url, data=bad_words_data)
    assertFormError(response, form='form', field='text', errors=WARNING)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_delete_comment(
    author_client, comment_id_for_args, news_id_for_args
):
    """Авторизованный пользователь может удалять свои комментарии."""
    url = reverse('news:detail', args=news_id_for_args)
    url_to_comments = f'{url}#comments'
    delete_url = reverse('news:delete', args=comment_id_for_args)
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    comments_count = Comment.objects.count()
    assert comments_count == 0


def test_author_can_edit_comment(
    author,
    author_client,
    comment,
    comment_id_for_args,
    form_data,
    news,
    news_id_for_args,
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    url = reverse('news:detail', args=news_id_for_args)
    url_to_comments = f'{url}#comments'
    edit_url = reverse('news:edit', args=comment_id_for_args)
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.author == author
    assert comment.news == news


def test_user_cant_delete_comment_of_another_user(
    not_author_client, comment_id_for_args
):
    """Авторизованный пользователь не может удалять чужие комментарии."""
    delete_url = reverse('news:delete', args=comment_id_for_args)
    response = not_author_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comments_count = Comment.objects.count()
    assert comments_count == 1


def test_user_cant_edit_comment_of_another_user(
    not_author_client, comment_id_for_args, form_data, comment, author, news
):
    """Авторизованный пользователь не может редактировать чужие комментарии."""
    edit_url = reverse('news:edit', args=comment_id_for_args)
    comment_text = comment.text
    response = not_author_client.post(edit_url, form=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == comment_text
    assert comment.author == author
    assert comment.news == news
