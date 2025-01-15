# Data types of the app

from logger import logger
logger.debug('Loading <app_types> module')

from datetime import datetime
from pyrogram.enums import MessageMediaType


from pgdb import Row, Rows


media_types_encoder = {
    MessageMediaType.ANIMATION:'ANIMATION',
    MessageMediaType.AUDIO:'AUDIO',
    MessageMediaType.CONTACT:'CONTACT',
    MessageMediaType.DICE:'DICE',
    MessageMediaType.DOCUMENT:'DOCUMENT',
    MessageMediaType.GAME:'GAME',
    MessageMediaType.GIVEAWAY:'GIVEAWAY',
    MessageMediaType.GIVEAWAY_WINNERS:'GIVEAWAY_WINNERS',
    MessageMediaType.INVOICE:'INVOICE',
    MessageMediaType.LOCATION:'LOCATION',
    MessageMediaType.PAID_MEDIA:'PAID_MEDIA',
    MessageMediaType.PHOTO:'PHOTO',
    MessageMediaType.POLL:'POLL',
    MessageMediaType.STICKER:'STICKER',
    MessageMediaType.STORY:'STORY',
    MessageMediaType.VENUE:'VENUE',
    MessageMediaType.VIDEO:'VIDEO',
    MessageMediaType.VIDEO_NOTE:'VIDEO_NOTE',
    MessageMediaType.VOICE:'VOICE',
    MessageMediaType.WEB_PAGE:'WEB_PAGE'
}


# The data structures for save in database
class DBChannel(Row) :       # record in <channel> table
    id: int     # channel id    - primary key

    username: str   # name for telegram channel login
    title: str  # title of the channel
    category: str   # 'Аналитика' - channel category
    creation_time: datetime     # channel creation time
    turn_on_time: datetime     # channel time of start analysis
    turn_off_time: datetime | None    # channel time of ending analysis


class DBChannelHist(Row) :       # record in <channel_hist> table
    channel_id: int     # channel id    - foreign key

    update_time: datetime   # update time
    subscribers: int    # number of subscribers of the channel
    msgs_count: int     # number of messages of the channel


class DBPost(Row) :       # record in <post> table
    channel_id: int     # channel id  - part of the group primary key
    post_id: int     # post id      - part of the group primary key

    forward_from_chat : int | None    # channel id from where the post was forwarded (if any)
    creation_time: datetime     # post creation time
    drop_time: datetime | None    # time to delete a post
    is_advertising: bool    # the sign of an advertising post
    media_group_id: int      # media group id if the post is a group post
    media_type : str   # type of content
    post_text: str | None     # content of a text or a caption field if any
    text_len: int | None    # the length of the text content string
    text_entities_count: int | None     # the number of formatting entities in the text or caption field
    post_url: str |None     # the url-link to the post (for example, https://t.me/simulative_official/2109)
    is_planned: bool    # a sign that planning has been completed


class DBPostHist(Row) :       # record in <post_hist> table
    channel_id: int     # channel id  - part of the group foreign key
    post_id: int     # post id      - part of the group foreign key

    update_time: datetime   # update time
    observation_day: int    # serial number of the observation day
    post_comments: int     # number of comments
    post_views: int     # number of views
    stars: int     # number of <stars> reactions
    positives: int  # number of positive emoji
    negatives: int  # number of negative emoji
    neutrals: int   # number of neutrals emoji
    customs: int  # number of custom emoji
    reposts: int  # the number of reposts of this post


class DBMediaGroup(Row) :       # record in <post_hist> table
    media_group_id: int      # media group id if the post is a group post  - primary key

    update_time: datetime   # update time
    post_id: int     # post id
    observation_day: int    # serial number of the observation day
    post_order: int     # serial number of the post in the media group
    post_views: int     # number of views
    reposts: int    # the number of reposts of this post

class DBTaskPlan(Row) :       # record in <task_plan> table
    channel_id: int     # channel id  - part of the group foreign key
    post_id: int     # post id      - part of the group foreign key

    observation_day: int    # the ordinal number of the day on which the observation will be performed
    planned_at: datetime   # scheduled task start time
    # started_at: datetime | None  # the time when the task was actually started
    completed_at: datetime | None  # the time of the actual completion of the task