from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
import pytest

from news.forms import CommentForm
from yanews.settings import NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_count(client, news_list):
    """Количество новостей на главной странице — не более 10."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context.get('object_list')
    news_count = object_list.count()
    assert news_count == NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client):
    """Новости отсортированы от самой свежей к самой старой."""
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context.get('object_list')
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, news, comments_list):
    """Комментарии отсортированы в хронологическом порядке"""
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    news = response.context.get('news')
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
@pytest.mark.parametrize(
    'parametrized_client, availability_form',
    (
        (lazy_fixture('not_author_client'), True),
        (lazy_fixture('client'), False),
    )
)
def test_form_availability_for_different_users(
    parametrized_client, availability_form, news_id_for_args
):
    """
    Тест доступности формы отправки комментария.

    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости, а авторизованному доступна.
    """
    url = reverse('news:detail', args=news_id_for_args)
    response = parametrized_client.get(url)
    assert ('form' in response.context) is availability_form
    if 'form' in response.context:
        assert isinstance(response.context['form'], CommentForm)
