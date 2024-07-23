from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    input_amount: State = State()
    waiting_for_order_id: State = State()
    waiting_for_problem_description: State = State()
    in_chat: State = State()
    input_business_name: State = State()
    input_account_description: State = State()
    top_up: State = State()
