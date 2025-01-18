"""
main database module
"""

from logger import logger
logger.debug('Loading <database> module')

from pyrogram import Client

from pgdb import Database, Row, Rows
from config_py import settings
from scheduler import main_schedule


async def recreate_tables() -> bool:
    db: Database = Database(settings.database_connection)
    if not db.is_connected :
        return False

    if not db.create_table(table_name='channel',
                           columns_statement='''
                                id int8 NOT NULL,
                                username varchar NOT NULL,
                                title varchar NOT NULL,
                                category varchar NULL,
                                creation_time timestamp NULL,
                                turn_on_time timestamp NULL,
                                turn_off_time timestamp NULL,
                                CONSTRAINT channel_pk PRIMARY KEY (id)
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='channel_hist',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                subscribers int4 NULL,
                                msgs_count int4 NULL,
                                CONSTRAINT channel_hist_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='channel_plan',
                           columns_statement='''
                                planned_at timestamp NOT NULL,
                                completed_at timestamp NULL
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                post_id int4 NOT NULL,
                                forward_from_chat int8 NULL,
                                creation_time timestamp NOT NULL,
                                drop_time timestamp NULL,
                                is_advertising bool DEFAULT false NOT NULL,
                                media_group_id int8 NULL,
                                media_type varchar NULL,
                                post_text varchar NULL,
                                text_len int4 NULL,
                                text_entities_count int4 NULL,
                                post_url varchar NULL,
                                is_planned bool DEFAULT false NOT NULL,
                                CONSTRAINT post_pk PRIMARY KEY (channel_id, post_id),
                                CONSTRAINT post_unique UNIQUE (media_group_id),
                                CONSTRAINT post_channel_fk FOREIGN KEY (channel_id) 
                                    REFERENCES public.channel(id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='post_hist',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                post_id int4 NOT NULL,
                                update_time timestamp NOT NULL,
                                observation_day int4 NOT NULL, 
                                post_comments int4 DEFAULT 0 NOT NULL,
                                post_views int4 DEFAULT 0 NOT NULL,
                                stars int4 DEFAULT 0 NOT NULL,
                                positives int4 DEFAULT 0 NOT NULL,
                                negatives int4 DEFAULT 0 NOT NULL,
                                neutrals int4 DEFAULT 0 NOT NULL,
                                customs int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT post_hist_post_fk FOREIGN KEY (channel_id, post_id)
                                    REFERENCES public.post(channel_id, post_id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='media_group',
                           columns_statement='''                            
                                media_group_id int8 NOT NULL,
                                update_time timestamp NOT NULL,
                                post_id int4 NOT NULL,
                                observation_day int4 NOT NULL,
                                post_order int2 NOT NULL,
                                post_views int4 DEFAULT 0 NOT NULL,
                                reposts int4 DEFAULT 0 NOT NULL,
                                CONSTRAINT media_group_post_fk FOREIGN KEY (media_group_id) 
                                    REFERENCES public.post(media_group_id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    if not db.create_table(table_name='task_plan',
                           columns_statement='''
                                channel_id int8 NOT NULL,
                                post_id int4 NOT NULL,
                                observation_day int4 NOT NULL,
                                planned_at timestamp NOT NULL,
                                completed_at timestamp NULL,
                                CONSTRAINT task_fk FOREIGN KEY (channel_id, post_id)
                                    REFERENCES public.post(channel_id, post_id) ON UPDATE CASCADE
                                ''',
                           overwrite=True) : return False

    return True




# from asyncio import TaskGroup
# from channel import channels_update
# from task import get_tasks_to_launch
# from normalizer import normalizer
# from app_status import app_status, AppStatusType
# from app_types import media_types_encoder
# from chunk import Chunk, chunks

# from post import get_tg_channel_posts_dict, posts_update, get_db_channel_posts_list
# import gc
#
# async def memory_info() :
#     main_schedule.print_memory()
#     logger.info(f'Count of objets in generations before collecting: {gc.get_count()}')
#     logger.info(f'Collected objects by gc: {gc.collect()}')
#     logger.info(f'Count of objets in generations after collecting: {gc.get_count()}')
#     main_schedule.print_memory()


    # for i in range(3):
    #     all_objs = gc.get_objects(generation=i)
    #     logger.info(f'Total objects of the {i} generation: {len(all_objs)}, including :')
    #     logger.info(all_objs[:10])



async def run_debug(client: Client) :

    main_schedule.print_tasks()
    await client.send_message('me', main_schedule.print_memory())


    # await memory_info()


    # await print_used_memory(client=client)

    # logger.info(await client.get_messages(chat_id=-1001720833502, message_ids=50555555))

    # await channels_update(client, is_first=False)
    # await get_tg_channel_posts_dict(client=client, chat_id=-1001720833502)
    # db: Database = Database(settings.database_connection)
    # if not db.is_connected :
    #     return False
    #
    # logger.debug(await get_tasks_to_launch(db=db))

    # # logger.debug(await get_db_channel_posts_list(db=db, chat_id= -1001720833502))
    #
    # res = db.read_rows(
    #     table_name='post',
    #     columns_statement='creation_time',
    #     condition_statement=f'channel_id = -1001720833502 '
    #                         f'and post_id = 5 '
    #                         f'and drop_time notnull')
    # logger.debug(f'res:{res}')
    # logger.debug(f'res.value:{res.value}')
    # logger.debug(f'len(res.value):{len(res.value)==1}')



    # await posts_update(client)

    # chat_id = -1001720833502
    # msg_id = [4412, 4413, 4414, 4415, 4416, 4417, 4418, 4419, 4420]
    # msg = await client.get_messages(chat_id, msg_id)

    # msg_id = 4418
    # msg_id = 5846

    # chat_id = -1002092560383
    # logger.debug(await client.get_chat(chat_id))
    # async for ms in client.get_chat_history(chat_id, limit=1) :
    #     logger.debug(ms)


    # chat_id = -1002330451219
    # msg_id = 67
    #
    # logger.debug(await client.get_media_group(chat_id=chat_id, message_id=msg_id))

    # chat_id = -1001694201893
    # msg_id_comm = 32515

    # logger.debug(await client.get_chat_history_count(chat_id))
    # # Get message with all chained replied-to messages
    #
    # # logger.debug(f'{await client.get_discussion_message(chat_id, msg_id)}')
    #
    # msg = await client.get_messages(chat_id=chat_id, message_ids=msg_id)
    # logger.debug(f'Debug: {msg}')



    # chunk = Chunk(normalizer)
    # i = 1
    # start = datetime.now()
    # while (datetime.now() - start).total_seconds() < 0.5 :
    #     try:
            # res = await client.get_discussion_replies_count(chat_id, msg_id)

            # res = await normalizer.run(client.get_discussion_replies_count, chat_id, msg_id)
            # logger.debug(f'{i} - {res}')

            # res = 0
            # async for msg in client.get_discussion_replies(chat_id, msg_id) :
            #     logger.debug(msg)
            #     res += 1
            # logger.debug(f'{i} - {res}')

            # for j in range(60) :
            #     await chunk.one_reading()  # anti flood reading pause

        # except FloodWait as e:
        #     logger.error(f'Telegram error: {e}')
        #     logger.debug(f'Waiting {e.value} sec.')
        #     await asyncio.sleep(e.value)
        #     i = 0
        # i += 1




    # messages: list[Message] = []
    # media_groups_messages: list[Message] = []
    # upload_time = datetime.now()
    #
    # chunk_reading = Chunk(normalizer)

    # res1 = await get_chat_history_chunk(client, chat_id=chat_id, chunk_size=500, offset_id=5500)
    # logger.debug(f'{len(res1)}, {res1}')
    # res2 = await get_chat_history_chunk(client, chat_id=chat_id, chunk_size=1000, offset_id=4500)
    # logger.debug(f'{len(res2)}, {res2}')
    # res3 = await get_chat_history_chunk(client, chat_id=chat_id, chunk_size=1000, offset_id=3500)
    # logger.debug(f'{len(res3)}, {res3}')
    # res4 = await get_chat_history_chunk(client, chat_id=chat_id, chunk_size=1000, offset_id=2500)
    # logger.debug(f'{len(res4)}, {res4}')
    # res5 = await get_chat_history_chunk(client, chat_id=chat_id, chunk_size=1000, offset_id=1500)
    # logger.debug(f'{len(res5)}, {res5}')

    # for _ in range(32) :
    # for _ in range(3) :
    #     async with asyncio.TaskGroup() as tg :
    #         task1 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=200, offset_id=5500))
    #         # task2 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=4500))
    #         # task3 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=4000))
    #         # task4 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=3500))
    #         # task5 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=3000))
    #         # task6 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=2500))
    #         # task7 = tg.create_task(get_chat_history_chunk(client, chat_id=chat_id, chunk_size=400, offset_id=2000))
    #
        # res1 = task1.result()
    #     # res2 = task2.result()
    #     # res3 = task3.result()
    #     # res4 = task4.result()
    #     # res5 = task5.result()
    #     # res6 = task6.result()
    #     # res7 = task7.result()
    #     # logger.debug(f'{len(res1)}, {res1}')
    #     # logger.debug(f'{len(res2)}, {res2}')
    #     # logger.debug(f'{len(res3)}, {res3}')
    #     # logger.debug(f'{len(res4)}, {res4}')
    #     # logger.debug(f'{len(res5)}, {res5}')
    #     # logger.debug(f'{len(res6)}, {res6}')
    #     # logger.debug(f'{len(res7)}, {res7}')
    #
        # await normalizer.run()
        # logger.debug('normalizer - run')
        # pause = 1
        # logger.debug(f'Pause - {pause} sec.')
        # await asyncio.sleep(pause)



    # try:
    # async with asyncio.TaskGroup() as tg :
    #     task1 = tg.create_task(
    #         put_to_base_posts(
    #             db=db,
    #             messages=messages
    #         )
    #     )
    #     task2 = tg.create_task(
    #         put_to_base_media(
    #             db=db,
    #             messages=media_groups_messages,
    #             upload_time=upload_time
    #         )
    #     )
    # if not (task1.result() and task2.result()) :

#
# async def get_comments(client, chat_id, msg_id) -> int:
#     try :
#         post_comments = await client.get_discussion_replies_count(chat_id=chat_id, message_id=msg_id)
#
#     except BadRequest as e :
#         logger.info(f'<No comments> status for the post # {msg_id}')
#         post_comments = 0
#     return post_comments
#
#
# async def get_chat_history_chunk(client, chat_id, chunk_size, offset_id) :
#     res = []
#     async for msg in client.get_chat_history(chat_id=chat_id, limit=chunk_size, offset_id=offset_id) :
#         res.append(msg.id)
#         # res.append(await get_comments(client, chat_id, msg.id))
#     return res

if __name__ == '__mail__' :
    pass