from __future__ import annotations

from datetime import UTC, datetime
from typing import cast

from klei.forum import (
    KleiForumClient,
    find_comment_url,
    parse_forum_page,
    parse_search_page,
    parse_topic_page,
    topic_page_url,
)
from klei.forum.url import join_url, parse_query, with_query
from klei_support import FakeRoutePool
from urllib3_future import AsyncPoolManager

TOPIC_URL = "https://forums.kleientertainment.com/forums/topic/145450-test-topic/"
TOPIC_PAGE_2_URL = f"{TOPIC_URL}page/2/"
FORUM_URL = "https://forums.kleientertainment.com/forums/forum/208-beta/"


def _json_ld(page: int = 1) -> str:
    comments = """
        "comment": [
            {
                "@type": "Comment",
                "@id": "https://forums.kleientertainment.com/forums/topic/145450-test-topic/#comment-2",
                "upvoteCount": 4
            }
        ],
    """
    if page == 2:
        comments = """
        "comment": [
            {
                "@type": "Comment",
                "@id": "https://forums.kleientertainment.com/forums/topic/145450-test-topic/page/2/#comment-3",
                "upvoteCount": 0
            }
        ],
    """
    return f"""
    <script type="application/ld+json">
    {{
        "@context": "http://schema.org",
        "@type": "DiscussionForumPosting",
        "headline": "Test Topic",
        "author": {{"@type": "Person", "name": "PeterA"}},
        "interactionStatistic": [
            {{
                "interactionType": "http://schema.org/ViewAction",
                "userInteractionCount": 12
            }},
            {{
                "interactionType": "http://schema.org/CommentAction",
                "userInteractionCount": 2
            }},
            {{
                "interactionType": "http://schema.org/FollowAction",
                "userInteractionCount": 1
            }}
        ],
        {comments}
        "url": "{TOPIC_URL}"
    }}
    </script>
    <script type="application/ld+json">
    {{
        "@context": "http://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {{
                "@type": "ListItem",
                "position": 1,
                "item": {{
                    "name": "Forums",
                    "@id": "https://forums.kleientertainment.com/forums/"
                }}
            }},
            {{
                "@type": "ListItem",
                "position": 2,
                "item": {{
                    "name": "Don't Starve Together",
                    "@id": "https://forums.kleientertainment.com/forums/forum/73-dont-starve-together/"
                }}
            }}
        ]
    }}
    </script>
    """


def _post(comment_id: int, author: str, body: str, *, highlighted: bool = False) -> str:
    classes = (
        "cPost ipsComment ipsComment_highlighted" if highlighted else "cPost ipsComment"
    )
    return f"""
    <article id="elComment_{comment_id}" class="{classes}">
        <aside class="cAuthorPane">
            <h3 class="cAuthorName">
                <a href="https://forums.kleientertainment.com/profile/{comment_id}-{author.lower()}/">
                    <span>{author}</span>
                </a>
            </h3>
            <span class="ipsType_light">Developer</span>
            <span>1.4k</span>
            <a class="ipsUserPhoto" href="#">
                <img src="//cdn.forums.klei.com/avatar-{comment_id}.jpg" alt="{author}">
            </a>
        </aside>
        <div class="ipsComment_content"
             data-commentID="{comment_id}"
             data-controller="core.front.core.comment">
            <div class="ipsComment_meta">
                {"Author" if author == "PeterA" else ""}
                <a href="{TOPIC_URL}?do=findComment&amp;comment={comment_id}">
                    <time datetime="2023-01-04T21:31:26Z">January 5, 2023</time>
                </a>
            </div>
            <div data-role="commentContent" class="ipsType_richText">
                {body}
            </div>
        </div>
    </article>
    """


