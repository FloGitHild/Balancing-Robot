import itertools
import string
kombinationen = []

def letter_sequence():
    alphabet = string.ascii_uppercase  # A–Z
    length = 1

    while (length < 26):  # läuft unendlich
        for combo in itertools.product(alphabet, repeat=length):
            yield ''.join(combo)
        length += 1


# Endlose Ausgabe:
for s in letter_sequence():
    kombinationen.append(s)
print(kombinationen)