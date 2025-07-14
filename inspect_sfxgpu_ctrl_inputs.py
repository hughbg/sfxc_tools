import sys

if len(sys.argv) != 2:
    print("Usage: inspect_sfxgpu_ctrl_inputs.py control_parameters_code")
    exit(1)

lines = open(sys.argv[1]).readlines()

fields = []

for l in lines:
    while "ctrl[\"" in l:
        where = l.find("ctrl[")+6
        where_end = where
        while l[where_end] != '"': where_end += 1
        field = l[where:where_end]
        if field not in fields: fields.append(field)

        l = l[where_end:]


print("Fields expected in control file:\n\n", fields)

import json

with open("/home/v66437hg/merlin_git/sfxc/run/sfxctest.ctrl") as f:

    params = json.load(f)
print()
print("Expected fields present in control file:\n")
for p in params:
    if p in fields:
        print(p+":", params[p])

print()
print("Expected fields missing from control file:\n")
for f in fields:
    if f not in params:
        print(f)

print()
print("Unexpected fields in control file:\n")
for p in params:
    if p not in fields:
        print(p+":", params[p])

