#include <gtest/gtest.h>

extern "C"
{
#include "../../src/calculator.h"
}

// parseNumber: при вводе "abc" => exit(1)
TEST(ParseNumberTest, InvalidLetters)
{
    char input[] = "abc";
    char *expr = input;
    EXPECT_EXIT({ parseNumber(&expr); }, ::testing::ExitedWithCode(1), "");
}

// parseFactor: унарный минус запрещён, "-3" => exit(1)
TEST(ParseFactorTest, UnaryMinusFails)
{
    char input[] = "-3";
    char *expr = input;
    EXPECT_EXIT({ parseFactor(&expr); }, ::testing::ExitedWithCode(1), "");
}

// parseTerm: деление на 0 -> exit(1)
TEST(ParseTermTest, DivisionByZero)
{
    char input[] = "3/0";
    char *expr = input;
    EXPECT_EXIT({ parseTerm(&expr); }, ::testing::ExitedWithCode(1), "");
}

// parseExpressionF: унарный + запрещён => "+5" => exit(1)
TEST(ParseExpressionFTest, UnaryPlusFails)
{
    char input[] = "+5";
    char *expr = input;
    EXPECT_EXIT({ parseExpressionF(&expr); }, ::testing::ExitedWithCode(1), "");
}

// validateInput (негатив)
// Если встретились недопустимые символы, должна быть ошибка
TEST(ValidateInputTest, InvalidChars)
{
    const char *str = "abc$+5"; // $ — недопустимый
    EXPECT_EXIT({ validateInput(str); }, ::testing::ExitedWithCode(1), "");
}

// parseNumberF (негатив): "abc" => exit(1)
TEST(ParseNumberFTest, InvalidLetters)
{
    char input[] = "abc";
    char *expr = input;
    EXPECT_EXIT({ parseNumberF(&expr); }, ::testing::ExitedWithCode(1), "");
}

// parseFactorF (негатив): "abc" => exit(1)
TEST(ParseFactorFTest, InvalidLetters)
{
    char input[] = "abc";
    char *expr = input;
    EXPECT_EXIT({ parseFactorF(&expr); }, ::testing::ExitedWithCode(1), "");
}

// parseTermF (негатив): деление на 0 => exit(1)
TEST(ParseTermFTest, DivisionByZeroF)
{
    char input[] = "3/0";
    char *expr = input;
    EXPECT_EXIT({ parseTermF(&expr); }, ::testing::ExitedWithCode(1), "");
}
