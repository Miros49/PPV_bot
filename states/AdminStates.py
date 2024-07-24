from aiogram.fsm.state import State, StatesGroup


class AdminStates(StatesGroup):
    input_id: State = State()
