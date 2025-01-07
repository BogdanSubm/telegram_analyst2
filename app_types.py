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