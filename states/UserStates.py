from aiogram.dispatcher.filters.state import State, StatesGroup


class UserState(StatesGroup):
    waiting_for_user_id: State = State()
    waiting_for_order_id: State = State()
    waiting_for_problem_description: State = State()
    # TODO: ввод валюты
