from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    input_id: State = State()
    edit_price_buy: State = State()
    edit_price_sell: State = State()
    input_answer: State = State()
    ban_input_period: State = State()
    input_amount_to_edit: State = State()
    in_chat: State = State()
    input_newsletter: State = State()
