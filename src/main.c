#include <ctype.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "calculator.h"

#define INPUT_SIZE 1024

// Глобальный флаг: 0 – целочисленный режим, 1 – вещественный режим
int use_float = 0;

/* Прототипы функций для целочисленного режима */
int parseExpression(char **expression);

/* Прототипы функций для вещественного режима */
double parseExpressionF(char **expression);

/*
Вход: указатель на строку (pointer to pointer)
Выход: ничего
Задача: Пропускает пробельные символы в строке
*/
void skipSpaces(char **expression)
{
    while (**expression && isspace((unsigned char)**expression))
        (*expression)++;
}

/*
Вход: строка
Выход: строка (обрезанная)
Задача: Удаляет все пробелы в начале и в конце строки
*/
void trim(char *str)
{
    char *start = str;
    while (*start && isspace((unsigned char)*start))
        start++;
    if (*start == '\0')
    {
        str[0] = '\0';
        return;
    }
    char *end = start + strlen(start) - 1;
    while (end > start && isspace((unsigned char)*end))
        end--;
    *(end + 1) = '\0';
    if (start != str)
        memmove(str, start, end - start + 2);
}

/*
Вход: строка
Выход: ничего (выход через exit, если обнаружен недопустимый символ)
Задача: Проверяет, что входная строка содержит только разрешённые символы:
цифры, пробельные символы, символы: ( ) * + / -
*/
void validateInput(const char *str)
{
    while (*str)
    {
        char c = *str;
        if (!(isdigit((unsigned char)c) || isspace((unsigned char)c) || c == '(' || c == ')' || c == '*' || c == '+' ||
              c == '/' || c == '-'))
        {
            // Недопустимый символ – завершаем работу с ошибкой.
            exit(1);
        }
        str++;
    }
}

