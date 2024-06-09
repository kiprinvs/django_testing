from datetime import timedelta
import pytest

from django.test.client import Client
from django.utils import timezone

from news.models import News, Comment
from yanews.settings import NEWS_COUNT_ON_HOME_PAGE


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def not_author(django_user_model):
    return django_user_model.objects.create(username='Не автор')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(not_author):
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def news():
    news = News.objects.create(
        title='Заголовок',
        text='Текст заметки',
    )
    return news


@pytest.fixture
def news_id_for_args(news):
    return (news.id,)


@pytest.fixture
def comment(author, news):
    comment = Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария',
    )
    return comment


@pytest.fixture
def comment_id_for_args(comment):
    return (comment.id,)


@pytest.fixture
def form_data():
    return {
        'text': 'Новый текст'
    }


@pytest.fixture
def news_list():
    today = timezone.now()
    all_news = [
        News(
            title=f'Новость {index}.',
            text='Текст новости.',
            date=today - timedelta(days=index)
        )
        for index in range(NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def comments_list(news, author):
    now = timezone.now()
    comments = []
    for index in range(5):
        comment = Comment.objects.create(
            news=news,
            author=author,
            text=f'Teкст комментария {index}.',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
        comments.append(comment)
    return comments
