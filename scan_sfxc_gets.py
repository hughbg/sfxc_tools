import sys, numpy as np

frame_time = 0.000125

last_value = None

if len(sys.argv) != 2:
    print("Need 1 arg")
    exit(1)

frame_number = 0
for line in sys.stdin:
    tokens = line[:-1].split()
    assert len(tokens)%2 == 0, "Must be an even number of tokens in a line (field name followed by value, repeated)"

    if sys.argv[1] == "s_from_ref_epoch" or sys.argv[1] == "valid":
        value = int(tokens[1 if sys.argv[1] == "valid" else 5])
        if last_value is not None:
            if value != last_value:
                print("T =", "{:7.4f}".format(frame_number*frame_time), sys.argv[1], last_value, "->", value)

    elif sys.argv[1] == "frame_num":
        value = int(tokens[11])
        if last_value is not None:
            if value != last_value+1:
                print("T =", "{:7.4f}".format(frame_number*frame_time), sys.argv[1], last_value, "->", value)

    else:
        print("Invalid arg - can't handle")
        exit(1)


    last_value = value
    frame_number += 1



