# Work with message(post) reactions

from logger import logger
logger.debug('Loading <reaction> module')

from pyrogram.types import Message, MessageReactions, Reaction
# from pyrogram.types.messages_and_media import MessageReactions
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TGReactions:
    stars: int
    positives: int
    negatives: int
    neutrals: int
    customs: int


positive_emojis = (
    "👍", "❤️", "🔥", "😍", "🥰", "👏", "😁", "🎉", "🤩", "🙏", "👌", "🕊", "🤣", "😅",
    "😆", "😜", "😘", "💯", "🏆", "💋", "🥂", "🤝", "😄", "😺", "☺️", "😸", "😻",
    "😽", "😚", "😙", "😗", "😝", "😛", "🥳", "😎", "🤗","❤","🐳", "💖"
)

neutral_emojis = (
    "🤔", "🤯", "🤡", "⚡️", "🍌", "🍓", "✍️", "🤷", "🧐", "😶", "🤫", "🤭", "😯", "😮",
    "😬", "😕", "🙄", "😏"
)

negative_emojis = (
    "👎", "😱", "🤬", "😢", "🤮", "💩", "😭", "💔", "🤦", "😑", "😦", "😧", "😨", "😰",
    "😥", "😓", "😔", "😖", "😣", "😩", "😫", "😤", "😡", "😠", "😿", "😾", "😒"
)


async def get_post_reactions(msg: Message) -> TGReactions :
    stars = positives = negatives = neutrals = customs = 0
    post_reactions: MessageReactions | None = msg.reactions

    if post_reactions :
        for reaction in post_reactions.reactions :
            if reaction.is_paid is not None and reaction.is_paid:
                stars += reaction.count
            elif reaction.emoji and reaction.emoji in positive_emojis:
                positives += reaction.count
            elif reaction.custom_emoji_id:
                customs += reaction.count
            elif reaction.emoji and reaction.emoji in negative_emojis :
                negatives += reaction.count
            elif reaction.emoji :
                neutrals += reaction.count
    return TGReactions(
        stars=stars,
        positives=positives,
        negatives=negatives,
        neutrals=neutrals,
        customs=customs
    )
