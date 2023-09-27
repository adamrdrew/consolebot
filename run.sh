#!/bin/bash

while true; do
    python get_data.py
    if [ $? -ne 0 ]; then
        echo "get_data.py failed. Restarting..."
        continue
    fi

    python process_data.py
    if [ $? -ne 0 ]; then
        echo "process_data.py failed. Restarting..."
        continue
    fi

    python trainer.py
    if [ $? -ne 0 ]; then
        echo "trainer.py failed. Restarting..."
        continue
    fi

    # If all commands succeed, break out of the loop
    break
done

echo "All commands executed successfully!"
