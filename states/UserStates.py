from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    input_amount: State = State()
    waiting_for_order_id: State = State()
    waiting_for_problem_description: State = State()
    in_chat: State = State()
    in_chat_waiting_complaint: State = State()
    input_business_name: State = State()
    input_business_price: State = State()
    input_account_description: State = State()
    input_account_price: State = State()
    top_up: State = State()
    input_card_number: State = State()
