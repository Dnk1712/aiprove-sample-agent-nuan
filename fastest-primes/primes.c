#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* Count primes <= N (1 <= N <= 5000000) with an odd-only sieve.
   Reads N from stdin, prints the count on stdout. */

int main(void) {
    long n;
    if (scanf("%ld", &n) != 1) return 0;
    if (n < 2) {
        puts("0");
        return 0;
    }
    /* c[k] marks the odd number 2k+1 as composite. */
    long m = (n + 1) / 2;
    unsigned char *c = calloc(m, 1);
    if (!c) return 1;
    long sq = (long)sqrt((double)n);
    for (long i = 3; i <= sq; i += 2) {
        if (!c[i / 2]) {
            for (long j = i * i; j <= n; j += 2 * i)
                c[j / 2] = 1;
        }
    }
    long cnt = 1; /* prime 2 */
    for (long i = 3; i <= n; i += 2)
        if (!c[i / 2]) cnt++;
    printf("%ld\n", cnt);
    free(c);
    return 0;
}
