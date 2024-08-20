from aiogram.types import CallbackQuery

from core import bot
from database import *
from keyboards import AdminKeyboards as Admin_kb
from lexicon import *
import utils


async def send_information(target: str, target_id: int, chat_id: int, message_id: int):
    if target == 'user':
        user = get_user(target_id)

        if not user:
            await bot.edit_message_text(
                text='Пользователя с таким ID не существует',
                chat_id=chat_id, message_id=message_id,
                reply_markup=Admin_kb.back_to_information_kb()
            )
            return True

        bans_info = get_ban_info(target_id)
        ban_text = information['ban'].format(bans_info[2], bans_info[3]) if bans_info else ''
        user_activity = get_user_activity_summary(target_id)

        await bot.edit_message_text(
            text=information['user'].format(
                user[0], ban_text, user[1], f"@{user[2]}" if user[2] else '<code>Не указан</code>',
                user[3] if user[3] else 'Не указан', '{:,}'.format(round(user[4])).replace(',', ' '),
                user_activity['total_top_up'], 'dev', user[5], user_activity['total_orders'],
                user_activity['total_deals'], user_activity['confirmed_deals'], user_activity['complaints_against_user']
            ), chat_id=chat_id, message_id=message_id,
            reply_markup=Admin_kb.inspect_user_kb(target_id, not user_is_not_banned(target_id))
        )

    elif target == 'order':
        # order = get_order(target_id)
        pass

    elif target == 'deal':
        deal = get_deal(target_id)

        if not deal:
            await bot.edit_message_text(
                text='Пользователя с таким ID не существует',
                chat_id=chat_id, message_id=message_id,
                reply_markup=Admin_kb.back_to_information_kb()
            )
            return True

        deal_id, buyer_id, buyer_order_id, seller_id, seller_order_id, status, created_at = deal
        _, _, _, _, item, project, server, amount, description, price_sell, _, _ = get_order(seller_order_id)

        status_text = 'Отменена' if status == 'canceled' else 'В процессе' if status == 'open' else 'Завершена'
        item_info_text = f'Кол-во виртов: {"{:,}".format(amount)}' if item == 'virt' \
            else f'Название бизнеса: {description}' if item == 'business' else f'Описание аккаунта: {description}'
        price_buy = utils.get_price(seller_order_id, 'buy')
        price_buy, price_sell = '{:,}'.format(price_buy).replace(',', ' '), '{:,}'.format(price_sell).replace(',', ' ')

        await bot.edit_message_text(
            text=information['deal'].format(
                deal_id, status_text, seller_order_id, buyer_order_id, seller_id, buyer_id, created_at,
                utils.get_item_text(item), project, server, item_info_text, price_buy, price_sell
            ), chat_id=chat_id, message_id=message_id,
            reply_markup=Admin_kb.inspect_deal_kb(deal_id, buyer_id, seller_id, status == 'open')
        )

    elif target == 'report':
        complaint = get_open_complaints()

        if not complaint:
            await bot.edit_message_text(
                text='Нет жалобы с данным ID',
                chat_id=chat_id, message_id=message_id,
                reply_markup=Admin_kb.back_to_information_kb()
            )
            return True

        complaint_id, deal_id, complainer_id, offender_id, complaint_text, answer, created_at = complaint

        complainer = get_user(complainer_id)
        offender = get_user(offender_id)

        complainer_username = f'@{complainer[2]}' if complainer[2] else '<b>нет тега</b>'
        offender_username = f'@{offender[2]}' if offender[2] else '<b>нет тега</b>'

        await bot.edit_message_text(
            LEXICON['admin_report'].format(
                complaint_id, deal_id, created_at,
                get_bot_user_id(complainer_id), complainer_username, complainer_id,
                get_bot_user_id(offender_id), offender_username, offender_id, complaint_text),
            chat_id=chat_id, message_id=message_id,
            reply_markup=Admin_kb.answer_to_complaint_kb(complaint_id)
        )

    else:
        pass


async def send_chat_logs(callback: CallbackQuery, deal_id: int):
    messages = get_chat_messages(deal_id)

    for message_info in messages:
        _, sender_id, receiver_id, message_type, message, timestamp = message_info

        if message_type == 'text':
            await callback.message.answer(f'<b>Сообщение от {sender_id}</b>: {message}')

        elif message_type == 'photo':
            await callback.message.answer_photo(photo=message, caption=f'<b>Сообщение от {sender_id}</b>:')

        elif message_type == 'video':
            await callback.message.answer_video(video=message, caption=f'<b>Сообщение от {sender_id}</b>:', )

        elif message_type == 'sticker':
            await callback.message.answer(f'<b>Сообщение от {sender_id}</b>:')
            await callback.message.answer_sticker(sticker=message)

        elif message_type == 'voice':
            await callback.message.answer_voice(voice=message, caption=f'<b>Сообщение от {sender_id}</b>:', )

        elif message_type == 'video_note':
            await callback.message.answer(f'<b>Сообщение от {sender_id}</b>:')
            await callback.message.answer_video_note(video_note=message)

        elif message_type == 'animation':
            await callback.message.answer(f'<b>Сообщение от {sender_id}</b>:')
            await callback.message.answer_animation(animation=message, caption=f'<b>Сообщение от {sender_id}</b>:', )

