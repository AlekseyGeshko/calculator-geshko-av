# tests/integration/test_server.py

import subprocess
import time
import requests
import json
import pytest
import os

@pytest.fixture(scope="module")
def server_proc():
    """
    Фикстура для запуска и остановки Python-сервера.
    Запускает сервер в фоновом процессе, даёт ему 1 сек. подняться,
    затем по окончании тестов завершает процесс.
    """
    python_bin = os.path.join("build", "venv", "bin", "python")
    cmd = [python_bin, "server/server.py"]
    proc = subprocess.Popen(cmd)
    time.sleep(1)  # Небольшая пауза для инициализации

    yield proc

    proc.terminate()
    proc.wait()


# -----------------------------------------------------------------------------
# Вспомогательные функции
# -----------------------------------------------------------------------------

def post_calc(expression, use_float=None, content_type="application/json"):
    """
    Упрощает вызов POST /calc.
    - expression: строка (арифметическое выражение) или None (для эмуляции отсутствия тела)
    - use_float: True/False/None (None => параметр не добавляется)
    - content_type: тип контента (по умолчанию application/json)
    Возвращает (status_code, json_body или None, raw_text).
    """
    url = "http://localhost:8000/calc"
    if use_float is not None:
        url += f"?float={str(use_float).lower()}"

    headers = {
        "Content-Type": content_type
    }

    if expression is None:
        data = None
    else:
        data = json.dumps(expression)

    resp = requests.post(url, data=data, headers=headers)

    try:
        return resp.status_code, resp.json(), resp.text
    except ValueError:
        # Если невалидный JSON в ответе
        return resp.status_code, None, resp.text

# -----------------------------------------------------------------------------
# Тесты на целочисленный режим
# -----------------------------------------------------------------------------

def test_calc_int_simple(server_proc):
    """
    3 + 2 = 5 (целочисленный режим по умолчанию)
    """
    status, jdata, _ = post_calc("3 + 2")
    assert status == 200, f"Unexpected status code: {status}"
    assert jdata == "5", f"Expected '5', got {jdata}"

def test_calc_int_division(server_proc):
    """
    10 / 3 => 3 (целочисленный режим)
    """
    status, jdata, _ = post_calc("10 / 3")
    assert status == 200
    assert jdata == "3"

def test_calc_int_negative_result(server_proc):
    """
    1 - 5 => -4 (целочисленный режим)
    """
    status, jdata, _ = post_calc("1 - 5")
    assert status == 200
    assert jdata == "-4"

# -----------------------------------------------------------------------------
# Тесты на вещественный режим
# -----------------------------------------------------------------------------

def test_calc_float_div(server_proc):
    """
    3 / 2 => 1.5 (float режим)
    Сервер может вернуть '1.5' или '1.5000', мы парсим как float.
    """
    status, jdata, _ = post_calc("3 / 2", use_float=True)
    assert status == 200, f"Expected 200, got {status}"

    try:
        val = float(jdata)
        assert abs(val - 1.5) < 1e-9, f"Expected 1.5, got {val}"
    except (TypeError, ValueError):
        pytest.fail(f"Server returned non-float response: {jdata}")

# -----------------------------------------------------------------------------
# Тесты на ошибки и крайние случаи
# -----------------------------------------------------------------------------

def test_calc_error_syntax(server_proc):
    """
    Некорректный ввод -> 500
    """
    status, jdata, raw = post_calc("1 ++ 2")
    assert status == 500, f"Expected 500, got {status}"
    assert jdata is not None, "Expected JSON body"
    assert "error" in jdata, f"Missing 'error' in response: {raw}"

def test_calc_error_div_by_zero(server_proc):
    """
    Проверяем деление на 0. Предполагаем, что C-программа возвращает ошибку => 500
    """
    status, jdata, raw = post_calc("10 / 0")
    assert status == 500, f"Expected 500, got {status}"
    assert "error" in jdata, f"Missing 'error' in {jdata}"

def test_calc_huge_expr(server_proc):
    """
    Проверяем очень длинное выражение (например, много плюсов).
    Если C-программа ограничена в размере буфера, ожидаем 500 (ошибка).
    """
    huge_expr = "+".join(["1"] * 10000)  # 10000 слагаемых
    status, jdata, raw = post_calc(huge_expr)
    # В зависимости от реализации С-калькулятора:
    # - либо 500 если переполнен буфер/ошибка парсинга
    # - либо вернёт 10000
    if status == 200:
        assert jdata == "10000", f"Unexpected sum result: {jdata}"
    else:
        # Если 500, значит слишком длинное для парсинга
        assert status == 500, f"Expected 200 or 500, got {status}"

def test_calc_empty_body(server_proc):
    """
    Пустое тело запроса -> ожидаем 400 (по нашему ТЗ) или что-то ещё.
    Смотря как реализовано на сервере.
    Если сервер отвечает 400, проверяем.
    """
    url = "http://localhost:8000/calc"
    resp = requests.post(url, headers={"Content-Type": "application/json"}, data=None)

    # Если сервер жёстко настроен на 400:
    #  (или вы можете проверить, что вернёт 500, смотря код)
    assert resp.status_code in (400, 500), f"Expected 400 or 500, got {resp.status_code}"

def test_calc_invalid_content_type(server_proc):
    """
    Если Content-Type не application/json, сервер может вернуть 400 (invalid content type).
    """
    status, jdata, raw = post_calc("3 + 2", content_type="text/plain")
    # Предполагаем, что сервер вернёт 400 (или 500) при 'invalid content type'
    assert status in (400, 500), f"Expected 400 or 500, got {status}"
    # Можно проверить поле 'error'
    if jdata:
        assert "error" in jdata, f"Missing 'error' in response: {raw}"

def test_calc_query_false(server_proc):
    """
    Явное float=false => целочисленный режим,
    проверяем, что 3 / 2 = 1
    """
    status, jdata, raw = post_calc("3 / 2", use_float=False)
    assert status == 200
    assert jdata == "1", f"Expected '1', got {jdata}"

def test_calc_weird_chars(server_proc):
    """
    Содержатся ли буквы или другие символы. Ожидаем 500?
    """
    status, jdata, raw = post_calc("abc + 123")
    assert status == 500, f"Expected 500, got {status}"
    assert jdata is not None
    assert "error" in jdata, "Expected 'error' field in the response"
