import logging

logger = logging.getLogger(__name__)

lines = open('main.py', 'r', encoding='utf-8').readlines()
lines[577] = '                            except Exception as e:\n'
lines.insert(578, '                                logger.warning(f"Skipping signal due to error: {e}")\n')
open('main.py', 'w', encoding='utf-8').writelines(lines)
print("Fixed indentation error")