def _topic_html(page: int = 1) -> bytes:
    posts = [
        _post(
            1,
            "PeterA",
            """
            <p>Happy New Year!</p>
            <p>Read <a href="/forums/topic/106156-beta/">here</a>.</p>
            <img src="//cdn.forums.klei.com/smile.gif" alt=":)">
            """,
            highlighted=True,
        ),
        _post(
            2,
            "Capybara007",
            """
            <blockquote>
                <div class="ipsQuote_citation">
                    <a
                        href="/forums/topic/145450-test-topic/?do=findComment&amp;comment=1"
                    >
                        PeterA said:
                    </a>
                </div>
                <p>Improved synchronization.</p>
            </blockquote>
            <p>better lag prediction?</p>
            """,
        ),
    ]
    if page == 2:
        posts = [
            _post(3, "Hillside sheep", "<p>Page two body.</p>"),
        ]
    return f"""
    <html>
    <head>
        <title>Test Topic</title>
        <link rel="canonical" href="{TOPIC_URL}">
        <link rel="last" href="{TOPIC_PAGE_2_URL}">
        {_json_ld(page)}
    </head>
    <body data-pagecontroller="topic" data-pageid="145450">
        <h1>Test Topic</h1>
        <ul class="ipsPagination"><li>Page {page} of 2</li></ul>
        <div id="comments">
            {"".join(posts)}
        </div>
    </body>
    </html>
    """.encode()


def _forum_html() -> bytes:
    return f"""
    <html>
    <head><link rel="canonical" href="{FORUM_URL}"></head>
    <body data-pagecontroller="forums" data-pageid="208">
        <h1>[Don't Starve Together] Beta Branch</h1>
        <ul class="ipsPagination"><li>Page 1 of 1</li></ul>
        <ol>
            <li class="cForumRow ipsDataItem" data-forumid="256">
                <h4>
                    <a href="/forums/forum/256-beta-branch-bug-tracker/">
                        Beta Branch - Bug Tracker
                    </a>
                </h4>
                <div class="ipsDataItem_meta">Bug reports</div>
            </li>
            <li
                class="ipsDataItem"
                data-rowid="145450"
                data-controller="forums.front.forum.topicRow"
            >
                <h4 class="ipsDataItem_title"><a href="{TOPIC_URL}">Test Topic</a></h4>
                <p class="ipsDataItem_meta">
                    By <a href="/profile/475356-petera/">PeterA</a>, January 5, 2023
                </p>
                <dl class="ipsDataItem_stats">
                    <dt>2 replies</dt><dt>293.6k views</dt>
                </dl>
                <ul class="ipsDataItem_lastPoster">
                    <li><a href="/profile/1394590-capybara007/">Capybara007</a></li>
                    <li>
                        <a href="{TOPIC_URL}?do=findComment&amp;comment=2">
                            Last post
                        </a>
                    </li>
                    <li><time datetime="2023-01-05T00:00:00Z">January 5</time></li>
                </ul>
            </li>
        </ol>
    </body>
    </html>
    """.encode()


def test_parse_topic_page_extracts_typed_posts() -> None:
    page = parse_topic_page(_topic_html().decode(), TOPIC_URL)

    assert page.topic_id == 145450
    assert page.title == "Test Topic"
    assert page.page == 1
    assert page.page_count == 2
    assert page.stats.views == 12
    assert page.stats.comments == 2
    assert page.breadcrumbs[1].name == "Don't Starve Together"
    assert len(page.posts) == 2

    first = page.posts[0]
    assert first.comment_id == 1
    assert first.author.name == "PeterA"
    assert first.author.id == 1
    assert first.author.avatar_url == "https://cdn.forums.klei.com/avatar-1.jpg"
    assert first.author.post_count == 1400
    assert first.posted_at == datetime(2023, 1, 4, 21, 31, 26, tzinfo=UTC)
    assert first.is_topic_author is True
    assert first.is_highlighted is True
    assert first.links[0].url == (
        "https://forums.kleientertainment.com/forums/topic/106156-beta/"
    )
    assert first.images[0].url == "https://cdn.forums.klei.com/smile.gif"

    second = page.posts[1]
    assert second.upvote_count == 4
    assert second.quotes[0].citation == "PeterA said:"
    assert second.quotes[0].source_url == (f"{TOPIC_URL}?do=findComment&comment=1")
    assert second.content_text.endswith("better lag prediction?")


