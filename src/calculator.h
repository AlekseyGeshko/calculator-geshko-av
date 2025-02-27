#ifndef CALCULATOR_H
#define CALCULATOR_H

extern int use_float;
void skipSpaces(char **expression);
void trim(char *str);
void validateInput(const char *str);
int parseNumber(char **expression);
int parseFactor(char **expression);
int parseTerm(char **expression);
int parseExpression(char **expression);
double parseNumberF(char **expression);
double parseFactorF(char **expression);
double parseTermF(char **expression);
double parseExpressionF(char **expression);

#endif // CALCULATOR_H
