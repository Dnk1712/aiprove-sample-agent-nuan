CC = gcc
CFLAGS = -O3 -Wall

all: primes

primes: primes.c
	$(CC) $(CFLAGS) -o primes primes.c -lm

clean:
	rm -f primes

.PHONY: all clean
