#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>

#define INPUT_SIZE 1024

/*
Вход: строка
Выход: число
Задача: Разбирает множитель, который является числом или выражением в скобках
*/
int parseFactor(char **expression);

/*
Вход: строка
Выход: число
Задача: Разбирает терм с операциями умножения и деления
*/
int parseTerm(char **expression);

/*
Вход: строка
Выход: число
Задача: Разбирает арифметическое выражение с операциями сложения и вычитания
*/
int parseExpression(char **expression);

/*
Вход: строка
Выход: число
Задача: возвращает число, представленное в виде строки
*/
int parseNumber(char **expression);

/*
Вход: строка
Выход: строка
Задача: пропускает подряд идущие пробелы
*/
void skipSpaces(char **expression);

/*
Вход: строка
Выход: строка
Задача: удалить все пробелы вначале и вконце строки
*/
void trim(char *str);

int parseNumber(char **expression)
{
    int result = 0;
    while (**expression && isdigit((char)**expression))
    {
        result = result * 10 + (**expression - '0');
        (*expression)++;
    }

    return result;
}

void skipSpaces(char **expression)
{
    while (**expression && isspace((unsigned char)**expression))
        (*expression)++;
}

int parseFactor(char **expression)
{
    skipSpaces(expression);
    if (**expression == '(')
    {
        (*expression)++;
        int result = parseExpression(expression);
        skipSpaces(expression);

        if (**expression == ')')
            (*expression)++;

        return result;
    }

    return parseNumber(expression);
}

int parseTerm(char **expression)
{
    int result = parseFactor(expression);
    while (true)
    {
        skipSpaces(expression);
        if (**expression == '*')
        {
            (*expression)++;
            result *= parseFactor(expression);
        }
        else if (**expression == '/')
        {
            (*expression)++;
            int divisor = parseFactor(expression);
            if (divisor)
                result /= divisor;
        }
        else
            break;
    }

    return result;
}

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
            break;
    }

    return result;
}

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

int main()
{
    char buffer[INPUT_SIZE];
    while (fgets(buffer, sizeof(buffer), stdin))
    {
        trim(buffer);
        char *expression = buffer;
        printf("%d\n", parseExpression(&expression));
    }

    return 0;
}
