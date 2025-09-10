import subprocess
import matplotlib.pyplot as plt
import time
import numpy as np

from tensor_core_test_plots import do_scaling_plots, do_ch_bl_plots, do_int_time_plots
import pickle

PROG = "./build/test/CorrelatorTest/CorrelatorTest"

# num channels failed on '65792',
nrPolarizations = 2

nrChannels_min = 256       # starting points
nrReceivers_min = 2
nrSamplesPerChannel_min = 256


nrChannels_max = 65535        # increments
nrReceivers_max = 358
nrSamplesPerChannel_max = 2**18

NUM_SCALING_STEPS = 20
NUM_REPEATS = 1


measures = [ "host-to-device", "device-to-host", "correlate-gpu", "correlate-sequential" ]

def increasing_test(nrChannels, nrReceivers, nrSamplesPerChannel, whats_changing):
    # The lists are all the same length but only one of them is changing
    assert len(nrChannels) == len(nrReceivers) and len(nrChannels) == len(nrSamplesPerChannel)
    assert whats_changing in ["nrChannels", "nrReceivers", "nrSamplesPerChannel", "all"] 
    print("Changing", whats_changing+",", "steps:", len(nrChannels))

    calc_baselines = lambda n: (n*(n+1))//2
    calc_FLOPS = lambda receivers, channels, samples: calc_baselines(receivers)*nrPolarizations*nrPolarizations*channels*samples
    empty = lambda: { "time": [], "TOPS": [], "rate": [] }   # outputs from test programs

 
    timings = {}
    for m in measures:
        timings[m] = empty()

    timings["nrChannels"] = nrChannels
    timings["nrReceivers"] = nrReceivers
    timings["nrSamplesPerChannel"] = nrSamplesPerChannel
    timings["nrBaselines"] = [ calc_baselines(n) for n in nrReceivers]
    timings["nrFLOPS"] = [ calc_FLOPS(nrReceivers[i], nrChannels[i], nrSamplesPerChannel[i]) for i in range(len(nrReceivers)) ]

    timings["whats_changing"] = whats_changing

    
    for i in range(len(nrChannels)):
        print("Step", i)
        timings_to_average = {}
        for m in measures:
            timings_to_average[m] = empty()
            
        
        # Do the repeats and keep them in a temporary dict
        for iter in range(NUM_REPEATS):

            try:
                # Correlator test
                command = PROG+" -V 0 -I fp16 -c "+str(nrChannels[i])+" -n "+str(nrReceivers[i])+" -N 32 -r 1 -R 1 -t "+str(int(nrSamplesPerChannel[i]))
                output = subprocess.check_output(command.split()).decode()
            except:
                print("GPU run failed. Stopping.")
                return timings

            # correlator serial in C
            command = "./correlator_sequential "+str(nrChannels[i])+" "+str(nrReceivers[i])+" "+str(nrSamplesPerChannel[i])
            output1 = subprocess.check_output(command.split()).decode()


            output += output1

            # Parse output
            for line in output.split("\n"):
                l = line.split()
                if len(l) >= 2 and l[0] in measures:
                    timings_to_average[l[0]]["time"].append(float(l[2]))

                    if l[0] in [ "correlate-total", "total" ]:
                        timings_to_average[l[0]]["TOPS"].append(float(l[4]))

                    if l[0] in [ "host-to-device", "device-to-host" ]:
                        timings_to_average[l[0]]["rate"].append(float(l[4]))
                        
        # Get average and transfer to output dict
        for meas in measures:
            for stat in timings_to_average[meas]:
                assert len(timings_to_average[meas][stat]) in [ 0, NUM_REPEATS ]
                if len(timings_to_average[meas][stat]) > 0:
                    average = sum(timings_to_average[meas][stat])/len(timings_to_average[meas][stat])
                    timings[meas][stat].append(average)

                
        time.sleep(2)
        
    return timings



    
