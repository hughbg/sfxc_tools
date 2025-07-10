import sys

if len(sys.argv) != 2:
    print("Usage: inspect_sfxgpu_ctrl_inputs.py control_parameters_code")
    exit(1)

lines = open(sys.argv[1]).readlines()

print(len(lines))
