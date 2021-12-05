import asyncio
import psycopg2
from config import host, user, password, db_name

def validation(command, ready_data):
    request_answer = 'АМОЖНА? РКСОК/1.0\r\n'
    request_body = command + ' ' + ready_data[0] + ' ' + 'РКСОК/1.0\r\n'
    request_phone = ' '.join(ready_data[1])
    if request_phone != '':
        ready_request = request_answer + request_body + request_phone + '\r\n'
    else:
        ready_request = request_answer + request_body
    print(f'[INFO serv] запрос на сервер проврки:\r\n{ready_request}')
    return 'МОЖНА РКСОК/1.0'

# Функция получения данных из БД
def OTDOVAI(ready_data):
    user_name = ready_data[0]
    try:
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )

        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT name
                    FROM users;"""
            )
            all_names = [i[0] for i in cursor.fetchall()]

        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT phone
                    FROM users
                    WHERE name = '{user_name}';"""
            )

            user_phone = cursor.fetchone()

    except Exception as _ex:
        print('[INFO sql] Error while working with PostgreSQL', _ex)
    finally:
        if connection:
            connection.close()
            print('[INFO sql] PostgreSQL connection closed')
            # print(all_names, user_name, user_phone, sep='\n')

    if user_name in all_names and user_phone[0] != '':
        return f'НОРМАЛДЫКС РКСОК/1.0\r\n{user_phone[0]}'
    else:
        return 'НИНАШОЛ РКСОК/1.0'

# Функция записи данных в БД
def ZAPISHI(ready_data):
    user_name = ready_data[0]
    user_phone = ' '.join(ready_data[1])

    try:
        # connect to exist database
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )

        connection.autocommit = True

    # insert data into table
        with connection.cursor() as cursor:
            cursor.execute(
                f"""INSERT INTO users(name, phone) 
                VALUES ('{user_name}', '{user_phone}');"""
            )
            print('[INFO sql] Data was successfully inserted')

    except Exception as _ex:
        print('[INFO sql] Error while working with PostgreSQL', _ex)
    finally:
        if connection:
            connection.close()
            print('[INFO sql] PostgreSQL connection closed')

    return 'НОРМАЛДЫКС РКСОК/1.0'

# Функция удаления номера из базы данных
def UDALI(ready_data):
    user_name = ready_data[0]
    try:
        # connect to exist database
        connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )

        connection.autocommit = True

        with connection.cursor() as cursor:
            cursor.execute(
                f"""SELECT name
                    FROM users;"""
            )
            all_names = [i[0] for i in cursor.fetchall()]

        if user_name in all_names:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""UPDATE users
                        SET phone = '' 
                        WHERE name = '{user_name}';"""
                )
                print('[INFO sql] Data was successfully deleted')

            return f'НОРМАЛДЫКС РКСОК/1.0'
        else:
            return 'НИНАШОЛ РКСОК/1.0'

    except Exception as _ex:
        print('[INFO sql] Error while working with PostgreSQL', _ex)
    finally:
        if connection:
            connection.close()
            print('[INFO sql] PostgreSQL connection closed')


COMMAND_TO_ACTION = {
    'ОТДОВАЙ': OTDOVAI,
    'ЗОПИШИ': ZAPISHI,
    'УДОЛИ': UDALI
}


async def main():
    server = await asyncio.start_server(serve_client, '127.0.0.1', 8888)

    addr = server.sockets[0].getsockname()
    print(f'[INFO serv] Serving on {addr}')

    async with server:
        await server.serve_forever()


async def serve_client(reader, writer):  # ОБРАБОТЧИК КЛИЕНТА

    # ПОЛУЧАЕМ СЫРОЙ ЗАПРОС ОТ КЛИЕНТА
    data = await reader.read(1024)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print(f"[INFO serv] Received {message!r} from {addr!r}")

    # ПАРСИМ ЗАПРОС ОТ КЛИЕНТА
    data_lines = message.split('\r\n')  # Создаем список из всех строк
    # В переменной сохраняем основной полный запрос от клиента
    header = data_lines[0].split(' ')

    try:
        # Разбиваем запрос на команду и врсию протокола в переменные
        command, protocol_version = header.pop(0), header.pop(-1)
        # Сохраняем в переменную текст пользователя из запроса
        user_text = ' '.join(header)
        # Создаем список телефонов
        body_phone = [num for num in data_lines[1:] if num]
        # Создаем список с именем и списком телефонов
        ready_data = [user_text, body_phone]

        # ПРОВЕРЯЕМ ПРАВИЛЬНОСТЬ ЗАПРОСА, выполняем команды and send response
        if protocol_version == 'РКСОК/1.0':
            if command in COMMAND_TO_ACTION:
                if user_text:
                    if validation(command, ready_data) == "МОЖНА РКСОК/1.0":
                        print(
                            '[INFO serv] Ответ от сервера проверки:\r\nМОЖНА РКСОК/1.0')
                        result = COMMAND_TO_ACTION[command](ready_data)
                        writer.write(result.encode())
                        await writer.drain()
                else:
                    writer.write('НИПОНЯЛ РКСОК/1.0'.encode())
                    await writer.drain()
            else:
                print[f'[INFO serv] ~{command}~ Unknown server command']
        else:
            try:
                print[f'[INFO serv] ~{protocol_version}~ Unknown protocol command']
            except TypeError as _ex:
                print(f'Твой запрос не правильный дружок:', _ex)
                writer.write('НИПОНЯЛ РКСОК/1.0'.encode())
                await writer.drain()

        print("[INFO serv] Close the connection")
        writer.close()

    except IndexError as _ex:
        print(f'Твой запрос не правильный дружок:', _ex)
        writer.write('НИПОНЯЛ РКСОК/1.0'.encode())
        await writer.drain()
        print("[INFO serv] Close the connection")
        writer.close()


if __name__ == '__main__':
    asyncio.run(main())