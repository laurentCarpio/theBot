import re
import trade_bot.utils.enums as const


def getFreq_in_ms(frequency: str) -> int:
    # Regular expression to match any of the characters 'm', 'H', 'D', 'W', 'M'
    freq = int(re.split(r"[mHDWM]", frequency, maxsplit=1)[0])
    if frequency.find('m') != -1:
        return freq * 60 * 1000
    if frequency.find('H') != -1:
        return freq * 60 * 60 * 1000
    if frequency.find('D') != -1:
        return freq * 24 * 60 * 60 * 1000
    if frequency.find('W') != -1:
        return freq * 7 * 24 * 60 * 60 * 1000
    if frequency.find('M') != -1:
        return freq * 31 * 24 * 60 * 60 * 1000
    return 0

def freq_to_resample(frequency: str) -> str:
    # Replace characters
    return frequency.replace("m", "min").lower()

def resample_to_freq(frequency: str) -> str:
    # Replace characters
    if frequency.find('min') != -1:
        return frequency.replace("min", "m").lower()
    else:
        return frequency

def get_above_frequency(frequency: str) -> str:
    my_list = const.MY_FREQUENCY_LIST
    try:
        last_index = my_list.index(const.FREQUENCY_4H)
        index = my_list.index(frequency)
        # Get the next item
        if index < last_index: 
            return my_list[index + 1]
        else: # to the last frequency available for validation
            return const.FREQUENCY_12H
    except ValueError:
        # # should never happens 
        return frequency

def get_frequency_for_next_step(frequency: str) -> str:
    return const.FREQUENCY_MAPPING[frequency]