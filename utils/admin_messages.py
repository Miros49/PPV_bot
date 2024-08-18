from core import bot
from database import *
from keyboards import AdminKeyboards as Admin_kb
from lexicon import *
import utils


async def send_information(target: str, target_id: int, chat_id: int, message_id: int):
    if target == 'user':
        user = get_user(target_id)
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
            reply_markup=Admin_kb.inspect_user_kb(target_id, bans_info is not None)
        )

    elif target == 'order':
        # order = get_order(target_id)
        pass

    elif target == 'deal':
        deal_id, buyer_id, buyer_order_id, seller_id, seller_order_id, status, created_at = get_deal(target_id)
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
        # report = get_report(target_id)
        pass

    else:
        pass


