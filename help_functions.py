import glob
import os
import time

base_dir = os.path.join('.', 'data')


def get_last_modified_time(m_type, name):
    all_files = glob.glob(os.path.join('.', m_type, name, '*'))
    last_m_time = 0
    m_time = 0
    for file in all_files:
        m_time = os.path.getmtime(file)
        if last_m_time < m_time:
            last_m_time = m_time
    current_time = time.time()
    time_past = round(current_time - m_time)
    last_modified_string = get_last_updated_time_as_string(time_past)
    return last_modified_string


def get_last_updated_time_as_string(time_in):
    d = time_in // (60 * 60 * 24)
    h = (time_in - d * 60 * 60 * 24) // (60 * 60)
    m = (time_in - d * 60 * 60 * 24 - h * 60 * 60) // 60
    if d == 0:
        d_string = ''
    elif d == 1:
        d_string = f' {d} day'
    else:
        d_string = f' {d} days'
    if h == 0 and d == 0:
        h_string = ''
    elif h == 1:
        h_string = f' {h} hr'
    else:
        h_string = f' {h} hrs'
    if m == 1:
        m_string = f' {m} min ago'
    else:
        m_string = f' {m} mins ago'
    last_modified_string = 'Last updated' + d_string + h_string + m_string
    return last_modified_string
