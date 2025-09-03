import pickle, numpy as np
import matplotlib.pyplot as plt

measures_to_plot = [ "host-to-device,time", "device-to-host,time", "host-to-device,rate", "device-to-host,rate", "correlate-real,time", "correlate-sequential,time" ]


def do_scaling_plots():
    with open("timings.pkl","rb") as _file:
        all_timings = pickle.load(_file)
    assert len(all_timings) == 3, "# parameters not recorded properly"

    # What we have in a timing: there are 5 input parameters, nrReceivers etc. and a list for each one with values.
    # Which parameters are changing in those lists is in whats_changing. Then there the output statistics,
    # host-to-device etc. Each statistic has 3 lists, which may or may not be filled and used: time, rate, TOPS,
    # which come from the test programs.




    plt.figure(figsize=(16, 4))

    for meas in measures_to_plot:
        m = meas.split(",")
        
        plt.clf()

        plot_index = 1
        for i, timing in enumerate(all_timings):   # channels, receivers, samples
            plt.subplot(1, len(all_timings)+1, plot_index)
            plt.plot(timing[timing["whats_changing"]], timing[m[0]][m[1]])   # e.g. [host-to-device][rate]
            plt.ylim(ymin=0)
            plt.xlim(xmin=0)
            plt.title("Changing "+timing["whats_changing"])
            if plot_index == 1:
                if m[1] == "time": plt.ylabel("Time [s]")
                elif m[1] == "rate": plt.ylabel("Rate [GB/s]")
                elif m[1] == "TOPS": plt.ylabel("TOPS")
            plt.xlabel(timing["whats_changing"])

            plot_index += 1

            # If the receivers changing then add baseline plot

            if timing["whats_changing"] == "nrReceivers":
                plt.subplot(1, len(all_timings)+1, plot_index)
                plt.plot(timing["nrBaselines"], timing[m[0]][m[1]])   # e.g. [host-to-device][rate]
                plt.ylim(ymin=0)
                plt.xlim(xmin=0)
                plt.title("Changing nrBaselines")
                if plot_index == 1:
                    if m[1] == "time": plt.ylabel("Time [s]")
                    elif m[1] == "rate": plt.ylabel("Rate [GB/s]")
                    elif m[1] == "TOPS": plt.ylabel("TOPS")
                plt.xlabel("nrBaselines")

                plot_index += 1



        plt.suptitle(m[0]+" "+m[1])
        plt.tight_layout()
        plt.savefig(meas)

    """
    # Now do the FLOPS plot
    plt.clf()
    plt.figure(figsize=(8, 8))

    for i, timing in enumerate(all_timings):   # channels, receivers, samples
        plt.plot(timing["nrFLOPS"], timing["correlate-real"]["time"], label=timing["whats_changing"])

    plt.legend()
    plt.ylabel("Time [s]")
    plt.xlabel("nrFLOPS")

    plt.ylim(ymin=0)
    plt.xlim(xmin=0, xmax=0.2e10)

    plt.savefig("flops1")

    plt.clf()
    for i, timing in enumerate(all_timings):   # channels, receivers, samples
        if timing["whats_changing"] == "nrReceivers":
            plt.plot(timing["nrFLOPS"], timing["nrBaselines"], label=timing["whats_changing"])
        else:
            plt.plot(timing["nrFLOPS"], timing[timing["whats_changing"]], label=timing["whats_changing"])

    plt.legend()
    plt.yscale("log")
    plt.ylabel("Number")
    plt.xlabel("nrFLOPS")

    plt.ylim(ymin=0)
    plt.xlim(xmin=0, xmax=0.2e10)

    plt.savefig("flops2")
    """

def do_ch_bl_plots():
    
    
    with open("ch_bl_timings.pkl","rb") as _file:
        timing = pickle.load(_file)

    plt.clf()
    # Sanity check plot. Combined should be flat.
    mult = [ timing["nrBaselines"][i]*timing["nrChannels"][i] for i in range(len(timing["nrChannels"])) ]
    plt.plot(mult, label="Combined")
    plt.plot(timing["nrBaselines"], label="Baselines")
    plt.plot(timing["nrChannels"], label="Channels")
    plt.legend()
    plt.ylim(ymin=0)
    plt.savefig("check")

    plt.figure(figsize=(12, 8))

    for meas in measures_to_plot:
        m = meas.split(",")

        plt.clf()

        plt.subplot(2, 1, 1)

        plt.plot(timing["nrBaselines"], timing[m[0]][m[1]])
        plt.scatter(timing["nrBaselines"], timing[m[0]][m[1]], marker=".")
        plt.ylim(ymin=0)

        plt.xlabel("(nrBaselines/nrChannels)")
        if m[1] == "time": plt.ylabel("Time [s]")
        elif m[1] == "rate": plt.ylabel("Rate [GB/s]")
        elif m[1] == "TOPS": plt.ylabel("TOPS")
        bl_ticks = plt.xticks()[0][:-1]
        bl_ticks = [ n for n in bl_ticks if n >= 0  and n < 65000]
        chan_ticks = np.interp(bl_ticks, timing["nrBaselines"], timing["nrChannels"])
        plt.xticks(bl_ticks, [ "("+str(int(np.round(bl_ticks[i])))+"/"+str(int(np.round(chan_ticks[i],1)))+")" for i in range(len(bl_ticks))])
        plt.xlabel("(nrBaselines/nrChannel)")


        plt.subplot(2, 1, 2)

        cut = 26
        plt.plot(timing["nrChannels"][::-1][:cut], timing[m[0]][m[1]][::-1][:cut])
        plt.scatter(timing["nrChannels"][::-1][:cut], timing[m[0]][m[1]][::-1][:cut], marker=".")
        plt.ylim(ymin=0)

        plt.xlabel("(nrChannels/nrBaselines)")
        if m[1] == "time": plt.ylabel("Time [s]")
        elif m[1] == "rate": plt.ylabel("Rate [GB/s]")
        elif m[1] == "TOPS": plt.ylabel("TOPS")

        chan_ticks = plt.xticks()[0][:-1]
        chan_ticks = [ n for n in chan_ticks if n >= 0 ]
        bl_ticks = np.interp(chan_ticks, timing["nrChannels"][::-1], timing["nrBaselines"][::-1])
        plt.xticks(chan_ticks, [ "("+str(int(np.round(chan_ticks[i])))+"/"+str(int(np.round(bl_ticks[i],1)))+")" for i in range(len(chan_ticks))])


        plt.suptitle(m[0]+" "+m[1])

        plt.tight_layout()
        #plt.xlim(xmin=-1000, xmax=65000)
        plt.savefig("ch_bl_"+meas)



if __name__ == "__main__":
    do_scaling_plots()
    do_ch_bl_plots()
        

