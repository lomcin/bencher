# Bencher
A benchmarking tool for software in terms of CPU, RAM, and Storage (read, write) usage.


# Dependencies

* Python 3.x
* venv

## Installing *venv*
```bash
pip3 install venv
```


## Configuring virtual environment
```bash
./env.sh
```

# Running the Bencher

Modify the **cfg** attributes in ```src/bench.py```. Follow the BencherConfig class to fill up the attributes. Then, use the following command to run the Bencher with the selected application:
```
python3 src/bench.py
```