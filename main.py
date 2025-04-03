import time

import click
from loguru import logger
import schedule

from dingding import DingdingRobot
from gcw import get_unlist_gcws
from settings import Settings


def job(settings: Settings):
    notify_params = get_unlist_gcws(
        rpc="https://mainnet.ethereumpow.org",
        spreadsheet_id="1QeEeXy9tDvEp1pfEpMqtjVBrjXPb5CXTZdZFbGUjss4",
        div=3,
        mod=2,
        unlist_sheet="unlist",
        result_sheet="id%3==2",
        # end_token_id=10,
    )
    robot = DingdingRobot(settings.dingding_access_token, settings.dingding_secret)
    robot.notify(**notify_params)
    return schedule.CancelJob


cli = click.Group()


@cli.command(name="gcw")
@click.option("--envfile", type=str, help="env file")
@click.option("--at", type=str, help="at time")
def gcw_command(envfile: str, at: str):
    settings = Settings(_env_file=envfile)

    schedule.every().day.at(at).do(job, settings)

    while True:
        n = schedule.idle_seconds()
        logger.info("idle_seconds: {}", n)
        if n is None:
            break
        elif n > 0:
            time.sleep(n)

        schedule.run_pending()


if __name__ == "__main__":
    cli()
