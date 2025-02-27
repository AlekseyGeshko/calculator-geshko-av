#include <gtest/gtest.h>

// Подключаем ваши C-функции как extern "C"
extern "C"
{
#include "../../src/calculator.h"
}

TEST(ParseNumberTest, ValidInput)
{
    char input[] = "123";
    char *expr = input;
    int val = parseNumber(&expr);
    EXPECT_EQ(val, 123);
}

TEST(ParseNumberFTest, ValidFloatInput)
{
    char input[] = "456";
    char *expr = input;
    double val = parseNumberF(&expr);
    EXPECT_DOUBLE_EQ(val, 456.0);
}

TEST(ParseFactorTest, SimpleNumber)
{
    char input[] = "42";
    char *expr = input;
    int val = parseFactor(&expr);
    EXPECT_EQ(val, 42);
}

TEST(ParseExpressionTest, ComplexExpression)
{
    char input[] = "1+2*3";
    char *expr = input;
    int val = parseExpression(&expr);
    EXPECT_EQ(val, 7); // 1 + 2*3 = 1+6=7
}

TEST(ParseExpressionFTest, SimpleFloatExpression)
{
    char input[] = "10/4";
    char *expr = input;
    double val = parseExpressionF(&expr);
    EXPECT_DOUBLE_EQ(val, 2.5);
}

// skipSpaces
TEST(SkipSpacesTest, LeadingSpaces)
{
    char input[] = "   hello";
    char *ptr = input;
    skipSpaces(&ptr);
    // Ожидаем, что ptr теперь указывает на 'h'
    EXPECT_STREQ("hello", ptr);
}

TEST(SkipSpacesTest, NoSpaces)
{
    char input[] = "world";
    char *ptr = input;
    skipSpaces(&ptr);
    // ptr не меняется
    EXPECT_STREQ("world", ptr);
}

// trim
TEST(TrimTest, LeadingAndTrailingSpaces)
{
    char input[] = "   hello   ";
    trim(input);
    // Должно получиться "hello"
    EXPECT_STREQ("hello", input);
}

TEST(TrimTest, EmptyString)
{
    char input[] = "    ";
    trim(input);
    // Ожидаем пустую строку
    EXPECT_STREQ("", input);
}

// validateInput (положительный сценарий)
// Допустимые символы: цифры, пробелы, ( ) * + / -
TEST(ValidateInputTest, ValidChars)
{
    const char *str = "1 + 2 - (3*4)";
    // Если функция не вызывает exit(1), значит всё ок
    validateInput(str);
    SUCCEED(); // Явно указываем, что дошли сюда без ошибок
}

// parseNumberF (доп. позитив)
// Проверим ещё один пример
TEST(ParseNumberFTest, AnotherFloatInput)
{
    char input[] = "789";
    char *expr = input;
    double val = parseNumberF(&expr);
    EXPECT_DOUBLE_EQ(789.0, val);
}

// parseFactorF (положительный сценарий)
TEST(ParseFactorFTest, SimpleNumberF)
{
    char input[] = "42";
    char *expr = input;
    double val = parseFactorF(&expr);
    EXPECT_DOUBLE_EQ(val, 42.0);
}

// parseTermF (положительный сценарий)
TEST(ParseTermFTest, MultiplicationF)
{
    char input[] = "2*3";
    char *expr = input;
    double val = parseTermF(&expr);
    EXPECT_DOUBLE_EQ(val, 6.0);
}
