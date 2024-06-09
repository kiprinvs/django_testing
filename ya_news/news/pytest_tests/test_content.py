from pytest_lazyfixture import lazy_fixture
import pytest

from django.urls import reverse

from yanews.settings import NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_count(client, news_list):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    news_count = object_list.count()
    assert news_count == NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client):
    url = reverse('news:home')
    response = client.get(url)
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, news, comments_list):
    url = reverse('news:detail', args=(news.id,))
    response = client.get(url)
    news = response.context['news']
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
    url = reverse('news:detail', args=news_id_for_args)
    response = parametrized_client.get(url)
    assert ('form' in response.context) is availability_form
