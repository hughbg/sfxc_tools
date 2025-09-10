import numpy as np
import os

PROG = "./build/test/CorrelatorTest/CorrelatorTest"

NETWORK = "evn"

if NETWORK == "emerlin":
    NUM_TELESCOPES = 7
    BANDWIDTH = 64000000            # A higher sample rate means more FFTs need to be done for the integration time
    NUM_CHANNELS = 4096
    INTEGRATION_TIME = 0.5  # s

elif NETWORK == "evn":
    NUM_TELESCOPES = 16
    BANDWIDTH = 64000000
    NUM_CHANNELS = 1024
    INTEGRATION_TIME = 0.1  # s



assert int(NUM_TELESCOPES) == NUM_TELESCOPES, "Num telescopes is not integer"
assert int(NUM_CHANNELS) == NUM_CHANNELS, "Num channels is not integer"


print("NUM_TELESCOPES", NUM_TELESCOPES, "BANDWIDTH", BANDWIDTH, "NUM_CHANNELS", NUM_CHANNELS, "INTEGRATION_TIME", INTEGRATION_TIME)

sampling_rate = BANDWIDTH*2
spectral_resolution = BANDWIDTH/NUM_CHANNELS
fft_length_in_seconds = 1/spectral_resolution   # NUM_CHANNELS/BANDWIDTH
input_fft_length_in_samples = 2*NUM_CHANNELS    # sampling_rate*fft_length_in_seconds. Assuming real fft then output len is NUM_CHANNELS.

print("Spectral resolution:", spectral_resolution, "(Hz) FFT length (nanosec):", fft_length_in_seconds*1e9, "Input FFT length (samples):", input_fft_length_in_samples)

"""
# Use numpy to verify these values fit together. Assuming fft not rfft here.
fftfreq = np.fft.fftfreq(input_fft_length_in_samples, 1/sampling_rate)
assert spectral_resolution == fftfreq[1]-fftfreq[0]
assert fftfreq.size//2 == NUM_CHANNELS
"""

# Check integers and multiples so things fit.

samples_in_integration = sampling_rate*INTEGRATION_TIME
if int(samples_in_integration) != samples_in_integration:
    print("samples_in_integration", samples_in_integration, "is not integer, rounding to", end=" ")
    samples_in_integration = int(samples_in_integration)
    print(samples_in_integration)
else:
    samples_in_integration = int(samples_in_integration)

if samples_in_integration%input_fft_length_in_samples != 0:
    print("samples_in_integration", samples_in_integration, "is not a multiple of FFT length, rounding to", end=" ")
    samples_in_integration = samples_in_integration//input_fft_length_in_samples*input_fft_length_in_samples
    print(samples_in_integration)

# Do a pretend integration step with FFTs.

data = np.zeros((NUM_TELESCOPES, samples_in_integration), dtype=bool)

# split into FFT lengths
data = data.reshape(NUM_TELESCOPES, samples_in_integration//input_fft_length_in_samples, input_fft_length_in_samples)

# Now "do" the FFT. The output FFT will be half the size of the input FFT for real input, so cut that dimension.
data = data[:, :, :data.shape[2]//2]


print("With an integration time of "+str(INTEGRATION_TIME)+"s,", samples_in_integration//input_fft_length_in_samples, "FFTs are made, giving data block",
      NUM_TELESCOPES, "x", NUM_CHANNELS, "x", samples_in_integration//input_fft_length_in_samples)


# Prepare for Tensor-Core
nrReceivers = NUM_TELESCOPES
nrBaselines = (nrReceivers*(nrReceivers+1))//2
nrChannels = NUM_CHANNELS
nrSamplesPerChannel = samples_in_integration//input_fft_length_in_samples



# Another restriction from Tensor-Core
if nrSamplesPerChannel%8 != 0:
    print("For Tensor-Core,", nrSamplesPerChannel, "is not a multiple of 8, rounding to", end=" ")
    nrSamplesPerChannel = int(nrSamplesPerChannel)//8*8
    print(nrSamplesPerChannel)
    print("Integration time is now", fft_length_in_seconds*nrSamplesPerChannel)


print("Problem size", nrBaselines*nrChannels*nrSamplesPerChannel*2*2)


# Correlator test options
# [-I i4|i8|e4m3|e5m2|fp16] [-c nrChannels] [-n nrReceivers] [-N nrReceiversPerBlock] [-r innerRepeatCount] [-R outerRepeatCount] [-t nrSamplesPerChannel] [-V verifyOutput]

command = PROG+" -V 0 -I fp16 -c "+str(nrChannels)+" -n "+str(nrReceivers)+" -N 32 -r 1 -R 1 -t "+str(int(nrSamplesPerChannel))
print(command)
os.system(command)




