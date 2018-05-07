/* head file for mory version string utilities */
#pragma once

void append(char *str1, char *str2, char **result);
void free_append(char *result);
void split(char *str, char sep, char ***result);
void free_split(char **result);

