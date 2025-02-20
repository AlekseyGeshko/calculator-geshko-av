#include <stdio.h>
#include <string.h>
#include <ctype.h>

#define INPUT_SIZE 1024

int parseNumber(char* expression)
{
    int result = 0;
    while (*expression && isdigit((char)*expression))
    {
        result = result * 10 + (*expression - '0');
        expression++;
    }

    return result;
}

void trim(char *str)
{
    char *start = str;
    while (*start && isspace((unsigned char)*start))
        start++;

    if (*start == '\0') {
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
        printf("%s", buffer);
    }

    return 0;
}