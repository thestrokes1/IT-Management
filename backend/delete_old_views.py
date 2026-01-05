import os
try:
    os.remove('apps/frontend/views.py')
    print('Deleted: apps/frontend/views.py')
except FileNotFoundError:
    print('File not found')
except Exception as e:
    print(f'Error: {e}')