/* ========== ЦЕЛОЧИСЛЕННЫЙ РЕЖИМ ========== */

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (int)
Задача: Возвращает число, представленное в виде строки (последовательность цифр)
*/
int parseNumber(char **expression)
{
    if (!isdigit((unsigned char)**expression))
    {
        // Первый символ не цифра – значит, это не число!
        exit(1);
    }
    int result = 0;
    while (**expression && isdigit((unsigned char)**expression))
    {
        result = result * 10 + (**expression - '0');
        (*expression)++;
    }
    return result;
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (int)
Задача: Разбирает множитель, который является числом или выражением в скобках
*/
int parseFactor(char **expression)
{
    skipSpaces(expression);

    // Если встречаем знак + или - именно в начале фактора, это запрещённый "унарный" вариант.
    if (**expression == '+' || **expression == '-')
    {
        exit(1);
    }

    if (**expression == '(')
    {
        (*expression)++; // пропускаем '('
        int result = parseExpression(expression);
        skipSpaces(expression);
        if (**expression != ')')
        {
            exit(1); // отсутствует закрывающая скобка
        }
        (*expression)++; // пропускаем ')'
        return result;
    }
    else
    {
        return parseNumber(expression);
    }
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (int)
Задача: Разбирает терм с операциями умножения и деления
*/
int parseTerm(char **expression)
{
    int result = parseFactor(expression);
    while (true)
    {
        skipSpaces(expression);
        if (**expression == '*')
        {
            (*expression)++;
            int factor = parseFactor(expression);
            result *= factor;
        }
        else if (**expression == '/')
        {
            (*expression)++;
            int divisor = parseFactor(expression);
            if (divisor == 0)
                exit(1); // деление на 0 запрещено
            result /= divisor;
        }
        else
        {
            break;
        }
    }
    return result;
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (int)
Задача: Разбирает арифметическое выражение с операциями сложения и вычитания
*/
int parseExpression(char **expression)
{
    int result = parseTerm(expression);
    while (true)
    {
        skipSpaces(expression);
        if (**expression == '+')
        {
            (*expression)++;
            result += parseTerm(expression);
        }
        else if (**expression == '-')
        {
            (*expression)++;
            result -= parseTerm(expression);
        }
        else
        {
            break;
        }
    }
    return result;
}

/* ========== ВЕЩЕСТВЕННЫЙ РЕЖИМ ========== */

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (double)
Задача: Разбирает число (последовательность цифр) в вещественном режиме
*/
double parseNumberF(char **expression)
{
    if (!isdigit((unsigned char)**expression))
    {
        exit(1);
    }
    double result = 0.0;
    while (**expression && isdigit((unsigned char)**expression))
    {
        result = result * 10.0 + ((double)(**expression - '0'));
        (*expression)++;
    }
    return result;
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (double)
Задача: Разбирает множитель, который является числом или выражением в скобках, в вещественном режиме
*/
double parseFactorF(char **expression)
{
    skipSpaces(expression);
    // Если встречаем унарный плюс, это ошибка.
    if (**expression == '+' || **expression == '-')
    {
        exit(1);
    }

    if (**expression == '(')
    {
        (*expression)++; // пропускаем '('
        double result = parseExpressionF(expression);
        skipSpaces(expression);
        if (**expression != ')')
        {
            exit(1); // отсутствует закрывающая скобка
        }
        (*expression)++; // пропускаем ')'
        return result;
    }
    return parseNumberF(expression);
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (double)
Задача: Разбирает терм с операциями умножения и деления в вещественном режиме
*/
double parseTermF(char **expression)
{
    double result = parseFactorF(expression);
    while (true)
    {
        skipSpaces(expression);
        if (**expression == '*')
        {
            (*expression)++;
            double factor = parseFactorF(expression);
            result *= factor;
        }
        else if (**expression == '/')
        {
            (*expression)++;
            double divisor = parseFactorF(expression);
            if (divisor == 0.0)
                exit(1); // деление на 0 запрещено
            result /= divisor;
        }
        else
        {
            break;
        }
    }
    return result;
}

/*
Вход: указатель на строку (pointer to pointer)
Выход: число (double)
Задача: Разбирает арифметическое выражение с операциями сложения и вычитания в вещественном режиме
*/
double parseExpressionF(char **expression)
{
    double result = parseTermF(expression);
    while (true)
    {
        skipSpaces(expression);
        if (**expression == '+')
        {
            (*expression)++;
            result += parseTermF(expression);
        }
        else if (**expression == '-')
        {
            (*expression)++;
            result -= parseTermF(expression);
        }
        else
        {
            break;
        }
    }
    return result;
}

/*
Вход: аргументы командной строки и данные со стандартного потока ввода
Выход: вывод результата вычисления через stdout
Задача: Читает входной текст, проверяет корректность символов, разбирает арифметическое выражение
в целочисленном или вещественном режиме (в зависимости от флага --float), и выводит результат.
*/
#ifndef UNIT_TEST
int main(int argc, char *argv[])
{
    if (argc > 1)
    {
        if (strcmp(argv[1], "--float") == 0)
        {
            use_float = 1;
        }
    }

    char buffer[INPUT_SIZE];
    char input[INPUT_SIZE] = "";

    /* Читаем весь входной поток до EOF */
    while (fgets(buffer, sizeof(buffer), stdin))
    {
        strcat(input, buffer);
    }

    trim(input);
    validateInput(input);

    char *expression = input;

    /* После разбора проверяем, что в строке не осталось лишних символов */
    if (use_float)
    {
        double result = parseExpressionF(&expression);
        skipSpaces(&expression);
        if (*expression != '\0') // Если есть лишние символы, это ошибка
            exit(1);
        printf("%f\n", result);
    }
    else
    {
        int result = parseExpression(&expression);
        skipSpaces(&expression);
        if (*expression != '\0') // Если есть лишние символы, это ошибка
            exit(1);
        printf("%d\n", result);
    }

    return 0;
}
#endif
