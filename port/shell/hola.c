#include <stdio.h>

int main(void)
{
    int numero;
    printf("Hola desde el cyberdeck. Ingresá un número: ");
    fflush(stdout);
    if (scanf("%d", &numero) != 1) {
        fputs("Entrada inválida.\n", stderr);
        return 1;
    }
    printf("Escribiste %d. ¡C funciona!\n", numero);
    return 0;
}
