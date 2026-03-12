lines = open('main.py', 'r', encoding='utf-8').readlines()
# Fix the position check: only compare to int if not a PositionSizing
lines[585] = '                        elif not hasattr(position, \'lot\') and position != 0:\n'
open('main.py', 'w', encoding='utf-8').writelines(lines)
print("Fixed position check at line 586")
