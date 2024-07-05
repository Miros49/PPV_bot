from datetime import datetime


def convert_datetime(datetime_str: str) -> str:
    dt = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')

    # Форматируем объект datetime в нужный формат
    european_format = dt.strftime('%d.%m.%Y %H:%M')

    return european_format
