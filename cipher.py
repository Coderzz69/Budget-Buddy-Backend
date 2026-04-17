def progressive_cipher(text):
    result = ""
    for i, char in enumerate(text):
        shift = i + 1
        if char.isupper():
            # Shift A-Z
            result += chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
        elif char.islower():
            # Shift a-z
            result += chr((ord(char) - ord('a') + shift) % 26 + ord('a'))
        else:
            # Keep non-alphabetical characters as they are
            result += char
    return result

key = "THE TREASURE NEEDS SCRAMBLING"
scrambled = progressive_cipher(key)
print(scrambled)