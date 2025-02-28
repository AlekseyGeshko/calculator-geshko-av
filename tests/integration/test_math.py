import subprocess

import subprocess

def run_test(args, input_str, expected_returncode, expected_output=None, float_precision=None):
    """
    Запускает приложение с заданными аргументами и входными данными.
    Проверяет код возврата и (по желанию) сравнивает результат (с округлением).
    """
    res = subprocess.run(args, input=input_str, text=True, capture_output=True)

    actual_returncode = res.returncode
    # Если мы ожидаем "ошибку" (любой != 0), то проверяем только actual_returncode != 0
    # Иначе (если expected_returncode == 0) - проверяем, что вернулся 0.
    if expected_returncode != 0:
        # Проверяем, что код возврата не 0 (программа упала с ошибкой)
        assert actual_returncode != 0, (
            f"Input: {input_str!r}\n"
            f"Expected ERROR code (not 0), but got: {actual_returncode}\n"
            f"Stdout: {res.stdout!r}\n"
            f"Stderr: {res.stderr!r}"
        )
    else:
        # Ожидаем 0
        assert actual_returncode == 0, (
            f"Input: {input_str!r}\n"
            f"Expected return code 0 but got: {actual_returncode}\n"
            f"Stdout: {res.stdout!r}\n"
            f"Stderr: {res.stderr!r}"
        )

    # Если не ожидаем конкретного вывода, завершаем здесь
    if expected_output is None:
        return

    # Удаляем пробелы/переносы строк из stdout
    output = res.stdout.strip()

    if float_precision is not None:
        # Сравниваем как float с округлением
        try:
            expected_val = round(float(expected_output), float_precision)
            output_val   = round(float(output), float_precision)
            assert output_val == expected_val, (
                f"Input: {input_str!r}\n"
                f"Expected float output: {expected_val:.{float_precision}f} but got: {output!r}"
            )
        except ValueError:
            # Если output не конвертируется в float
            assert False, f"Output is not a valid float: {output!r}"
    else:
        # Сравниваем строку (для целочисленных результатов)
        assert output == expected_output, (
            f"Input: {input_str!r}\n"
            f"Expected output: {expected_output!r} but got: {output!r}"
        )


def test_case1():
    # 1. Простое сложение: "1 + 2" -> 3 (целочисленный режим)
    run_test(["./build/app.exe"], "1 + 2", 0, "3")

def test_case2():
    # 2. Разные количества скобок (правильно сбалансированы):
    # "1 + 2 * ((3 - 4))" -> 3-4=-1, 2*-1=-2, 1+(-2)=-1
    run_test(["./build/app.exe"], "1 + 2 * ((3 - 4))", 0, "-1")

def test_case3():
    # 3. Глубокая вложенность
    run_test(["./build/app.exe"], "(((((((((((((((((((((((((((1)))))))))))))))))))))))))))", 0, "1")

def test_case4():
    # 4. Выражение около 1KiB по длине.
    # Построим длинную сумму, состоящую из 500 единиц через плюс: "1+1+...+1".
    expr = "+".join(["1"] * 502)
    run_test(["./build/app.exe"], expr, 0, "502")

def test_case5():
    # 5. Некорректный ввод знаков: "1 ++ 2" – два плюса подряд, должно выдать ошибку.
    run_test(["./build/app.exe"], "1 ++ 2", 1)

def test_case6():
    """
    6. Тест в вещественном режиме: "3 / 2" должно вернуть 1.5 (или 1.5000).
    Проверяем как float до 4 знаков.
    """
    run_test(
        ["./build/app.exe", "--float"],
        "3 / 2",
        0,
        "1.5",  # Можно "1.5000", важно, что float_precision=4 сделает нужное округление
        float_precision=4
    )

def test_case7():
    # 7. Некорректный ввод символов: "abc + 5" – буквы недопустимы.
    run_test(["./build/app.exe"], "abc + 5", 1)

def test_case8():
    # 8. Умножение чисел: "2 * 3" -> 6
    run_test(["./build/app.exe"], "2 * 3", 0, "6")

def test_case9():
    # 9. Деление чисел (целочисленно): "10 / 3" -> 3
    run_test(["./build/app.exe"], "10 / 3", 0, "3")

def test_case10():
    # 10. Вычитание: "10 - 4" -> 6
    run_test(["./build/app.exe"], "10 - 4", 0, "6")

def test_case11():
    # 11. Комбинированное выражение: "1 + 2 * 3 - 4 / 2"
    # 2*3=6, 4/2=2, итого 1+6-2=5
    run_test(["./build/app.exe"], "1 + 2 * 3 - 4 / 2", 0, "5")

def test_case12():
    # 12. Выражение с унарным минусом в скобках
    run_test(["./build/app.exe"], "1 - (3 + 4)",0 , "-6")

def test_case13():
    # 13. Двойной унарный минус: "--3" -> 3
    run_test(["./build/app.exe"], "--3", 1)

def test_case14():
    # 14. Комбинация унарного и бинарного минуса: "-3 * (2 + 4)" -> -3 * 6 = -18
    run_test(["./build/app.exe"], "-3 * (2 + 4)", 1)

def test_case15():
    """
    15. Сложное выражение в вещественном режиме: "((1+2)*3 - (4/2))" => 7.0
    """
    run_test(
        ["./build/app.exe", "--float"],
        "((1+2)*3 - (4/2))",
        0,
        "7.0",
        float_precision=4
    )

def test_case16():
    """
    16. "10 / 3" в режиме float => 3.3333 (округляем до 4 знаков)
    """
    run_test(
        ["./build/app.exe", "--float"],
        "10 / 3",
        0,
        "3.3333",
        float_precision=4
    )

def test_case18():
    """
    18. Сложение в режиме float: "3.5 + 2.5" => 6.0
    (Исходно стояло 1 в expected_returncode, но кажется это ошибка.
    Если программа обрабатывает "3.5 + 2.5" - результат 6.0)
    """
    run_test(
        ["./build/app.exe", "--float"],
        "3 + 2/3",
        0,          # Ожидаем успешный возврат
        "3.6667",      # Проверяем как float
        float_precision=4
    )

def test_case20():
    """
    20. Умножение и деление в режиме float: (3 * 2) / 4 => 1.5
    """
    run_test(
        ["./build/app.exe", "--float"],
        "(3 * 2) / 4",
        0,
        "1.5",
        float_precision=4
    )

def test_case21():
    # 20. Умножение и деление в режиме float
    run_test(["./build/app.exe", "--float"], "(3 * 2) / +4", 1)

def run_all_tests():
    tests = [
        test_case1,
        test_case2,
        test_case3,
        test_case4,
        test_case5,
        test_case6,
        test_case7,
        test_case8,
        test_case9,
        test_case10,
        test_case11,
        test_case12,
        test_case13,
        test_case14,
        test_case15,
        test_case16,
        test_case17,
        test_case18,
        test_case19,
        test_case20,
        test_case21
    ]
    for test in tests:
        test()
        print(f"{test.__name__} passed.")

if __name__ == "__main__":
    run_all_tests()
