import numpy as np
from matplotlib import pyplot as plt


def select_events_timestamps(sp_py, trials_idx, events):
    events_timestamps = []
    for i_t in trials_idx:
        e_timestamps = []
        for _, event in events.items():
            idx_event = np.where(sp_py["code_numbers"][i_t] == event)[0]
            if len(idx_event) == 0:
                sample_event = [np.nan]
            else:
                sample_event = sp_py["code_samples"][i_t][idx_event]
            e_timestamps.append(sample_event)
        events_timestamps.append(np.concatenate(e_timestamps))

    return np.array(events_timestamps, dtype="object")


def align_neuron_spikes(trials_idx, sp_py, neuron, event_timestamps):
    # create list of neurons containing the spikes timestamps aligned with the event
    neuron_trials = []
    for i, i_t in enumerate(trials_idx):
        neuron_trials.append(sp_py["sp_samples"][i_t][neuron] - event_timestamps[i])
    return np.array(neuron_trials, dtype="object")


def trial_average_fr(neuron_trials):
    # Compute the Average firing rate
    sorted_sp_neuron = np.sort(np.concatenate(neuron_trials))
    sum_sp = np.zeros(int(sorted_sp_neuron[-1] - sorted_sp_neuron[0] + 1))
    sorted_sp_shift = np.array(sorted_sp_neuron - sorted_sp_neuron[0], dtype=int)
    for i in sorted_sp_shift:
        sum_sp[i] += 1
    trial_average_sp = sum_sp / len(neuron_trials)
    return trial_average_sp, sorted_sp_neuron


def compute_fr(neuron_trials, kernel, fs, downsample):
    trials_conv = []
    for i_trial in range(len(neuron_trials)):
        if len(neuron_trials[i_trial]) != 0:
            arr_timestamps = np.zeros(
                neuron_trials[i_trial][-1] + 1
            )  # array with n timestamps
            for sp in neuron_trials[i_trial]:
                arr_timestamps[sp] += 1
            # Downsample to 1ms
            arr_timestamps = np.sum(
                np.concatenate(
                    (
                        arr_timestamps,
                        np.zeros(downsample - len(arr_timestamps) % downsample),
                    )
                ).reshape(-1, downsample),
                axis=1,
            )

            conv = np.convolve(arr_timestamps, kernel, mode="same") * fs
        else:
            conv = [0]
        trials_conv.append(conv)
    return trials_conv


def fr_in_window(x, start, end):
    fr = np.zeros(len(x))
    for i, i_x in enumerate(x):
        fr[i] = np.nan_to_num(np.mean(i_x[start[i] : end[i]]), nan=0)
    return fr


def compute_mean_fr(conv, event_timestamps, align_event):
    max_shift = np.max(event_timestamps[:, align_event])
    max_duration = np.max(event_timestamps[:, -1])
    conv_shift = []
    events_shift = []
    for i, i_conv in enumerate(conv):
        diff_before = max_shift - event_timestamps[i, align_event]
        diff_after = max_duration - (diff_before + len(i_conv))
        if diff_after < 0:  # (sp between trials)
            conv_shift.append(
                np.concatenate((np.zeros(diff_before), i_conv[:diff_after]))
            )
        else:
            conv_shift.append(
                np.concatenate((np.zeros(diff_before), i_conv, np.zeros(diff_after)))
            )
        events_shift.append(event_timestamps[i] + diff_before)
    return np.mean(conv_shift, axis=0), max_shift, events_shift


def plot_raster_fr(
    all_trials_fr,
    max_shift,
    fs,
    neuron_trials,
    code,
    ax,
    fig,
    i,
    x_lim_max,
    x_lim_min,
    events,
):
    ax2 = ax.twinx()
    # fr
    ax.plot((np.arange(len(all_trials_fr)) - max_shift) / fs, all_trials_fr)
    # raster
    conv_max = int(np.floor(max(all_trials_fr)) + 2)
    num_trials = len(neuron_trials)
    lineoffsets = np.arange(conv_max, num_trials + conv_max)
    ax2.eventplot(neuron_trials / fs, color=".2", lineoffsets=1, linewidths=0.8)
    # events
    ax.vlines(
        events[1] / fs, 0, lineoffsets[-1], color="b", linestyles="dashed"
    )  # target_on
    ax.vlines(
        events[2] / fs, 0, lineoffsets[-1], color="k", linestyles="dashed"
    )  # target_off
    ax.vlines(
        events[3] / fs, 0, lineoffsets[-1], color="k", linestyles="dashed"
    )  # fix_spot_off
    ax.vlines(
        events[4] / fs, 0, lineoffsets[-1], color="k", linestyles="dashed"
    )  # response
    # figure setings
    ax.set(xlabel="Time (s)", ylabel="Average firing rate")
    ax2.set(xlabel="Time (s)", ylabel="trials")
    ax2.set_yticks(range(-conv_max, num_trials))
    ax.set_title("Code %s" % (code), fontsize=8)
    ax.set_xlim(x_lim_min, x_lim_max)
    plt.setp(ax2.get_yticklabels(), visible=False)
    fig.tight_layout(pad=0.2, h_pad=0.2, w_pad=0.2)
    fig.suptitle("Neuron %d" % (i + 1), x=0)
    return fig
