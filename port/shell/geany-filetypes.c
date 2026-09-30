[build-menu]
FT_00_LB=Comprobar C (F8)
FT_00_CM=gcc -std=c17 -Wall -Wextra -Wpedantic -g -c "%f"
FT_00_WD=%d
FT_01_LB=Compilar C (F9)
FT_01_CM=gcc -std=c17 -Wall -Wextra -Wpedantic -g -o "%e" "%f" -lm
FT_01_WD=%d
EX_00_LB=Compilar y ejecutar C (F5)
EX_00_CM=gcc -std=c17 -Wall -Wextra -Wpedantic -g -o "%e" "%f" -lm && "./%e"
EX_00_WD=%d
