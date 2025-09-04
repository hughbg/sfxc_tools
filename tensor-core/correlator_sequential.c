// gcc -O correlator_sequential.c -DTEST -o correlator_sequential -lm

#include <time.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <strings.h>
#include <string.h>
#include <ctype.h>
#include <complex.h>

int get_int(const char *s) {
    // get int from string and check
    for (const char *s1=s; *s1!='\0'; ++s1) 
        if ( !isdigit(*s1) ) {
            fprintf(stderr, "Not an integer: %s\n", s);
            exit(1);
        }
        
    return atoi(s);
}

const int nrPolarizations = 2;
int nrChannels, nrReceivers, nrSamplesPerChannel, nrBaselines;

float complex *Samples;                         // [nrChannels][nrReceivers][nrPolarizations][nrSamplesPerChannel];    // this is my ordering
float complex *Visibilities;                     // [nrChannels][nrBaselines][nrPolarizations][nrPolarizations];


// Index a flat array as if it was 4-D
unsigned indexSamples(unsigned channel, unsigned receiver, unsigned pol, unsigned sample) {
    // ordering nrChannels nrReceivers nrPolarizations nrSamplesPerChannel


    return nrSamplesPerChannel*(nrPolarizations*(channel*nrReceivers + receiver) + pol)+sample;

}

unsigned indexVisibilities(unsigned channel, unsigned baseline, unsigned pol0, unsigned pol1) {
    // ordering nrChannels nrBaselines nrPolarizations nPolarizations


    return nrPolarizations*(nrPolarizations*(channel*nrBaselines + baseline) + pol0)+pol1;

}





/*
  These are the arrays defined in Tensor-Core TCCorrelator.cu. They will be slightly modified here.
  typedef Sample Samples[NR_CHANNELS][NR_SAMPLES_PER_CHANNEL / NR_TIMES_PER_BLOCK][NR_RECEIVERS][NR_POLARIZATIONS][NR_TIMES_PER_BLOCK];
  typedef Visibility Visibilities[NR_CHANNELS][NR_BASELINES][NR_POLARIZATIONS][NR_POLARIZATIONS];

*/