def test_parse_forum_page_extracts_subforums_and_topics() -> None:
    page = parse_forum_page(_forum_html().decode(), FORUM_URL)

    assert page.forum_id == 208
    assert page.title == "[Don't Starve Together] Beta Branch"
    assert page.forums[0].forum_id == 256
    assert page.forums[0].title == "Beta Branch - Bug Tracker"
    assert page.forums[0].description == "Bug reports"
    assert page.topics[0].topic_id == 145450
    assert page.topics[0].author is not None
    assert page.topics[0].author.name == "PeterA"
    assert page.topics[0].replies == 2
    assert page.topics[0].views == 293600
    assert page.topics[0].last_post is not None
    assert page.topics[0].last_post.author is not None
    assert page.topics[0].last_post.author.name == "Capybara007"


async def test_forum_client_fetches_and_merges_topic_pages() -> None:
    pool = FakeRoutePool({
        TOPIC_URL: _topic_html(),
        TOPIC_PAGE_2_URL: _topic_html(2),
    })
    client = KleiForumClient(http_pool=cast(AsyncPoolManager, pool))

    try:
        topic = await client.get_topic(TOPIC_URL)
    finally:
        await client.close()

    assert topic.topic_id == 145450
    assert topic.page_count == 2
    assert [post.comment_id for post in topic.posts] == [1, 2, 3]
    assert [page.page for page in topic.pages] == [1, 2]
    assert pool.cleared is True
    assert [call["url"] for call in pool.calls] == [TOPIC_URL, TOPIC_PAGE_2_URL]


async def test_forum_client_search_builds_public_html_query() -> None:
    search_url = (
        "https://forums.kleientertainment.com/search/?"
        "q=536845&type=forums_topic&nodes=208"
    )
    html = f"""
    <html>
    <title>Search results</title>
    <li class="ipsStreamItem" data-role="activityItem" data-timestamp="1672867886">
        <h2><a href="{TOPIC_URL}?do=findComment&amp;comment=1">Test Topic</a></h2>
        <a href="/profile/475356-petera/">PeterA</a>
        <div class="ipsType_richText">Happy New Year!</div>
    </li>
    </html>
    """.encode()
    pool = FakeRoutePool({search_url: html})
    client = KleiForumClient(http_pool=cast(AsyncPoolManager, pool))

    try:
        page = await client.search("536845", nodes=[208])
    finally:
        await client.close()

    assert page.results[0].title == "Test Topic"
    assert page.results[0].author is not None
    assert page.results[0].author.name == "PeterA"
    assert page.results[0].posted_at == datetime(2023, 1, 4, 21, 31, 26, tzinfo=UTC)
    assert pool.calls[0]["url"] == search_url


def test_forum_url_helpers() -> None:
    assert topic_page_url(TOPIC_URL, 2) == TOPIC_PAGE_2_URL
    assert find_comment_url(TOPIC_URL, 3) == f"{TOPIC_URL}?do=findComment&comment=3"
    assert join_url(TOPIC_URL, "/forums/") == (
        "https://forums.kleientertainment.com/forums/"
    )
    assert join_url(TOPIC_URL, "mailto:peter@example.com") == "mailto:peter@example.com"
    assert with_query(TOPIC_URL, (("q", "a b&c"), ("empty", ""))) == (
        f"{TOPIC_URL}?q=a+b%26c&empty="
    )
    assert parse_query("q=a+b%26c&empty=") == [("q", "a b&c"), ("empty", "")]
    assert parse_search_page("<html><title>Empty</title></html>", TOPIC_URL).title == (
        "Empty"
    )
