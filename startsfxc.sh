#!/bin/bash
export PATH="/home/v66437hg/merlin_git/sfxc/sfxc/install/bin:$PATH"
if [ "`hostname`" = "e-10lux3178xfn" ]
then 
  export LD_LIBRARY_PATH=/home/v66437hg/intel/oneapi/ipp/2021.10/lib:$LD_LIBRRAY_PATH
else
  export LD_LIBRARY_PATH=/opt/intel/oneapi/ipp/2022.1/lib:$LD_LIBRRAY_PATH
fi
export CALC_DIR=/home/v66437hg/merlin_git/sfxc/sfxc/lib/calc10/data
mpirun -rankfile default.rank /home/v66437hg/merlin_git/sfxc/sfxc/install/bin/sfxc sfxctest.ctrl sfxctest.vex
#mpirun -np 6 /home/v66437hg/merlin_git/sfxc/sfxc/install/bin/sfxc sfxctest.ctrl sfxctest.vex