int main(int argc, const char **argv) {
    struct timespec start, stop;

    // We want. Is there any significance in this ordering
    //float complex Samples[NR_CHANNELS][NR_SAMPLES_PER_CHANNEL][NR_RECEIVERS][NR_POLARIZATIONS];
    //float complex Visibilities[NR_CHANNELS][NR_BASELINES][NR_POLARIZATIONS][NR_POLARIZATIONS];

    if ( argc != 4 ) {
        fprintf(stderr, "Usage: correlator_serial nrChannels nrReceivers nrSamplesPerChannel\n");
        exit(1);
    }

    nrChannels = get_int(argv[1]);
    nrReceivers = get_int(argv[2]);
    nrSamplesPerChannel = get_int(argv[3]);
    nrBaselines = (nrReceivers*(nrReceivers+1))/2;

    // gotta malloc memory because too big for the stack
    Samples = calloc(sizeof(float complex), nrChannels*nrReceivers*nrPolarizations*nrSamplesPerChannel);
    Visibilities = calloc(sizeof(float complex), nrChannels*nrBaselines*nrPolarizations*nrPolarizations);
    if ( Samples == NULL || Visibilities == NULL ) {
        fprintf(stderr, "Failed to calloc\n");
        exit(1);
    }

#ifdef TEST

    // check indexing by writing a sequence to a flat array and reading the sequence as a 4-D array
    // use int elements for comparing. use different shapes for Samples and Visibilities
    unsigned *a = calloc(sizeof(unsigned), nrChannels*nrReceivers*nrPolarizations*nrSamplesPerChannel);  // Samples shape
    for (unsigned i=0; i<nrChannels*nrReceivers*nrPolarizations*nrSamplesPerChannel; ++i)
        a[i] = i;


    unsigned num=0;
    for (unsigned i=0; i<nrChannels; ++i)
        for (unsigned j=0; j<nrReceivers; ++j)
            for (unsigned k=0; k<nrPolarizations; ++k)
                for (unsigned l=0; l<nrSamplesPerChannel; ++l) {
                    if ( num != a[indexSamples(i, j, k, l)]) {
                        fprintf(stderr, "Samples indexing not working, expect %u, got %u\n", num, a[indexSamples(i, j, k, l)]);
                        exit(1);
                    }
                    ++num;
                }

    free(a);


    a = calloc(sizeof(unsigned), nrChannels*nrBaselines*nrPolarizations*nrPolarizations);    // Visibilities shape
    for (unsigned i=0; i<nrChannels*nrBaselines*nrPolarizations*nrPolarizations; ++i)
        a[i] = i;

    num=0;
    for (unsigned i=0; i<nrChannels; ++i)
        for (unsigned j=0; j<nrBaselines; ++j)
            for (unsigned k=0; k<nrPolarizations; ++k)
                for (unsigned l=0; l<nrPolarizations; ++l) {
                    if ( num != a[indexVisibilities(i, j, k, l)]) {
                        fprintf(stderr, "Visibilities indexing not working, expect %u, got %u\n", num, a[indexSamples(i, j, k, l)]);
                        exit(1);
                    }
                    ++num;
                }

    free(a);

    // end indexing check
#endif


    // init arrays using as flat arrays
    for (int i=0; i<nrChannels*nrReceivers*nrPolarizations*nrSamplesPerChannel; ++i)
        Samples[i] = 1+2*I;
    bzero((void*)Visibilities, sizeof(nrChannels*nrBaselines*nrPolarizations*nrPolarizations));


    // correlate as 4-D arrays
    clock_gettime(CLOCK_MONOTONIC, &start);

    //unsigned num_flops = 0;
    //unsigned num_baselines = 0;
    for (unsigned channel=0; channel<nrChannels; ++channel) {
        unsigned baseline = 0;
        for (unsigned receiver0=0; receiver0<nrReceivers; ++receiver0) {
            for (unsigned receiver1=receiver0; receiver1<nrReceivers; ++receiver1) {
                //++num_baselines;
                for (unsigned pol0=0; pol0<nrPolarizations; ++pol0) {
                    for (unsigned pol1=0; pol1<nrPolarizations; ++pol1) {
                        for (unsigned sample=0; sample<nrSamplesPerChannel; ++sample) {
                            //++num_flops;
                            Visibilities[indexVisibilities(channel, baseline, pol0, pol1)] +=
                                    Samples[indexSamples(channel, receiver0, pol0, sample)]*conjf(Samples[indexSamples(channel, receiver1, pol1, sample)]);
                            /*printf("vis %d %d %d %d %f %.1f+%.1fi %.1f+%.1fi\n", channel, baseline, pol0, pol1, cabsf(Visibilities[indexVisibilities(channel, baseline, pol0, pol1)]),
                                        crealf(Samples[indexSamples(channel, receiver1, pol1, sample)]), cimagf(Samples[indexSamples(channel, receiver1, pol1, sample)]),
                                        crealf(Samples[indexSamples(channel, receiver1, pol1, sample)]), cimagf(Samples[indexSamples(channel, receiver1, pol1, sample)]));*/
                        }
                    }
                }
                ++baseline;
            }
        }
    }

    clock_gettime(CLOCK_MONOTONIC, &stop);
    printf("correlate-sequential : %f s\n", (stop.tv_sec+stop.tv_nsec/1e9)-(start.tv_sec+start.tv_nsec/1e9));
    //printf("num_flops %u num_baselines %u\n", num_flops, num_baselines/nrChannels);

#ifdef TEST
    // Check every slot has a value
    for (unsigned channel=0; channel<nrChannels; ++channel)
        for (unsigned baseline=0; baseline<nrBaselines; ++baseline)
           for (unsigned pol0=0; pol0<nrPolarizations; ++pol0)
                for (unsigned pol1=0; pol1<nrPolarizations; ++pol1)
                    if ( cabsf(Visibilities[indexVisibilities(channel, baseline, pol0, pol1)]) == 0 ) {
                        fprintf(stderr, "visibility %d %d %d %d %f is 0\n", channel, baseline, pol0, pol1, cabsf(Visibilities[indexVisibilities(channel, baseline, pol0, pol1)]));
                        exit(1);
                    }
#endif

}
    
