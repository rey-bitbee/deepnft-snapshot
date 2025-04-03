import time

from alive_progress import alive_bar


def get_progress_bar(total: int):
    prefix = ("[{}]: ").format(time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))
    return alive_bar(
        total,
        title=prefix,
        enrich_print=False,
        receipt=False,
        spinner=False,
        stats="(eta: {eta})",
    )