def init_lists(whats_changing):
    assert whats_changing in ["nrChannels", "nrReceivers", "nrSamplesPerChannel"] 
    
    # Init
    nrC = [ nrChannels_min for i in range(NUM_SCALING_STEPS) ]
    nrR = [ nrReceivers_min for i in range(NUM_SCALING_STEPS) ]
    nrS = [ nrSamplesPerChannel_min for i in range(NUM_SCALING_STEPS) ]

    # Modify the one changing
    if whats_changing == "nrChannels": nrC = np.linspace(nrChannels_min, nrChannels_max, NUM_SCALING_STEPS, dtype=int)
    elif whats_changing == "nrReceivers": nrR = np.linspace(nrReceivers_min, nrReceivers_max, NUM_SCALING_STEPS, dtype=int)
    elif whats_changing == "nrSamplesPerChannel": nrS = np.linspace(nrSamplesPerChannel_min, nrSamplesPerChannel_max, NUM_SCALING_STEPS, dtype=int)

    nrS = [ nr//8*8 for nr in nrS ]                # nrSamplesPerChannel has to be a multiple of 8
                
    return nrC, nrR, nrS

    
def init_lists_ch_bl():
    
    # Find the array element that is closest to x
    where_nearest_match = lambda a, x: np.argmin(np.abs(a-x))
    
    # Get baselines
    nrR = np.linspace(2, 348, dtype=int)
    nrB = np.array([ (n*(n+1))//2 for n in nrR ])


    # Calculate channels so that nrB*nrC is a constant
    constant = nrB[0]*nrB[-1]
    nrC = [ int(np.round(constant/n)) for n in nrB ]
    
    # clip when channels get to 10
    clip_i = where_nearest_match(np.array(nrC), 10)
    
    nrR = nrR[:clip_i+1]
    nrB = nrB[:clip_i+1]
    nrC = nrC[:clip_i+1]
    
    #for i in range(len(nrR)):
    #    print(nrB[i], nrC[i], nrC[i]*nrB[i])

    nrS = [ 1024 for i in nrR ]                # nrSamplesPerChannel has to be a multiple of 8
                

    return nrC, nrR, nrS

def init_lists_int_time(num_telescopes, bandwidth, num_channels):

    integration_times = np.array([0.1, 0.5, 2, 3, 4, 5, 6, 7, 8])

    input_fft_length_in_samples = 2*num_channels
    sampling_rate = bandwidth*2

    nrS = np.zeros(integration_times.size, dtype=int)
    for i, it in enumerate(integration_times):
        nrS[i] = int(np.round(sampling_rate*it/input_fft_length_in_samples))
        nrS[i] = nrS[i]//8*8      # have to be multiple of 8

    nrC = np.full(integration_times.size, num_channels)
    nrR = np.full(integration_times.size, num_telescopes)

    return nrC, nrR, nrS, integration_times



def do_scaling_tests():
    print("Scaling tests")

    order = [ "nrChannels", "nrReceivers", "nrSamplesPerChannel" ]
    all_timings = []
    for what in order:
        nrCs, nrRs, nrSs = init_lists(what)
        all_timings.append(increasing_test(nrCs, nrRs, nrSs, what))


    with open("timings.pkl","wb") as f:
        pickle.dump(all_timings, f)

    do_scaling_plots()

def do_ch_bl_tests():
    print("Channel vs Baseline tests")
    nrCs, nrRs, nrSs, int_times = init_lists_ch_bl()

    timings = increasing_test(nrCs, nrRs, nrSs, "all")

    with open("ch_bl_timings.pkl","wb") as f:
        pickle.dump(timings, f)

    do_ch_bl_plots()

def do_int_time_tests():
    print("Integration time tests, emerlin")
    nrCs, nrRs, nrSs, int_times = init_lists_int_time(2, 64000000, 4096)      # emerlin

    timings = increasing_test(nrCs, nrRs, nrSs, "nrSamplesPerChannel")
    timings["integration_times"] = int_times

    with open("emerlin_int_time_timings.pkl","wb") as f:
        pickle.dump(timings, f)

    do_int_time_plots("emerlin")

    print("integration time tests, EVN")
    nrCs, nrRs, nrSs, int_times = init_lists_int_time(2, 32000000, 1024)      # EVN

    timings = increasing_test(nrCs, nrRs, nrSs, "nrSamplesPerChannel")
    timings["integration_times"] = int_times

    with open("evn_int_time_timings.pkl","wb") as f:
        pickle.dump(timings, f)

    do_int_time_plots("evn")

do_int_time_tests()


do_scaling_tests()
do_ch_bl_tests()


