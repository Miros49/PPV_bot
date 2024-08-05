from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    input_id: State = State()
    edit_price_buy: State = State()
    edit_price_sell: State = State()
    input_answer: State = State()
